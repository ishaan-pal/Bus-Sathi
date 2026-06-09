import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/api/api_client.dart';
import '../../core/models/route_model.dart';
import '../../core/models/ticket_model.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/hr_app_bar.dart';
import '../../core/widgets/loading_overlay.dart';
import '../buses/bus_repository.dart';
import 'ticket_repository.dart';

class FarePreviewScreen extends StatefulWidget {
  const FarePreviewScreen({
    super.key,
    required this.busId,
    required this.fromStop,
    required this.toStop,
    this.routeNumber,
    this.busNumber,
  });

  final String busId;
  final String fromStop;
  final String toStop;
  final String? routeNumber;
  final String? busNumber;

  @override
  State<FarePreviewScreen> createState() => _FarePreviewScreenState();
}

class _FarePreviewScreenState extends State<FarePreviewScreen> {
  late final TicketRepository _ticketRepo;
  late final BusRepository _busRepo;

  FareBreakdownModel? _fare;
  String? _routeId;
  int _adults = 1;
  int _children = 0;
  int _seniors = 0;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _ticketRepo = TicketRepository(ApiClient());
    _busRepo = BusRepository(ApiClient());
    _loadFare();
  }

  Future<void> _loadFare() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final routes = await _busRepo.getAllRoutes();
      RouteModel? route;
      if (widget.routeNumber != null) {
        for (final r in routes) {
          if (r.routeNumber == widget.routeNumber) {
            route = r;
            break;
          }
        }
      }
      route ??= routes.isNotEmpty ? routes.first : null;
      if (route == null) {
        throw ApiException('Route not found');
      }
      _routeId = route.id;
      final fare = await _ticketRepo.calculateFare(
        routeId: _routeId!,
        boardingStop: widget.fromStop,
        destinationStop: widget.toStop,
        adultCount: _adults,
        childCount: _children,
        seniorCount: _seniors,
      );
      setState(() {
        _fare = fare;
        _loading = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _error = e.message;
        _loading = false;
      });
    }
  }

  void _book() {
    context.push('/booking', extra: {
      'busId': widget.busId,
      'from': widget.fromStop,
      'to': widget.toStop,
      'adults': _adults,
      'children': _children,
      'seniors': _seniors,
      'busNumber': widget.busNumber,
      'fare': _fare?.totalFareRupees,
    });
  }

  Widget _counter(String label, int value, VoidCallback onDec, VoidCallback onInc) {
    return Row(
      children: [
        Expanded(child: Text(label, style: GoogleFonts.poppins())),
        IconButton(onPressed: onDec, icon: const Icon(Icons.remove_circle_outline)),
        Text('$value', style: GoogleFonts.poppins(fontWeight: FontWeight.bold)),
        IconButton(onPressed: onInc, icon: const Icon(Icons.add_circle_outline)),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: HrAppBar(
        title: 'Fare Preview',
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: Stack(
        children: [
          if (_error != null)
            Center(child: Text(_error!))
          else
            ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (widget.busNumber != null)
                          Text(
                            'Bus ${widget.busNumber}',
                            style: GoogleFonts.poppins(
                              fontWeight: FontWeight.bold,
                              fontSize: 18,
                            ),
                          ),
                        const SizedBox(height: 8),
                        Text('${widget.fromStop} → ${widget.toStop}'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      children: [
                        _counter('Adults', _adults, () {
                          if (_adults > 0) setState(() => _adults--);
                          _loadFare();
                        }, () {
                          if (_adults < 10) setState(() => _adults++);
                          _loadFare();
                        }),
                        _counter('Children', _children, () {
                          if (_children > 0) setState(() => _children--);
                          _loadFare();
                        }, () {
                          if (_children < 10) setState(() => _children++);
                          _loadFare();
                        }),
                        _counter('Senior Citizens', _seniors, () {
                          if (_seniors > 0) setState(() => _seniors--);
                          _loadFare();
                        }, () {
                          if (_seniors < 10) setState(() => _seniors++);
                          _loadFare();
                        }),
                      ],
                    ),
                  ),
                ),
                if (_fare != null) ...[
                  const SizedBox(height: 16),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Fare Breakdown',
                            style: GoogleFonts.poppins(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 8),
                          Text('Distance: ${_fare!.distanceKm.toStringAsFixed(1)} km'),
                          const Divider(),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'Total Fare',
                                style: GoogleFonts.poppins(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                '₹${_fare!.totalFareRupees.toStringAsFixed(2)}',
                                style: GoogleFonts.poppins(
                                  fontSize: 22,
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.saffron,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: (_adults + _children + _seniors) > 0 ? _book : null,
                    child: const Text('Proceed to Book'),
                  ),
                ],
              ],
            ),
          if (_loading) const LoadingOverlay(message: 'Calculating fare...'),
        ],
      ),
    );
  }
}
