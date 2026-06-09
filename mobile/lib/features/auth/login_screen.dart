import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/config.dart';
import '../../core/theme/app_colors.dart';
import 'auth_cubit.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _mobileController = TextEditingController();

  @override
  void dispose() {
    _mobileController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState?.validate() ?? false) {
      context.read<AuthCubit>().sendOtp(_mobileController.text.trim());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: BlocConsumer<AuthCubit, AuthState>(
        listener: (context, state) {
          if (state.status == AuthStatus.otpSent) {
            context.push('/otp', extra: state.mobile);
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
              SafeArea(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(24),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const SizedBox(height: 40),
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            color: AppColors.deepBlue,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: const Icon(
                            Icons.directions_bus,
                            color: Colors.white,
                            size: 44,
                          ),
                        ),
                        const SizedBox(height: 24),
                        Text(
                          'Haryana Roadways',
                          style: GoogleFonts.poppins(
                            fontSize: 28,
                            fontWeight: FontWeight.bold,
                            color: AppColors.deepBlue,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Book tickets, track buses & manage passes',
                          style: GoogleFonts.poppins(
                            color: AppColors.textSecondary,
                          ),
                        ),
                        const SizedBox(height: 48),
                        Text(
                          'Mobile Number',
                          style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
                        ),
                        const SizedBox(height: 8),
                        TextFormField(
                          controller: _mobileController,
                          keyboardType: TextInputType.phone,
                          maxLength: 10,
                          inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                          decoration: const InputDecoration(
                            hintText: '10-digit mobile number',
                            prefixText: '+91 ',
                            counterText: '',
                          ),
                          validator: (value) {
                            final v = value?.trim() ?? '';
                            if (!RegExp(r'^[6-9]\d{9}$').hasMatch(v)) {
                              return 'Enter a valid 10-digit mobile number';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 24),
                        ElevatedButton(
                          onPressed: isLoading ? null : _submit,
                          child: const Text('Send OTP'),
                        ),
                        const SizedBox(height: 16),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppColors.saffron.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            'Dev mode: Use OTP ${AppConfig.devOtp} for any number',
                            style: GoogleFonts.poppins(
                              fontSize: 12,
                              color: AppColors.deepBlue,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ],
                    ),
                  ),
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
