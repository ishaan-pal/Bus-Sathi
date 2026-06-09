import 'dart:io';

import 'package:flutter/foundation.dart';

class AppConfig {
  AppConfig._();

  /// Override at run time: flutter run --dart-define=API_HOST=192.168.1.5
  /// - Android emulator: default 10.0.2.2 (maps to your PC's localhost)
  /// - Physical Android phone: your PC's Wi‑Fi IP (same network as phone)
  /// - Linux/desktop: localhost
  static String get apiBaseUrl {
    const host = String.fromEnvironment('API_HOST');
    if (host.isNotEmpty) {
      return 'http://$host:8000/api/v1';
    }
    if (!kIsWeb && Platform.isAndroid) {
      return 'http://10.0.2.2:8000/api/v1';
    }
    return 'http://localhost:8000/api/v1';
  }
  static const String devOtp = '123456';
  static const String adminMobile = '9999999999';

  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userIdKey = 'user_id';
  static const String profileCompleteKey = 'profile_complete';

  static const Duration locationPollInterval = Duration(seconds: 15);
  static const Duration tokenRefreshInterval = Duration(seconds: 50);
}
