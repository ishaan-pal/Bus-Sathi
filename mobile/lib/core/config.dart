import 'dart:io';

import 'package:flutter/foundation.dart';

class AppConfig {
  AppConfig._();

  /// Override API host at build/run time:
  /// - USB device: run `./scripts/dev-mobile.sh` (uses 127.0.0.1 + adb reverse)
  /// - Wi‑Fi device: API_HOST=192.168.x.x + scripts/forward-api-port.ps1 on WSL2
  /// - Emulator: omit API_HOST (uses 10.0.2.2)
  static String get apiHost {
    const host = String.fromEnvironment('API_HOST');
    if (host.isNotEmpty) return host;
    // Physical Android over USB: run `adb reverse tcp:8000 tcp:8000` first.
    // Android emulator: flutter run --dart-define=API_HOST=10.0.2.2
    if (!kIsWeb && Platform.isAndroid) return '127.0.0.1';
    return 'localhost';
  }

  static String get apiBaseUrl => 'http://$apiHost:8000/api/v1';

  static String get healthUrl => 'http://$apiHost:8000/health';

  /// Guidance shown when the phone cannot reach the dev backend.
  static String get connectionHelp {
    const host = String.fromEnvironment('API_HOST');
    if (host == '127.0.0.1' || host.isEmpty) {
      return 'USB fix: run ./scripts/dev-mobile.sh from the project root '
          '(sets up adb reverse and launches the app).';
    }
    return 'Wi‑Fi fix (WSL2): on Windows PowerShell as Administrator run '
        'scripts/forward-api-port.ps1, then use the LAN IP it prints.\n'
        'USB fix: run ./scripts/dev-mobile.sh instead of a Wi‑Fi IP.';
  }

  /// Returns a user-facing message when [API_HOST] looks wrong, else null.
  static String? apiHostConfigError() {
    const host = String.fromEnvironment('API_HOST');
    if (host.isEmpty) return null;

    if (host.endsWith('2484')) {
      return 'API_HOST looks wrong: "$host". '
          'Use 192.168.29.248 (not 2484), or run ./scripts/dev-mobile.sh over USB.';
    }

    final ipv4 = RegExp(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$');
    final match = ipv4.firstMatch(host);
    if (match != null) {
      for (var i = 1; i <= 4; i++) {
        final octet = int.parse(match.group(i)!);
        if (octet > 255) {
          return 'Invalid API_HOST "$host": IP numbers must be 0–255. '
              'Try 192.168.29.248 or ./scripts/dev-mobile.sh';
        }
      }
    }

    return null;
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
