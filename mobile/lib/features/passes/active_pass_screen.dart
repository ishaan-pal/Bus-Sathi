import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/api/api_client.dart';
import '../../core/api/app_api.dart';
import '../../core/models/pass_model.dart';
import '../../core/theme/app_colors.dart';
import '../../core/utils/safe_state.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_view.dart';
import '../../core/widgets/hr_app_bar.dart';
import '../../core/widgets/loading_overlay.dart';
import '../../core/widgets/verification_token_display.dart';
import 'pass_repository.dart';

class ActivePassScreen extends StatefulWidget {
  const ActivePassScreen({super.key});

  @override
  State<ActivePassScreen> createState() => _ActivePassScreenState();
}

class _ActivePassScreenState extends State<ActivePassScreen>
    with AsyncRequestGuard, SafeSetState {
  late final PassRepository _repo;
  ActivePassModel? _pass;
  List<PassListItemModel> _history = [];
  bool _loading = true;
  String? _error;
  bool _noActivePass = false;

  @override
  void initState() {
    super.initState();
    _repo = PassRepository(AppApi.client);
    _load();
  }

  Future<void> _load() async {
    final generation = beginRequest();
    safeSetState(() {
      _loading = true;
      _error = null;
      _noActivePass = false;
    });

    try {
      final pass = await _repo.getActivePass();
      if (!isCurrentRequest(generation)) return;

      List<PassListItemModel> history = [];
      try {
        history = await _repo.getPassHistory();
      } catch (_) {}

      if (!isCurrentRequest(generation)) return;
      safeSetState(() {
        _pass = pass;
        _history = history;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (!isCurrentRequest(generation)) return;

      if (e.statusCode == 404) {
        List<PassListItemModel> history = [];
        try {
          history = await _repo.getPassHistory();
        } catch (_) {}

        if (!isCurrentRequest(generation)) return;
        safeSetState(() {
          _noActivePass = true;
          _history = history;
          _loading = false;
        });
      } else if (e.isConnectivityError) {
        safeSetState(() {
          _error = e.message;
          _loading = false;
        });
      } else {
        safeSetState(() {
          _error = e.message;
          _loading = false;
        });
      }
    } catch (_) {
      if (!isCurrentRequest(generation)) return;
      safeSetState(() {
        _error = 'Could not load pass information.';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: HrAppBar(
        title: 'My Pass',
        actions: [
          IconButton(
            icon: const Icon(Icons.add_card),
            onPressed: () => context.push('/passes/apply'),
            tooltip: 'Apply for pass',
          ),
        ],
      ),
      body: Stack(
        children: [
          if (_error != null)
            ErrorView(message: _error!, onRetry: _load)
          else
            RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (_pass != null) ...[
                    VerificationTokenDisplay(
                      token: _pass!.verificationToken,
                      banner: _pass!.verificationBanner,
                      onRefresh: _load,
                    ),
                    const SizedBox(height: 16),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              _pass!.passNumber,
                              style: GoogleFonts.poppins(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: AppColors.deepBlue,
                              ),
                            ),
                            const SizedBox(height: 12),
                            _row('Holder', _pass!.applicantName),
                            _row('Type', _pass!.passType.replaceAll('_', ' ')),
                            if (_pass!.routeNumber != null)
                              _row('Route', _pass!.routeNumber!),
                            if (_pass!.fromStop != null && _pass!.toStop != null)
                              _row('Journey', '${_pass!.fromStop} → ${_pass!.toStop}'),
                            _row('Valid From', _pass!.validFrom),
                            _row('Valid Until', _pass!.validUntil),
                            if (_pass!.daysRemaining != null)
                              _row('Days Left', '${_pass!.daysRemaining}'),
                          ],
                        ),
                      ),
                    ),
                  ] else if (_noActivePass)
                    const EmptyState(
                      icon: Icons.card_membership_outlined,
                      title: 'No active pass',
                      subtitle: 'Apply for a student, monthly, or senior pass',
                    ),
                  if (_history.isNotEmpty) ...[
                    const SizedBox(height: 24),
                    Text(
                      'Pass History',
                      style: GoogleFonts.poppins(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 8),
                    ..._history.map((p) => Card(
                          child: ListTile(
                            title: Text(
                              p.passType.replaceAll('_', ' '),
                              style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
                            ),
                            subtitle: Text(
                              '${p.status} • ${p.createdAt.split('T').first}',
                            ),
                            trailing: const Icon(Icons.chevron_right),
                            onTap: () =>
                                context.push('/passes/status/${p.passId}'),
                          ),
                        )),
                  ],
                  const SizedBox(height: 16),
                  OutlinedButton.icon(
                    onPressed: () => context.push('/passes/apply'),
                    icon: const Icon(Icons.add),
                    label: const Text('Apply for New Pass'),
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
