import 'dart:io';

import 'package:flutter/foundation.dart';

class AppConfig {
  AppConfig._();

  /// Override API host at build/run time:
  /// - USB device: `adb reverse tcp:8000 tcp:8000` then API_HOST=127.0.0.1
  /// - Wi‑Fi device: API_HOST=<PC LAN IP> + scripts/forward-api-port.ps1 on WSL2
  /// - Emulator: omit API_HOST (uses 10.0.2.2)
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

  static const String adminMobile = '9999999999';

  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userIdKey = 'user_id';
  static const String aadhaarVerifiedKey = 'aadhaar_verified';
  static const String guestMobileKey = 'guest_mobile';

  static const Duration locationPollInterval = Duration(seconds: 15);
  static const Duration tokenRefreshInterval = Duration(seconds: 50);
}
