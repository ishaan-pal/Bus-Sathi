import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_colors.dart';
import '../../features/auth/auth_cubit.dart';

/// Prompts user to verify Aadhaar before protected actions.
Future<bool> ensureAadhaarVerified(BuildContext context) async {
  final cubit = context.read<AuthCubit>();
  await cubit.ensureSession();
  if (!context.mounted) return false;
  if (cubit.state.isAadhaarVerified) return true;

  final result = await context.push<bool>('/aadhaar-verify');
  if (!context.mounted) return false;
  return result == true || cubit.state.isAadhaarVerified;
}

class AadhaarBanner extends StatelessWidget {
  const AadhaarBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuthCubit, AuthState>(
      buildWhen: (prev, curr) =>
          prev.user?.aadhaarVerified != curr.user?.aadhaarVerified,
      builder: (context, state) {
        if (state.isAadhaarVerified) return const SizedBox.shrink();
        return Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          child: Material(
            color: AppColors.saffron.withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(12),
            child: InkWell(
              onTap: () => context.push('/aadhaar-verify'),
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Row(
                  children: [
                    const Icon(Icons.fingerprint, color: AppColors.deepBlue),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Verify Aadhaar to book tickets & apply for passes',
                        style: GoogleFonts.poppins(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: AppColors.deepBlue,
                        ),
                      ),
                    ),
                    const Icon(Icons.chevron_right, color: AppColors.deepBlue),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
