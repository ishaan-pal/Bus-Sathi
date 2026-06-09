import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

class LoadingOverlay extends StatelessWidget {
  const LoadingOverlay({super.key, this.message});

  final String? message;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.black26,
      alignment: Alignment.center,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(color: AppColors.saffron),
              if (message != null) ...[
                const SizedBox(height: 16),
                Text(message!, textAlign: TextAlign.center),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
