import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/api/api_client.dart';
import '../../core/api/app_api.dart';
import '../../core/demo_stops.dart';
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
  bool _usingDemoStops = false;

  @override
  void initState() {
    super.initState();
    _busRepo = BusRepository(AppApi.client);
    _loadStops();
  }

  Future<void> _loadStops() async {
    if (_stopsLoaded || _stopsLoading) return;

    setState(() => _stopsLoading = true);
    try {
      final stops = await _busRepo.getAllStops();
      if (!mounted) return;
      setState(() {
        _allStops = stops;
        _stopsLoaded = true;
        _stopsLoading = false;
        _usingDemoStops = false;
      });
    } on ApiException catch (e) {
      _applyDemoStops(message: e.message);
    } catch (_) {
      _applyDemoStops(
        message: 'Could not reach server. Using demo stops for testing.',
      );
    }
  }

  void _applyDemoStops({required String message}) {
    if (!mounted) return;
    setState(() {
      _allStops = List<String>.from(DemoStops.all);
      _stopsLoaded = true;
      _stopsLoading = false;
      _usingDemoStops = true;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  Future<void> _pickStop({
    required String title,
    required String? currentValue,
    required ValueChanged<String> onSelected,
  }) async {
    if (!_stopsLoaded) {
      await _loadStops();
    }
    if (!mounted || _allStops.isEmpty) return;

    final selected = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => _StopPickerSheet(
        title: title,
        stops: _allStops,
        selected: currentValue,
      ),
    );

    if (selected != null) {
      onSelected(selected);
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
    if (!_stopsLoaded) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Stops are still loading. Please wait.')),
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
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const AadhaarBanner(),
          if (_usingDemoStops)
            Card(
              color: AppColors.saffron.withValues(alpha: 0.12),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    const Icon(Icons.info_outline, color: AppColors.saffron),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Using demo stops. Connect to the backend for live data.',
                        style: GoogleFonts.poppins(fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          _buildSearchCard(),
          const SizedBox(height: 24),
          Text(
            _stopsLoading
                ? 'Loading stations...'
                : 'Select boarding and destination, then search for buses.',
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
            _buildStopField(
              label: 'From',
              value: _fromStop,
              hint: 'Tap to select boarding stop',
              icon: Icons.trip_origin,
              iconColor: AppColors.green,
              onTap: () => _pickStop(
                title: 'Select boarding stop',
                currentValue: _fromStop,
                onSelected: (stop) => setState(() => _fromStop = stop),
              ),
            ),
            const SizedBox(height: 12),
            _buildStopField(
              label: 'To',
              value: _toStop,
              hint: 'Tap to select destination',
              icon: Icons.place,
              iconColor: AppColors.saffron,
              onTap: () => _pickStop(
                title: 'Select destination',
                currentValue: _toStop,
                onSelected: (stop) => setState(() => _toStop = stop),
              ),
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

  Widget _buildStopField({
    required String label,
    required String? value,
    required String hint,
    required IconData icon,
    required Color iconColor,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: _stopsLoading ? null : onTap,
      borderRadius: BorderRadius.circular(12),
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: Icon(icon, color: iconColor),
          suffixIcon: _stopsLoading
              ? const Padding(
                  padding: EdgeInsets.all(12),
                  child: SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                )
              : const Icon(Icons.arrow_drop_down),
        ),
        child: Text(
          value ?? hint,
          style: GoogleFonts.poppins(
            color: value == null ? Colors.grey.shade600 : Colors.black87,
          ),
        ),
      ),
    );
  }
}

class _StopPickerSheet extends StatefulWidget {
  const _StopPickerSheet({
    required this.title,
    required this.stops,
    this.selected,
  });

  final String title;
  final List<String> stops;
  final String? selected;

  @override
  State<_StopPickerSheet> createState() => _StopPickerSheetState();
}

class _StopPickerSheetState extends State<_StopPickerSheet> {
  late List<String> _filtered;
  final _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _filtered = widget.stops;
    _searchController.addListener(_filter);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _filter() {
    final query = _searchController.text.trim().toLowerCase();
    setState(() {
      _filtered = query.isEmpty
          ? widget.stops
          : widget.stops
              .where((stop) => stop.toLowerCase().contains(query))
              .toList();
    });
  }

  @override
  Widget build(BuildContext context) {
    final maxHeight = MediaQuery.of(context).size.height * 0.75;

    return SafeArea(
      child: SizedBox(
        height: maxHeight,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
              child: Text(
                widget.title,
                style: GoogleFonts.poppins(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                controller: _searchController,
                decoration: const InputDecoration(
                  hintText: 'Search station...',
                  prefixIcon: Icon(Icons.search),
                ),
              ),
            ),
            Expanded(
              child: _filtered.isEmpty
                  ? Center(
                      child: Text(
                        'No stations found',
                        style: GoogleFonts.poppins(color: Colors.grey),
                      ),
                    )
                  : ListView.builder(
                      itemCount: _filtered.length,
                      itemBuilder: (context, index) {
                        final stop = _filtered[index];
                        final isSelected = stop == widget.selected;
                        return ListTile(
                          title: Text(stop),
                          trailing: isSelected
                              ? const Icon(Icons.check, color: AppColors.green)
                              : null,
                          onTap: () => Navigator.pop(context, stop),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
