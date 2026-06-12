import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/api/api_client.dart';
import '../../core/api/app_api.dart';
import '../../core/models/pass_model.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/error_view.dart';
import '../../core/widgets/hr_app_bar.dart';
import '../../core/widgets/loading_overlay.dart';
import 'pass_repository.dart';

class PassStatusScreen extends StatefulWidget {
  const PassStatusScreen({super.key, required this.passId});

  final String passId;

  @override
  State<PassStatusScreen> createState() => _PassStatusScreenState();
}

class _PassStatusScreenState extends State<PassStatusScreen> {
  late final PassRepository _repo;
  PassStatusModel? _status;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _repo = PassRepository(AppApi.client);
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final status = await _repo.getPassStatus(widget.passId);
      setState(() {
        _status = status;
        _loading = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _error = e.message;
        _loading = false;
      });
    }
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'approved':
        return AppColors.green;
      case 'rejected':
        return AppColors.error;
      default:
        return AppColors.saffron;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: HrAppBar(
        title: 'Pass Status',
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: Stack(
        children: [
          if (_error != null)
            ErrorView(message: _error!, onRetry: _load)
          else if (_status != null)
            RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        children: [
                          Icon(
                            _status!.status == 'approved'
                                ? Icons.check_circle
                                : _status!.status == 'rejected'
                                    ? Icons.cancel
                                    : Icons.hourglass_top,
                            size: 64,
                            color: _statusColor(_status!.status),
                          ),
                          const SizedBox(height: 12),
                          Text(
                            _status!.status.replaceAll('_', ' ').toUpperCase(),
                            style: GoogleFonts.poppins(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: _statusColor(_status!.status),
                            ),
                          ),
                          if (_status!.passNumber != null) ...[
                            const SizedBox(height: 8),
                            Text('Pass #${_status!.passNumber}'),
                          ],
                          Text(
                            _status!.passType.replaceAll('_', ' '),
                            style: GoogleFonts.poppins(
                              color: AppColors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  if (_status!.rejectionReason != null) ...[
                    const SizedBox(height: 12),
                    Card(
                      color: AppColors.error.withValues(alpha: 0.05),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Text(
                          'Reason: ${_status!.rejectionReason}',
                          style: const TextStyle(color: AppColors.error),
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 16),
                  Text(
                    'Documents',
                    style: GoogleFonts.poppins(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ..._status!.requiredDocuments.map((doc) {
                    final uploaded = _status!.uploadedDocuments[doc] ?? false;
                    return Card(
                      child: ListTile(
                        leading: Icon(
                          uploaded ? Icons.check_circle : Icons.pending,
                          color: uploaded ? AppColors.green : AppColors.saffron,
                        ),
                        title: Text(doc.replaceAll('_', ' ')),
                        subtitle: Text(uploaded ? 'Uploaded' : 'Pending'),
                      ),
                    );
                  }),
                  if (_status!.status == 'approved') ...[
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () => context.go('/passes/active'),
                      child: const Text('View Active Pass'),
                    ),
                  ],
                ],
              ),
            ),
          if (_loading) const LoadingOverlay(),
        ],
      ),
    );
  }
}
