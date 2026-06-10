import 'package:go_router/go_router.dart';

import '../../features/auth/aadhaar_verify_screen.dart';
import '../../features/buses/bus_detail_screen.dart';
import '../../features/buses/search_results_screen.dart';
import '../../features/passes/active_pass_screen.dart';
import '../../features/passes/apply_pass_screen.dart';
import '../../features/passes/pass_status_screen.dart';
import '../../features/shell/main_shell.dart';
import '../../features/tickets/booking_screen.dart';
import '../../features/tickets/fare_preview_screen.dart';
import '../../features/tickets/ticket_detail_screen.dart';

class AppRouter {
  AppRouter();

  late final GoRouter router = GoRouter(
    initialLocation: '/home',
    routes: [
      GoRoute(
        path: '/aadhaar-verify',
        builder: (context, state) => const AadhaarVerifyScreen(),
      ),
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) =>
            MainShell(navigationShell: navigationShell),
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/home',
                builder: (context, state) => const HomeBranch(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/tickets',
                builder: (context, state) => const TicketsBranch(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/passes',
                builder: (context, state) => const PassBranch(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/profile',
                builder: (context, state) => const ProfileBranch(),
              ),
            ],
          ),
        ],
      ),
      GoRoute(
        path: '/search-results',
        builder: (context, state) {
          final extra = state.extra as Map<String, String>;
          return SearchResultsScreen(
            fromStop: extra['from']!,
            toStop: extra['to']!,
          );
        },
      ),
      GoRoute(
        path: '/bus/:busId',
        builder: (context, state) {
          final extra = state.extra as Map<String, String?>? ?? {};
          return BusDetailScreen(
            busId: state.pathParameters['busId']!,
            fromStop: extra['from'] ?? '',
            toStop: extra['to'] ?? '',
            routeNumber: extra['routeNumber'],
            routeName: extra['routeName'],
          );
        },
      ),
      GoRoute(
        path: '/fare-preview',
        builder: (context, state) {
          final extra = state.extra as Map<String, String?>? ?? {};
          return FarePreviewScreen(
            busId: extra['busId']!,
            fromStop: extra['from']!,
            toStop: extra['to']!,
            routeNumber: extra['routeNumber'],
            busNumber: extra['busNumber'],
          );
        },
      ),
      GoRoute(
        path: '/booking',
        builder: (context, state) {
          final extra = state.extra as Map<String, dynamic>? ?? {};
          return BookingScreen(
            busId: extra['busId'] as String,
            fromStop: extra['from'] as String,
            toStop: extra['to'] as String,
            adults: extra['adults'] as int? ?? 1,
            children: extra['children'] as int? ?? 0,
            seniors: extra['seniors'] as int? ?? 0,
            busNumber: extra['busNumber'] as String?,
            fare: (extra['fare'] as num?)?.toDouble(),
          );
        },
      ),
      GoRoute(
        path: '/tickets/:ticketId',
        builder: (context, state) => TicketDetailScreen(
          ticketId: state.pathParameters['ticketId']!,
        ),
      ),
      GoRoute(
        path: '/passes/apply',
        builder: (context, state) => const ApplyPassScreen(),
      ),
      GoRoute(
        path: '/passes/status/:passId',
        builder: (context, state) => PassStatusScreen(
          passId: state.pathParameters['passId']!,
        ),
      ),
      GoRoute(
        path: '/passes/active',
        builder: (context, state) => const ActivePassScreen(),
      ),
    ],
  );
}
