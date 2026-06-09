import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'core/api/api_client.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/auth_cubit.dart';
import 'features/auth/auth_repository.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const HaryanaRoadwaysApp());
}

class HaryanaRoadwaysApp extends StatefulWidget {
  const HaryanaRoadwaysApp({super.key});

  @override
  State<HaryanaRoadwaysApp> createState() => _HaryanaRoadwaysAppState();
}

class _HaryanaRoadwaysAppState extends State<HaryanaRoadwaysApp> {
  late final ApiClient _apiClient;
  late final AuthRepository _authRepository;
  late final AuthCubit _authCubit;
  late final AppRouter _appRouter;

  @override
  void initState() {
    super.initState();
    _apiClient = ApiClient();
    _authRepository = AuthRepository(_apiClient);
    _authCubit = AuthCubit(_authRepository)..checkAuthStatus();
    _appRouter = AppRouter(_authCubit);
  }

  @override
  void dispose() {
    _authCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider.value(
      value: _authCubit,
      child: MaterialApp.router(
        title: 'Haryana Roadways',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        routerConfig: _appRouter.router,
      ),
    );
  }
}
