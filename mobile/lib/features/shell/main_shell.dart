import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../home/home_screen.dart';
import '../passes/active_pass_screen.dart';
import '../profile/profile_screen.dart';
import '../tickets/active_tickets_screen.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: widget.navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: widget.navigationShell.currentIndex,
        onDestinationSelected: widget.navigationShell.goBranch,
        indicatorColor: AppColors.saffron.withValues(alpha: 0.2),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.confirmation_number_outlined),
            selectedIcon: Icon(Icons.confirmation_number),
            label: 'Tickets',
          ),
          NavigationDestination(
            icon: Icon(Icons.card_membership_outlined),
            selectedIcon: Icon(Icons.card_membership),
            label: 'Pass',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}

/// Branch screens for StatefulShellRoute
class HomeBranch extends StatelessWidget {
  const HomeBranch({super.key});
  @override
  Widget build(BuildContext context) => const HomeScreen();
}

class TicketsBranch extends StatelessWidget {
  const TicketsBranch({super.key});
  @override
  Widget build(BuildContext context) => const ActiveTicketsScreen();
}

class PassBranch extends StatelessWidget {
  const PassBranch({super.key});
  @override
  Widget build(BuildContext context) => const ActivePassScreen();
}

class ProfileBranch extends StatelessWidget {
  const ProfileBranch({super.key});
  @override
  Widget build(BuildContext context) => const ProfileScreen();
}
