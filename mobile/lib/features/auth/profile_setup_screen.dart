import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';

import '../../core/theme/app_colors.dart';
import '../../core/widgets/hr_app_bar.dart';
import 'auth_cubit.dart';

class ProfileSetupScreen extends StatefulWidget {
  const ProfileSetupScreen({super.key});

  @override
  State<ProfileSetupScreen> createState() => _ProfileSetupScreenState();
}

class _ProfileSetupScreenState extends State<ProfileSetupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  DateTime? _dob;
  final _aadhaarController = TextEditingController();
  bool _showAadhaar = false;

  @override
  void dispose() {
    _nameController.dispose();
    _aadhaarController.dispose();
    super.dispose();
  }

  Future<void> _pickDob() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime(now.year - 25),
      firstDate: DateTime(now.year - 120),
      lastDate: now.subtract(const Duration(days: 1)),
    );
    if (picked != null) setState(() => _dob = picked);
  }

  void _submit() {
    if (_formKey.currentState?.validate() ?? false) {
      if (_dob == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please select date of birth')),
        );
        return;
      }
      context.read<AuthCubit>().completeProfile(
            name: _nameController.text.trim(),
            dateOfBirth: DateFormat('yyyy-MM-dd').format(_dob!),
          );
    }
  }

  void _verifyAadhaar() {
    final aadhaar = _aadhaarController.text.trim();
    if (RegExp(r'^\d{12}$').hasMatch(aadhaar)) {
      context.read<AuthCubit>().verifyAadhaar(aadhaar);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter a valid 12-digit Aadhaar number')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const HrAppBar(title: 'Complete Profile'),
      body: BlocConsumer<AuthCubit, AuthState>(
        listener: (context, state) {
          if (state.status == AuthStatus.authenticated) {
            context.go('/home');
          }
          if (state.status == AuthStatus.aadhaarVerified) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.successMessage ?? 'Verified')),
            );
            context.read<AuthCubit>().clearMessages();
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
              SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Tell us about yourself',
                        style: GoogleFonts.poppins(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Required to book tickets and apply for passes',
                        style: GoogleFonts.poppins(
                          color: AppColors.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 32),
                      TextFormField(
                        controller: _nameController,
                        textCapitalization: TextCapitalization.words,
                        decoration: const InputDecoration(
                          labelText: 'Full Name',
                          hintText: 'As per ID proof',
                        ),
                        validator: (v) {
                          if ((v?.trim().length ?? 0) < 2) {
                            return 'Name must be at least 2 characters';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      InkWell(
                        onTap: _pickDob,
                        borderRadius: BorderRadius.circular(12),
                        child: InputDecorator(
                          decoration: const InputDecoration(
                            labelText: 'Date of Birth',
                          ),
                          child: Text(
                            _dob != null
                                ? DateFormat('dd MMM yyyy').format(_dob!)
                                : 'Select date',
                            style: TextStyle(
                              color: _dob != null
                                  ? AppColors.textPrimary
                                  : AppColors.textSecondary,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                      ElevatedButton(
                        onPressed: isLoading ? null : _submit,
                        child: const Text('Save & Continue'),
                      ),
                      const SizedBox(height: 24),
                      TextButton(
                        onPressed: () => setState(() => _showAadhaar = !_showAadhaar),
                        child: Text(
                          _showAadhaar
                              ? 'Hide Aadhaar verification'
                              : 'Verify Aadhaar (optional)',
                        ),
                      ),
                      if (_showAadhaar) ...[
                        const SizedBox(height: 8),
                        TextFormField(
                          controller: _aadhaarController,
                          keyboardType: TextInputType.number,
                          maxLength: 12,
                          decoration: const InputDecoration(
                            labelText: 'Aadhaar Number',
                            hintText: '12-digit number',
                          ),
                        ),
                        OutlinedButton(
                          onPressed: isLoading ? null : _verifyAadhaar,
                          child: const Text('Verify Aadhaar'),
                        ),
                      ],
                    ],
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
