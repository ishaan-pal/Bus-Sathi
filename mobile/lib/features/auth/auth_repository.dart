import 'dart:math';

import '../../core/api/api_client.dart';
import '../../core/config.dart';
import '../../core/models/user_model.dart';

class AuthRepository {
  AuthRepository(this._api);

  final ApiClient _api;
  final _random = Random();

  Future<({UserModel user, bool isNewUser})> login(String mobile) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/auth/login',
      data: {'mobile': mobile},
    );
    final data = response.data!;
    final tokens = data['tokens'] as Map<String, dynamic>;
    await _api.saveTokens(
      accessToken: tokens['access_token'] as String,
      refreshToken: tokens['refresh_token'] as String,
      userId: tokens['user_id'] as String,
      aadhaarVerified: tokens['aadhaar_verified'] as bool? ?? false,
    );
    return (
      user: UserModel.fromJson(data['user'] as Map<String, dynamic>),
      isNewUser: data['is_new_user'] as bool? ?? false,
    );
  }

  Future<UserModel?> ensureGuestSession() async {
    if (await _api.isLoggedIn()) {
      try {
        return await getMe();
      } catch (_) {
        await logout();
      }
    }

    final mobile = await _getOrCreateGuestMobile();
    final result = await login(mobile);
    return result.user;
  }

  Future<String> _getOrCreateGuestMobile() async {
    final stored = await _api.readStorage(AppConfig.guestMobileKey);
    if (stored != null && RegExp(r'^[6-9]\d{9}$').hasMatch(stored)) {
      return stored;
    }

    final mobile = '9${_random.nextInt(900000000) + 100000000}';
    await _api.writeStorage(AppConfig.guestMobileKey, mobile);
    return mobile;
  }

  Future<UserModel> verifyAadhaar(String aadhaarNumber) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/auth/verify-aadhaar',
      data: {'aadhaar_number': aadhaarNumber},
    );
    final user = UserModel.fromJson(response.data!['user'] as Map<String, dynamic>);
    await _api.saveTokens(
      accessToken: (await _api.getAccessToken()) ?? '',
      refreshToken: (await _api.getRefreshToken()) ?? '',
      userId: user.id,
      aadhaarVerified: user.aadhaarVerified,
    );
    return user;
  }

  Future<UserModel> getMe() async {
    final response = await _api.get<Map<String, dynamic>>('/auth/me');
    final user = UserModel.fromJson(response.data!);
    await _api.saveTokens(
      accessToken: (await _api.getAccessToken()) ?? '',
      refreshToken: (await _api.getRefreshToken()) ?? '',
      userId: user.id,
      aadhaarVerified: user.aadhaarVerified,
    );
    return user;
  }

  Future<void> logout() => _api.clearTokens();

  Future<bool> isLoggedIn() => _api.isLoggedIn();
}
