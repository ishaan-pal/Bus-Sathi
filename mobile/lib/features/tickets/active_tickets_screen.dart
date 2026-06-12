import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/api/api_client.dart';
import '../../core/api/app_api.dart';
import '../../core/models/ticket_model.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_view.dart';
import '../../core/widgets/hr_app_bar.dart';
import '../../core/widgets/loading_overlay.dart';
import 'ticket_repository.dart';

class ActiveTicketsScreen extends StatefulWidget {
  const ActiveTicketsScreen({super.key});

  @override
  State<ActiveTicketsScreen> createState() => _ActiveTicketsScreenState();
}

class _ActiveTicketsScreenState extends State<ActiveTicketsScreen> {
  late final TicketRepository _repo;
  List<ActiveTicketModel> _tickets = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _repo = TicketRepository(AppApi.client);
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final tickets = await _repo.getActiveTickets();
      setState(() {
        _tickets = tickets;
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
      appBar: const HrAppBar(title: 'My Tickets'),
      body: Stack(
        children: [
          RefreshIndicator(
            onRefresh: _load,
            child: _error != null
                ? ListView(
                    children: [SizedBox(
                      height: MediaQuery.of(context).size.height * 0.6,
                      child: ErrorView(message: _error!, onRetry: _load),
                    )],
                  )
                : _tickets.isEmpty && !_loading
                    ? ListView(
                        children: const [
                          SizedBox(
                            height: 300,
                            child: EmptyState(
                              icon: Icons.confirmation_number_outlined,
                              title: 'No active tickets',
                              subtitle: 'Book a ticket from the home screen',
                            ),
                          ),
                        ],
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _tickets.length,
                        itemBuilder: (context, index) {
                          final t = _tickets[index];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: ListTile(
                              contentPadding: const EdgeInsets.all(16),
                              leading: CircleAvatar(
                                backgroundColor:
                                    AppColors.saffron.withValues(alpha: 0.15),
                                child: const Icon(
                                  Icons.confirmation_number,
                                  color: AppColors.saffron,
                                ),
                              ),
                              title: Text(
                                t.ticketNumber,
                                style: GoogleFonts.poppins(
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              subtitle: Text(
                                'Bus ${t.busNumber}\n'
                                '${t.boardingStop} → ${t.destinationStop}\n'
                                '${t.journeyDate} at ${t.journeyTime}',
                                style: GoogleFonts.poppins(fontSize: 12),
                              ),
                              isThreeLine: true,
                              trailing: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: [
                                  Text(
                                    '₹${t.totalFareRupees.toStringAsFixed(0)}',
                                    style: GoogleFonts.poppins(
                                      fontWeight: FontWeight.bold,
                                      color: AppColors.deepBlue,
                                    ),
                                  ),
                                  Text(
                                    t.status.toUpperCase(),
                                    style: GoogleFonts.poppins(
                                      fontSize: 10,
                                      color: AppColors.green,
                                    ),
                                  ),
                                ],
                              ),
                              onTap: () => context.push('/tickets/${t.ticketId}'),
                            ),
                          );
                        },
                      ),
          ),
          if (_loading) const LoadingOverlay(),
        ],
      ),
    );
  }
}
