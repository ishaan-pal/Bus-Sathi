import 'api_client.dart';

/// Shared [ApiClient] for the whole app. Configured once in [main.dart].
class AppApi {
  AppApi._();

  static ApiClient? _client;

  static ApiClient get client {
    final existing = _client;
    if (existing == null) {
      throw StateError('AppApi.client used before AppApi.configure() in main.dart');
    }
    return existing;
  }

  static void configure(ApiClient client) {
    _client = client;
  }
}
