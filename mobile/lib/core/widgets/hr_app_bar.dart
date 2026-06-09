import 'package:flutter/material.dart';

class HrAppBar extends StatelessWidget implements PreferredSizeWidget {
  const HrAppBar({
    super.key,
    required this.title,
    this.actions,
    this.leading,
    this.showLogo = false,
  });

  final String title;
  final List<Widget>? actions;
  final Widget? leading;
  final bool showLogo;

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);

  @override
  Widget build(BuildContext context) {
    return AppBar(
      leading: leading,
      title: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (showLogo) ...[
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Icon(
                Icons.directions_bus,
                size: 18,
                color: Color(0xFF1A365D),
              ),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Text(title, overflow: TextOverflow.ellipsis),
          ),
        ],
      ),
      actions: actions,
    );
  }
}
