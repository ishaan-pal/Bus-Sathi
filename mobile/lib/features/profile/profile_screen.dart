import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_colors.dart';
import '../../core/widgets/hr_app_bar.dart';
import '../auth/auth_cubit.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const HrAppBar(title: 'Profile'),
      body: BlocBuilder<AuthCubit, AuthState>(
        builder: (context, state) {
          final user = state.user;
          if (user == null) {
            return const Center(child: CircularProgressIndicator());
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      CircleAvatar(
                        radius: 40,
                        backgroundColor: AppColors.deepBlue,
                        child: Text(
                          (user.name?.isNotEmpty == true
                                  ? user.name![0]
                                  : user.mobile[0])
                              .toUpperCase(),
                          style: GoogleFonts.poppins(
                            fontSize: 32,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        user.name ?? 'Passenger',
                        style: GoogleFonts.poppins(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        '+91 ${user.mobile}',
                        style: GoogleFonts.poppins(
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              _infoTile(Icons.phone, 'Mobile', '+91 ${user.mobile}'),
              if (user.dateOfBirth != null)
                _infoTile(Icons.cake, 'Date of Birth', user.dateOfBirth!),
              if (user.age != null)
                _infoTile(Icons.person, 'Age', '${user.age} years'),
              _infoTile(
                Icons.verified_user,
                'Profile',
                user.profileComplete ? 'Complete' : 'Incomplete',
              ),
              _infoTile(
                Icons.fingerprint,
                'Aadhaar',
                user.aadhaarVerified ? 'Verified' : 'Not verified',
              ),
              if (user.isSeniorCitizen)
                _infoTile(Icons.elderly, 'Category', 'Senior Citizen'),
              const SizedBox(height: 24),
              OutlinedButton.icon(
                onPressed: () async {
                  await context.read<AuthCubit>().logout();
                  if (context.mounted) context.go('/login');
                },
                icon: const Icon(Icons.logout, color: AppColors.error),
                label: Text(
                  'Logout',
                  style: GoogleFonts.poppins(color: AppColors.error),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _infoTile(IconData icon, String label, String value) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Icon(icon, color: AppColors.deepBlue),
        title: Text(label, style: GoogleFonts.poppins(fontSize: 12)),
        subtitle: Text(
          value,
          style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
        ),
      ),
    );
  }
}
