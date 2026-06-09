import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/api/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/hr_app_bar.dart';
import '../../core/widgets/loading_overlay.dart';
import 'ticket_repository.dart';

class BookingScreen extends StatefulWidget {
  const BookingScreen({
    super.key,
    required this.busId,
    required this.fromStop,
    required this.toStop,
    required this.adults,
    required this.children,
    required this.seniors,
    this.busNumber,
    this.fare,
  });

  final String busId;
  final String fromStop;
  final String toStop;
  final int adults;
  final int children;
  final int seniors;
  final String? busNumber;
  final double? fare;

  @override
  State<BookingScreen> createState() => _BookingScreenState();
}

class _BookingScreenState extends State<BookingScreen> {
  late final TicketRepository _repo;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _repo = TicketRepository(ApiClient());
  }

  Future<void> _bookAndPay() async {
    setState(() => _loading = true);
    try {
      final booking = await _repo.bookTicket(
        busId: widget.busId,
        boardingStop: widget.fromStop,
        destinationStop: widget.toStop,
        adultCount: widget.adults,
        childCount: widget.children,
        seniorCount: widget.seniors,
      );
      await _repo.confirmPayment(ticketId: booking.ticketId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Payment confirmed! Ticket activated.')),
      );
      context.go('/tickets/${booking.ticketId}');
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.message)),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: HrAppBar(
        title: 'Confirm Booking',
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: Stack(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Booking Summary',
                          style: GoogleFonts.poppins(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 16),
                        if (widget.busNumber != null)
                          _row('Bus', widget.busNumber!),
                        _row('From', widget.fromStop),
                        _row('To', widget.toStop),
                        _row('Passengers',
                            '${widget.adults} adult(s), ${widget.children} child(ren), ${widget.seniors} senior(s)'),
                        if (widget.fare != null)
                          _row('Total Fare', '₹${widget.fare!.toStringAsFixed(2)}'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.green.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    'Demo payment mode: Tap Pay to auto-confirm with demo credentials.',
                    style: GoogleFonts.poppins(fontSize: 13),
                  ),
                ),
                const Spacer(),
                ElevatedButton.icon(
                  onPressed: _loading ? null : _bookAndPay,
                  icon: const Icon(Icons.payment),
                  label: const Text('Pay & Confirm'),
                ),
              ],
            ),
          ),
          if (_loading) const LoadingOverlay(message: 'Processing payment...'),
        ],
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 100,
            child: Text(label, style: GoogleFonts.poppins(color: AppColors.textSecondary)),
          ),
          Expanded(
            child: Text(value, style: GoogleFonts.poppins(fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }
}
