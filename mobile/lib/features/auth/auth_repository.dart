import '../../core/api/api_client.dart';
import '../../core/models/user_model.dart';

class AuthRepository {
  AuthRepository(this._api);

  final ApiClient _api;

  Future<String> sendOtp(String mobile) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/auth/send-otp',
      data: {'mobile': mobile},
    );
    return response.data?['message'] as String? ?? 'OTP sent';
  }

  Future<({UserModel user, bool isNewUser})> verifyOtp(
    String mobile,
    String otp,
  ) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/auth/verify-otp',
      data: {'mobile': mobile, 'otp': otp},
    );
    final data = response.data!;
    final tokens = data['tokens'] as Map<String, dynamic>;
    await _api.saveTokens(
      accessToken: tokens['access_token'] as String,
      refreshToken: tokens['refresh_token'] as String,
      userId: tokens['user_id'] as String,
      profileComplete: tokens['profile_complete'] as bool? ?? false,
    );
    return (
      user: UserModel.fromJson(data['user'] as Map<String, dynamic>),
      isNewUser: data['is_new_user'] as bool? ?? false,
    );
  }

  Future<UserModel> completeProfile({
    required String name,
    required String dateOfBirth,
  }) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/auth/complete-profile',
      data: {'name': name, 'date_of_birth': dateOfBirth},
    );
    final user = UserModel.fromJson(
      response.data!['user'] as Map<String, dynamic>,
    );
    await _api.saveTokens(
      accessToken: (await _api.getAccessToken()) ?? '',
      refreshToken: (await _api.getRefreshToken()) ?? '',
      userId: user.id,
      profileComplete: user.profileComplete,
    );
    return user;
  }

  Future<UserModel> verifyAadhaar(String aadhaarNumber) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/auth/verify-aadhaar',
      data: {'aadhaar_number': aadhaarNumber},
    );
    return UserModel.fromJson(response.data!['user'] as Map<String, dynamic>);
  }

  Future<UserModel> getMe() async {
    final response = await _api.get<Map<String, dynamic>>('/auth/me');
    return UserModel.fromJson(response.data!);
  }

  Future<void> logout() => _api.clearTokens();

  Future<bool> isLoggedIn() => _api.isLoggedIn();

  Future<bool> isProfileComplete() => _api.isProfileComplete();
}
