import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_colors.dart';
import '../../core/widgets/hr_app_bar.dart';
import 'auth_cubit.dart';

class AadhaarVerifyScreen extends StatefulWidget {
  const AadhaarVerifyScreen({super.key});

  @override
  State<AadhaarVerifyScreen> createState() => _AadhaarVerifyScreenState();
}

class _AadhaarVerifyScreenState extends State<AadhaarVerifyScreen> {
  final _aadhaarController = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _aadhaarController.dispose();
    super.dispose();
  }

  Future<void> _verify() async {
    final aadhaar = _aadhaarController.text.trim();
    if (!RegExp(r'^\d{12}$').hasMatch(aadhaar)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter a valid 12-digit Aadhaar number')),
      );
      return;
    }
    setState(() => _loading = true);
    final ok = await context.read<AuthCubit>().verifyAadhaar(aadhaar);
    if (!mounted) return;
    setState(() => _loading = false);
    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Aadhaar verified successfully')),
      );
      context.pop(true);
    } else {
      final msg = context.read<AuthCubit>().state.errorMessage;
      if (msg != null) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
        context.read<AuthCubit>().clearMessages();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const HrAppBar(title: 'Aadhaar Verification'),
      body: Stack(
        children: [
          SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: AppColors.saffron.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.saffron.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.fingerprint, color: AppColors.deepBlue, size: 40),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Text(
                          'Aadhaar verification is required to book tickets and apply for bus passes.',
                          style: GoogleFonts.poppins(
                            fontSize: 14,
                            color: AppColors.deepBlue,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 32),
                Text(
                  'Enter Aadhaar Number',
                  style: GoogleFonts.poppins(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Demo mode: any valid 12-digit number works until government API is connected.',
                  style: GoogleFonts.poppins(
                    fontSize: 13,
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: 24),
                TextField(
                  controller: _aadhaarController,
                  keyboardType: TextInputType.number,
                  maxLength: 12,
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  decoration: const InputDecoration(
                    labelText: 'Aadhaar Number',
                    hintText: 'XXXX XXXX XXXX',
                    counterText: '',
                  ),
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: _loading ? null : _verify,
                  child: const Text('Verify Aadhaar'),
                ),
                const SizedBox(height: 12),
                TextButton(
                  onPressed: () => context.pop(false),
                  child: const Text('Skip for now'),
                ),
              ],
            ),
          ),
          if (_loading)
            const ColoredBox(
              color: Colors.black26,
              child: Center(child: CircularProgressIndicator()),
            ),
        ],
      ),
    );
  }
}
