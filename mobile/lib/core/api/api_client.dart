import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../config.dart';

class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConfig.apiBaseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
      ),
    );

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.read(key: AppConfig.accessTokenKey);
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) {
          handler.next(error);
        },
      ),
    );
  }

  final FlutterSecureStorage _storage;
  late final Dio _dio;

  Dio get dio => _dio;

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
    required String userId,
    required bool aadhaarVerified,
  }) async {
    await _storage.write(key: AppConfig.accessTokenKey, value: accessToken);
    await _storage.write(key: AppConfig.refreshTokenKey, value: refreshToken);
    await _storage.write(key: AppConfig.userIdKey, value: userId);
    await _storage.write(
      key: AppConfig.aadhaarVerifiedKey,
      value: aadhaarVerified.toString(),
    );
  }

  Future<void> clearTokens() async {
    await _storage.delete(key: AppConfig.accessTokenKey);
    await _storage.delete(key: AppConfig.refreshTokenKey);
    await _storage.delete(key: AppConfig.userIdKey);
    await _storage.delete(key: AppConfig.aadhaarVerifiedKey);
  }

  Future<String?> getAccessToken() =>
      _storage.read(key: AppConfig.accessTokenKey);

  Future<String?> getRefreshToken() =>
      _storage.read(key: AppConfig.refreshTokenKey);

  Future<String?> getUserId() => _storage.read(key: AppConfig.userIdKey);

  Future<String?> readStorage(String key) => _storage.read(key: key);

  Future<void> writeStorage(String key, String value) =>
      _storage.write(key: key, value: value);

  Future<bool> isLoggedIn() async {
    final token = await getAccessToken();
    return token != null && token.isNotEmpty;
  }

  Future<bool> isAadhaarVerified() async {
    final value = await _storage.read(key: AppConfig.aadhaarVerifiedKey);
    return value == 'true';
  }

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await _dio.get<T>(path,
          queryParameters: queryParameters, options: options);
    } on DioException catch (e) {
      throw ApiException(_extractMessage(e), statusCode: e.response?.statusCode);
    }
  }

  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await _dio.post<T>(path,
          data: data, queryParameters: queryParameters, options: options);
    } on DioException catch (e) {
      throw ApiException(_extractMessage(e), statusCode: e.response?.statusCode);
    }
  }

  Future<Response<T>> postMultipart<T>(
    String path, {
    required FormData data,
  }) async {
    try {
      return await _dio.post<T>(
        path,
        data: data,
        options: Options(contentType: 'multipart/form-data'),
      );
    } on DioException catch (e) {
      throw ApiException(_extractMessage(e), statusCode: e.response?.statusCode);
    }
  }

  String _extractMessage(DioException error) {
    final data = error.response?.data;
    if (data is Map && data['detail'] != null) {
      final detail = data['detail'];
      if (detail is String) return detail;
      if (detail is List && detail.isNotEmpty) {
        return detail.first.toString();
      }
    }
    final server = AppConfig.apiBaseUrl;
    if (error.type == DioExceptionType.connectionError) {
      return 'Unable to connect to $server. '
          'USB: run scripts/dev-mobile.sh. '
          'Wi‑Fi: same network + scripts/forward-api-port.ps1 (WSL2).';
    }
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      return 'Request timed out reaching $server. '
          'USB: run scripts/dev-mobile.sh. '
          'Wi‑Fi: run scripts/forward-api-port.ps1 as Administrator.';
    }
    return error.message ?? 'Something went wrong';
  }
}
