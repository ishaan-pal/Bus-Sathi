import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/api/api_client.dart';
import '../../core/models/bus_model.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_view.dart';
import '../../core/widgets/hr_app_bar.dart';
import '../../core/widgets/info_chip.dart';
import '../../core/widgets/loading_overlay.dart';
import 'bus_repository.dart';

class SearchResultsScreen extends StatefulWidget {
  const SearchResultsScreen({
    super.key,
    required this.fromStop,
    required this.toStop,
  });

  final String fromStop;
  final String toStop;

  @override
  State<SearchResultsScreen> createState() => _SearchResultsScreenState();
}

class _SearchResultsScreenState extends State<SearchResultsScreen> {
  late final BusRepository _repo;
  List<BusSearchResult> _buses = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _repo = BusRepository(ApiClient());
    _search();
  }

  Future<void> _search() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final results = await _repo.searchBuses(
        boardingStop: widget.fromStop,
        destinationStop: widget.toStop,
      );
      setState(() {
        _buses = results;
        _loading = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _error = e.message;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: HrAppBar(
        title: 'Search Results',
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: Stack(
        children: [
          Column(
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                color: AppColors.deepBlue.withValues(alpha: 0.05),
                child: Row(
                  children: [
                    const Icon(Icons.trip_origin, color: AppColors.green, size: 16),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        widget.fromStop,
                        style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
                      ),
                    ),
                    const Icon(Icons.arrow_forward, size: 16),
                    const SizedBox(width: 4),
                    const Icon(Icons.place, color: AppColors.saffron, size: 16),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        widget.toStop,
                        style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: _error != null
                    ? ErrorView(message: _error!, onRetry: _search)
                    : _buses.isEmpty && !_loading
                        ? const EmptyState(
                            icon: Icons.directions_bus_outlined,
                            title: 'No buses found',
                            subtitle: 'Try different stops or check again later',
                          )
                        : ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: _buses.length,
                            itemBuilder: (context, index) =>
                                _BusCard(bus: _buses[index]),
                          ),
              ),
            ],
          ),
          if (_loading) const LoadingOverlay(message: 'Searching buses...'),
        ],
      ),
    );
  }
}

class _BusCard extends StatelessWidget {
  const _BusCard({required this.bus});

  final BusSearchResult bus;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => context.push('/bus/${bus.busId}', extra: {
          'from': bus.boardingStop,
          'to': bus.destinationStop,
          'routeNumber': bus.routeNumber,
          'routeName': bus.routeName,
        }),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text(
                    bus.busNumber,
                    style: GoogleFonts.poppins(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Spacer(),
                  InfoChip(
                    icon: Icons.schedule,
                    label: bus.etaDisplay,
                    color: AppColors.green,
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                'Route ${bus.routeNumber} • ${bus.routeName}',
                style: GoogleFonts.poppins(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  InfoChip(icon: Icons.category, label: bus.busType),
                  if (bus.fareInfo.adultFareRupees != null)
                    InfoChip(
                      icon: Icons.currency_rupee,
                      label: '₹${bus.fareInfo.adultFareRupees!.toStringAsFixed(0)}',
                      color: AppColors.saffron,
                    ),
                  if (bus.delayMinutes > 0)
                    InfoChip(
                      icon: Icons.warning_amber,
                      label: '${bus.delayMinutes}m delay',
                      color: AppColors.error,
                    ),
                ],
              ),
              if (bus.currentStop != null) ...[
                const SizedBox(height: 8),
                Text(
                  'At: ${bus.currentStop}',
                  style: GoogleFonts.poppins(fontSize: 12),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
