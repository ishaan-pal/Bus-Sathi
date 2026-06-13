import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_colors.dart';
import '../../core/widgets/aadhaar_banner.dart';
import '../../core/widgets/hr_app_bar.dart';
import '../../core/widgets/stop_search_field.dart';
import '../../core/services/stops_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.stopsService});

  final StopsService stopsService;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String? _fromStop;
  String? _toStop;

  void _swapStops() {
    setState(() {
      final temp = _fromStop;
      _fromStop = _toStop;
      _toStop = temp;
    });
  }

  void _search() {
    final from = _fromStop?.trim();
    final to = _toStop?.trim();

    if (from == null || from.isEmpty || to == null || to.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter boarding and destination stops')),
      );
      return;
    }
    if (from == to) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Stops must be different')),
      );
      return;
    }

    context.push('/search-results', extra: {
      'from': from,
      'to': to,
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const HrAppBar(title: 'Bus Saathi', showLogo: true),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const AadhaarBanner(),
          _buildSearchCard(),
          const SizedBox(height: 16),
          Text(
            'Type a city or station name — suggestions appear as you type.',
            style: GoogleFonts.poppins(
              fontSize: 13,
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
            StopSearchField(
              key: ValueKey('from-${_fromStop ?? ''}-${_toStop ?? ''}'),
              label: 'From',
              hint: 'Boarding stop',
              icon: Icons.trip_origin,
              iconColor: AppColors.green,
              stopsService: widget.stopsService,
              initialValue: _fromStop,
              excludeStops: _toStop != null ? {_toStop!} : const {},
              onChanged: (v) => _fromStop = v.trim().isEmpty ? null : v.trim(),
              onSelected: (stop) => setState(() => _fromStop = stop),
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerRight,
              child: IconButton(
                tooltip: 'Swap',
                onPressed: _fromStop == null && _toStop == null ? null : _swapStops,
                icon: const Icon(Icons.swap_vert, color: AppColors.deepBlue),
              ),
            ),
            StopSearchField(
              key: ValueKey('to-${_toStop ?? ''}-${_fromStop ?? ''}'),
              label: 'To',
              hint: 'Destination stop',
              icon: Icons.place,
              iconColor: AppColors.saffron,
              stopsService: widget.stopsService,
              initialValue: _toStop,
              excludeStops: _fromStop != null ? {_fromStop!} : const {},
              onChanged: (v) => _toStop = v.trim().isEmpty ? null : v.trim(),
              onSelected: (stop) => setState(() => _toStop = stop),
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
}
