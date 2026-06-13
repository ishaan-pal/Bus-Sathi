import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:latlong2/latlong.dart';

import '../../core/api/api_client.dart';
import '../../core/api/app_api.dart';
import '../../core/config.dart';
import '../../core/models/bus_model.dart';
import '../../core/theme/app_colors.dart';
import '../../core/utils/safe_state.dart';
import '../../core/widgets/error_view.dart';
import '../../core/widgets/hr_app_bar.dart';
import '../../core/widgets/info_chip.dart';
import '../../core/widgets/loading_overlay.dart';
import 'bus_repository.dart';

class BusDetailScreen extends StatefulWidget {
  const BusDetailScreen({
    super.key,
    required this.busId,
    required this.fromStop,
    required this.toStop,
    this.routeNumber,
    this.routeName,
    this.fallbackResult,
  });

  final String busId;
  final String fromStop;
  final String toStop;
  final String? routeNumber;
  final String? routeName;
  final BusSearchResult? fallbackResult;

  @override
  State<BusDetailScreen> createState() => _BusDetailScreenState();
}

class _BusDetailScreenState extends State<BusDetailScreen>
    with AsyncRequestGuard, SafeSetState {
  late final BusRepository _repo;
  BusDetailModel? _bus;
  BusLocationModel? _location;
  bool _loading = true;
  String? _error;
  bool _isDemo = false;
  Timer? _locationTimer;

  @override
  void initState() {
    super.initState();
    _repo = BusRepository(AppApi.client);
    _isDemo =
        widget.busId.startsWith('demo-') || widget.fallbackResult != null;
    _load();
    if (!_isDemo) {
      _locationTimer = Timer.periodic(AppConfig.locationPollInterval, (_) {
        _refreshLocation();
      });
    }
  }

  @override
  void dispose() {
    _locationTimer?.cancel();
    super.dispose();
  }

  Future<void> _load() async {
    final generation = beginRequest();

    if (_isDemo && widget.fallbackResult != null) {
      if (!isCurrentRequest(generation)) return;
      safeSetState(() {
        _bus = BusDetailModel.fromSearchResult(widget.fallbackResult!);
        _location = widget.fallbackResult!.location;
        _loading = false;
        _error = null;
      });
      return;
    }

    safeSetState(() {
      _loading = true;
      _error = null;
    });

    try {
      final bus = await _repo.getBusDetail(widget.busId);
      if (!isCurrentRequest(generation)) return;
      safeSetState(() {
        _bus = bus;
        _location = bus.location;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (!isCurrentRequest(generation)) return;
      safeSetState(() {
        _error = e.message;
        _loading = false;
      });
    } catch (_) {
      if (!isCurrentRequest(generation)) return;
      safeSetState(() {
        _error = 'Something went wrong loading bus details.';
        _loading = false;
      });
    }
  }

  Future<void> _refreshLocation() async {
    if (_isDemo || !mounted) return;
    try {
      final loc = await _repo.getBusLocation(widget.busId);
      if (!mounted) return;
      safeSetState(() => _location = loc);
    } catch (_) {}
  }

  void _bookTicket() {
    context.push('/fare-preview', extra: {
      'busId': widget.busId,
      'from': widget.fromStop,
      'to': widget.toStop,
      'routeNumber': widget.routeNumber ?? _bus?.routeNumber,
      'busNumber': _bus?.busNumber,
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: HrAppBar(
        title: _bus?.busNumber ?? 'Bus Detail',
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: Stack(
        children: [
          if (_error != null)
            ErrorView(message: _error!, onRetry: _load)
          else if (_bus != null)
            Column(
              children: [
                if (_isDemo)
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 8,
                    ),
                    color: AppColors.saffron.withValues(alpha: 0.15),
                    child: Text(
                      'Demo bus — connect to backend for live tracking',
                      style: GoogleFonts.poppins(fontSize: 12),
                      textAlign: TextAlign.center,
                    ),
                  ),
                SizedBox(
                  height: 220,
                  child: _buildMap(),
                ),
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      Text(
                        'Route ${_bus!.routeNumber ?? ''} • ${_bus!.routeName ?? ''}',
                        style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          InfoChip(icon: Icons.category, label: _bus!.busType),
                          InfoChip(
                            icon: Icons.schedule,
                            label: _bus!.etaDisplay,
                            color: AppColors.green,
                          ),
                          InfoChip(icon: Icons.info, label: _bus!.status),
                        ],
                      ),
                      const SizedBox(height: 16),
                      _infoRow('From', widget.fromStop),
                      _infoRow('To', widget.toStop),
                      if (_bus!.currentStop != null)
                        _infoRow('Current Stop', _bus!.currentStop!),
                      if (_bus!.conductorName != null)
                        _infoRow('Conductor', _bus!.conductorName!),
                      if (_location != null) ...[
                        const SizedBox(height: 8),
                        _infoRow(
                          'Speed',
                          '${_location!.speedKmh?.toStringAsFixed(0) ?? '—'} km/h',
                        ),
                        if (_location!.isStale)
                          const Padding(
                            padding: EdgeInsets.only(top: 8),
                            child: Text(
                              '⚠ Location may be stale',
                              style: TextStyle(color: AppColors.error),
                            ),
                          ),
                      ],
                      const SizedBox(height: 24),
                      ElevatedButton.icon(
                        onPressed: _isDemo ? null : _bookTicket,
                        icon: const Icon(Icons.confirmation_number),
                        label: Text(_isDemo ? 'Booking needs server' : 'Book Ticket'),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          if (_loading) const LoadingOverlay(),
        ],
      ),
    );
  }

  Widget _buildMap() {
    final loc = _location;
    if (loc == null) {
      return Container(
        color: Colors.grey.shade200,
        child: Center(
          child: Text(
            _isDemo ? 'Map unavailable in demo mode' : 'Location unavailable',
            style: GoogleFonts.poppins(color: AppColors.textSecondary),
          ),
        ),
      );
    }
    final point = LatLng(loc.latitude, loc.longitude);
    return FlutterMap(
      options: MapOptions(
        initialCenter: point,
        initialZoom: 14,
        interactionOptions: const InteractionOptions(
          flags: InteractiveFlag.all & ~InteractiveFlag.rotate,
        ),
      ),
      children: [
        TileLayer(
          urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          userAgentPackageName: 'in.haryana.haryana_roadways',
        ),
        MarkerLayer(
          markers: [
            Marker(
              point: point,
              width: 48,
              height: 48,
              child: const Icon(
                Icons.directions_bus,
                color: AppColors.saffron,
                size: 40,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: GoogleFonts.poppins(color: AppColors.textSecondary),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}
