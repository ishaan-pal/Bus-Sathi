import 'dart:async';

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../config.dart';
import '../theme/app_colors.dart';

class VerificationTokenDisplay extends StatefulWidget {
  const VerificationTokenDisplay({
    super.key,
    required this.token,
    required this.banner,
    this.onRefresh,
    this.expiresAt,
  });

  final String? token;
  final String banner;
  final Future<void> Function()? onRefresh;
  final String? expiresAt;

  @override
  State<VerificationTokenDisplay> createState() =>
      _VerificationTokenDisplayState();
}

class _VerificationTokenDisplayState extends State<VerificationTokenDisplay>
    with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    _startRefreshTimer();
  }

  @override
  void didUpdateWidget(VerificationTokenDisplay oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.token != widget.token) {
      _startRefreshTimer();
    }
  }

  void _startRefreshTimer() {
    _refreshTimer?.cancel();
    if (widget.onRefresh != null) {
      _refreshTimer = Timer.periodic(AppConfig.tokenRefreshInterval, (_) {
        widget.onRefresh?.call();
      });
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _refreshTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final token = widget.token ?? '--------';
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.deepBlue, Color(0xFF2D4A7A)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: AppColors.deepBlue.withValues(alpha: 0.3),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          FadeTransition(
            opacity: Tween<double>(begin: 0.7, end: 1.0).animate(
              CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: AppColors.green,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  widget.banner,
                  style: GoogleFonts.poppins(
                    color: Colors.white70,
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 1.2,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Text(
            token,
            style: GoogleFonts.poppins(
              color: Colors.white,
              fontSize: 36,
              fontWeight: FontWeight.bold,
              letterSpacing: 8,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Show this code to the conductor',
            style: GoogleFonts.poppins(
              color: Colors.white60,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}
