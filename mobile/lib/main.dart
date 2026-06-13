import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';

import 'core/api/api_client.dart';
import 'core/api/app_api.dart';
import 'core/config.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/auth_cubit.dart';
import 'features/auth/auth_repository.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Preload primary font so first frame is not blocked by a network fetch.
  GoogleFonts.config.allowRuntimeFetching = true;
  await GoogleFonts.pendingFonts([
    GoogleFonts.poppins(fontWeight: FontWeight.w400),
    GoogleFonts.poppins(fontWeight: FontWeight.w600),
  ]);

  runApp(const BusSaathiApp());
}

class BusSaathiApp extends StatefulWidget {
  const BusSaathiApp({super.key});

  @override
  State<BusSaathiApp> createState() => _BusSaathiAppState();
}

class _BusSaathiAppState extends State<BusSaathiApp> {
  late final ApiClient _apiClient;
  late final AuthRepository _authRepository;
  late final AuthCubit _authCubit;
  late final AppRouter _appRouter;

  @override
  void initState() {
    super.initState();
    _apiClient = ApiClient();
    AppApi.configure(_apiClient);
    if (kDebugMode) {
      debugPrint('API base URL: ${AppConfig.apiBaseUrl}');
      final configError = AppConfig.apiHostConfigError();
      if (configError != null) {
        debugPrint('⚠️ API config: $configError');
      }
    }
    _authRepository = AuthRepository(_apiClient);
    _authCubit = AuthCubit(_authRepository);
    _appRouter = AppRouter();

    // Defer network work until after the first frame paints.
    SchedulerBinding.instance.addPostFrameCallback((_) {
      AppApi.stops.initialize();
      _authCubit.initSession();
    });
  }

  @override
  void dispose() {
    AppApi.stops.dispose();
    _authCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider.value(
      value: _authCubit,
      child: MaterialApp.router(
        title: 'Bus Saathi',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        routerConfig: _appRouter.router,
      ),
    );
  }
}
