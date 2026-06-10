import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/api/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/aadhaar_banner.dart';
import '../../core/widgets/hr_app_bar.dart';
import '../buses/bus_repository.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late final BusRepository _busRepo;

  String? _fromStop;
  String? _toStop;
  List<String> _allStops = [];
  bool _stopsLoading = false;
  bool _stopsLoaded = false;

  @override
  void initState() {
    super.initState();
    _busRepo = BusRepository(ApiClient());
  }

  Future<void> _ensureStopsLoaded() async {
    if (_stopsLoaded || _stopsLoading) return;

    setState(() => _stopsLoading = true);
    try {
      final routes = await _busRepo.getAllRoutes();
      final stops = <String>{};
      for (final route in routes) {
        stops.addAll(route.stopNames);
      }
      final sortedStops = stops.toList()..sort();
      if (!mounted) return;
      setState(() {
        _allStops = sortedStops;
        _stopsLoaded = true;
        _stopsLoading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _stopsLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.message)),
      );
    } catch (_) {
      if (!mounted) return;
      setState(() => _stopsLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not load stops. Please try again.')),
      );
    }
  }

  Future<void> _search() async {
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

    await _ensureStopsLoaded();
    if (!_stopsLoaded) return;

    if (!mounted) return;
    context.push('/search-results', extra: {
      'from': _fromStop!,
      'to': _toStop!,
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const HrAppBar(title: 'Haryana Roadways', showLogo: true),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const AadhaarBanner(),
          _buildSearchCard(),
          const SizedBox(height: 24),
          Text(
            'Search for buses between any two stops on the Haryana Roadways network.',
            style: GoogleFonts.poppins(
              fontSize: 14,
              color: Colors.grey.shade700,
            ),
            textAlign: TextAlign.center,
          ),
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
              decoration: InputDecoration(
                labelText: 'From',
                prefixIcon: const Icon(Icons.trip_origin, color: AppColors.green),
                suffixIcon: _stopsLoading
                    ? const Padding(
                        padding: EdgeInsets.all(12),
                        child: SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      )
                    : null,
              ),
              hint: const Text('Select boarding stop'),
              items: _allStops
                  .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                  .toList(),
              onTap: _ensureStopsLoaded,
              onChanged: _stopsLoading
                  ? null
                  : (v) => setState(() => _fromStop = v),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _toStop,
              decoration: InputDecoration(
                labelText: 'To',
                prefixIcon: const Icon(Icons.place, color: AppColors.saffron),
                suffixIcon: _stopsLoading
                    ? const Padding(
                        padding: EdgeInsets.all(12),
                        child: SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      )
                    : null,
              ),
              hint: const Text('Select destination'),
              items: _allStops
                  .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                  .toList(),
              onTap: _ensureStopsLoaded,
              onChanged: _stopsLoading
                  ? null
                  : (v) => setState(() => _toStop = v),
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: _stopsLoading ? null : _search,
              icon: const Icon(Icons.search),
              label: const Text('Search Buses'),
            ),
          ],
        ),
      ),
    );
  }
}
