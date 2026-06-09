import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/api/api_client.dart';
import '../../core/models/ticket_model.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/error_view.dart';
import '../../core/widgets/hr_app_bar.dart';
import '../../core/widgets/loading_overlay.dart';
import '../../core/widgets/verification_token_display.dart';
import 'ticket_repository.dart';

class TicketDetailScreen extends StatefulWidget {
  const TicketDetailScreen({super.key, required this.ticketId});

  final String ticketId;

  @override
  State<TicketDetailScreen> createState() => _TicketDetailScreenState();
}

class _TicketDetailScreenState extends State<TicketDetailScreen> {
  late final TicketRepository _repo;
  TicketDetailModel? _ticket;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _repo = TicketRepository(ApiClient());
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final ticket = await _repo.getTicketDetail(widget.ticketId);
      setState(() {
        _ticket = ticket;
        _loading = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _error = e.message;
        _loading = false;
      });
    }
  }

  Future<void> _refreshToken() async {
    try {
      final token = await _repo.refreshVerificationToken(widget.ticketId);
      if (mounted && _ticket != null) {
        setState(() {
          _ticket = TicketDetailModel(
            ticketId: _ticket!.ticketId,
            ticketNumber: _ticket!.ticketNumber,
            passengerName: _ticket!.passengerName,
            passengerMobile: _ticket!.passengerMobile,
            busNumber: _ticket!.busNumber,
            routeNumber: _ticket!.routeNumber,
            boardingStop: _ticket!.boardingStop,
            destinationStop: _ticket!.destinationStop,
            journeyDate: _ticket!.journeyDate,
            journeyTime: _ticket!.journeyTime,
            adultCount: _ticket!.adultCount,
            childCount: _ticket!.childCount,
            seniorCount: _ticket!.seniorCount,
            totalPassengers: _ticket!.totalPassengers,
            adultFareRupees: _ticket!.adultFareRupees,
            childFareRupees: _ticket!.childFareRupees,
            seniorFareRupees: _ticket!.seniorFareRupees,
            totalFareRupees: _ticket!.totalFareRupees,
            paymentMethod: _ticket!.paymentMethod,
            paidAt: _ticket!.paidAt,
            status: _ticket!.status,
            isValidForTravel: _ticket!.isValidForTravel,
            expiresAt: _ticket!.expiresAt,
            verificationToken: token,
            verificationTokenExpires: _ticket!.verificationTokenExpires,
            currentTimestamp: _ticket!.currentTimestamp,
            verificationBanner: _ticket!.verificationBanner,
          );
        });
      }
    } catch (_) {
      await _load();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: HrAppBar(
        title: 'Ticket',
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: Stack(
        children: [
          if (_error != null)
            ErrorView(message: _error!, onRetry: _load)
          else if (_ticket != null)
            RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  VerificationTokenDisplay(
                    token: _ticket!.verificationToken,
                    banner: _ticket!.verificationBanner,
                    onRefresh: _refreshToken,
                    expiresAt: _ticket!.verificationTokenExpires,
                  ),
                  const SizedBox(height: 16),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _ticket!.ticketNumber,
                            style: GoogleFonts.poppins(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: AppColors.deepBlue,
                            ),
                          ),
                          const SizedBox(height: 12),
                          _row('Passenger', _ticket!.passengerName),
                          _row('Mobile', _ticket!.passengerMobile),
                          _row('Bus', _ticket!.busNumber),
                          if (_ticket!.routeNumber != null)
                            _row('Route', _ticket!.routeNumber!),
                          _row('From', _ticket!.boardingStop),
                          _row('To', _ticket!.destinationStop),
                          _row('Date', _ticket!.journeyDate),
                          _row('Time', _ticket!.journeyTime),
                          _row('Passengers', '${_ticket!.totalPassengers}'),
                          _row('Fare', '₹${_ticket!.totalFareRupees.toStringAsFixed(2)}'),
                          _row('Status', _ticket!.status.toUpperCase()),
                          if (!_ticket!.isValidForTravel)
                            const Padding(
                              padding: EdgeInsets.only(top: 8),
                              child: Text(
                                'Not valid for travel',
                                style: TextStyle(color: AppColors.error),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          if (_loading) const LoadingOverlay(),
        ],
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
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
