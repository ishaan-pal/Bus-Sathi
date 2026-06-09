import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/api/api_client.dart';
import '../../core/models/route_model.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/error_view.dart';
import '../../core/widgets/hr_app_bar.dart';
import '../../core/widgets/loading_overlay.dart';
import '../buses/bus_repository.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late final BusRepository _busRepo;
  List<RouteModel> _routes = [];
  bool _loading = true;
  String? _error;

  String? _fromStop;
  String? _toStop;
  List<String> _allStops = [];

  @override
  void initState() {
    super.initState();
    _busRepo = BusRepository(ApiClient());
    _loadRoutes();
  }

  Future<void> _loadRoutes() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final routes = await _busRepo.getAllRoutes();
      final stops = <String>{};
      for (final route in routes) {
        stops.addAll(route.stopNames);
      }
      final sortedStops = stops.toList()..sort();
      setState(() {
        _routes = routes;
        _allStops = sortedStops;
        _loading = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _error = e.message;
        _loading = false;
      });
    }
  }

  void _search() {
    if (_fromStop == null || _toStop == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Select boarding and destination stops')),
      );
      return;
    }
    if (_fromStop == _toStop) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Stops must be different')),
      );
      return;
    }
    context.push('/search-results', extra: {
      'from': _fromStop!,
      'to': _toStop!,
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const HrAppBar(title: 'Haryana Roadways', showLogo: true),
      body: Stack(
        children: [
          if (_error != null)
            ErrorView(message: _error!, onRetry: _loadRoutes)
          else
            RefreshIndicator(
              onRefresh: _loadRoutes,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _buildSearchCard(),
                  const SizedBox(height: 24),
                  Text(
                    'Available Routes',
                    style: GoogleFonts.poppins(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  ..._routes.map(_buildRouteCard),
                ],
              ),
            ),
          if (_loading) const LoadingOverlay(message: 'Loading routes...'),
        ],
      ),
    );
  }

  Widget _buildSearchCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Plan Your Journey',
              style: GoogleFonts.poppins(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: AppColors.deepBlue,
              ),
            ),
            const SizedBox(height: 20),
            DropdownButtonFormField<String>(
              value: _fromStop,
              decoration: const InputDecoration(
                labelText: 'From',
                prefixIcon: Icon(Icons.trip_origin, color: AppColors.green),
              ),
              items: _allStops
                  .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                  .toList(),
              onChanged: (v) => setState(() => _fromStop = v),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _toStop,
              decoration: const InputDecoration(
                labelText: 'To',
                prefixIcon: Icon(Icons.place, color: AppColors.saffron),
              ),
              items: _allStops
                  .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                  .toList(),
              onChanged: (v) => setState(() => _toStop = v),
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: _search,
              icon: const Icon(Icons.search),
              label: const Text('Search Buses'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRouteCard(RouteModel route) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: CircleAvatar(
          backgroundColor: AppColors.saffron.withValues(alpha: 0.15),
          child: Text(
            route.routeNumber,
            style: GoogleFonts.poppins(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: AppColors.deepBlue,
            ),
          ),
        ),
        title: Text(
          route.name,
          style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
        ),
        subtitle: Text(
          '${route.origin} → ${route.destination}\n'
          '${route.totalDistanceKm.toStringAsFixed(0)} km • '
          '${route.estimatedDurationMinutes} min • '
          '${route.stops.length} stops',
          style: GoogleFonts.poppins(fontSize: 12),
        ),
        isThreeLine: true,
      ),
    );
  }
}
