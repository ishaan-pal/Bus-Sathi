import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:pin_code_fields/pin_code_fields.dart';

import '../../core/config.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/hr_app_bar.dart';
import 'auth_cubit.dart';

class OtpScreen extends StatefulWidget {
  const OtpScreen({super.key, required this.mobile});

  final String mobile;

  @override
  State<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends State<OtpScreen> {
  String _otp = '';

  void _verify() {
    if (_otp.length == 6) {
      context.read<AuthCubit>().verifyOtp(_otp);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: HrAppBar(
        title: 'Verify OTP',
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: BlocConsumer<AuthCubit, AuthState>(
        listener: (context, state) {
          if (state.status == AuthStatus.needsProfile) {
            context.go('/profile-setup');
          } else if (state.status == AuthStatus.authenticated) {
            context.go('/home');
          }
          if (state.errorMessage != null &&
              state.status == AuthStatus.failure) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.errorMessage!)),
            );
            context.read<AuthCubit>().clearMessages();
          }
        },
        builder: (context, state) {
          final isLoading = state.status == AuthStatus.loading;
          return Stack(
            children: [
              Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'Enter OTP',
                      style: GoogleFonts.poppins(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Sent to +91 ${widget.mobile}',
                      style: GoogleFonts.poppins(color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 32),
                    PinCodeTextField(
                      appContext: context,
                      length: 6,
                      keyboardType: TextInputType.number,
                      animationType: AnimationType.fade,
                      pinTheme: PinTheme(
                        shape: PinCodeFieldShape.box,
                        borderRadius: BorderRadius.circular(12),
                        fieldHeight: 52,
                        fieldWidth: 44,
                        activeColor: AppColors.deepBlue,
                        selectedColor: AppColors.saffron,
                        inactiveColor: Colors.grey.shade300,
                      ),
                      onChanged: (value) => _otp = value,
                      onCompleted: (value) {
                        _otp = value;
                        _verify();
                      },
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: isLoading ? null : _verify,
                      child: const Text('Verify & Continue'),
                    ),
                    const SizedBox(height: 16),
                    TextButton(
                      onPressed: isLoading
                          ? null
                          : () => context
                              .read<AuthCubit>()
                              .sendOtp(widget.mobile),
                      child: const Text('Resend OTP'),
                    ),
                    const Spacer(),
                    Text(
                      'Dev OTP: ${AppConfig.devOtp}',
                      textAlign: TextAlign.center,
                      style: GoogleFonts.poppins(
                        fontSize: 12,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              if (isLoading)
                const ColoredBox(
                  color: Colors.black26,
                  child: Center(child: CircularProgressIndicator()),
                ),
            ],
          );
        },
      ),
    );
  }
}
