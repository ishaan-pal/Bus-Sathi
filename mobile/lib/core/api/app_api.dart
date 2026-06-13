import 'api_client.dart';
import '../services/stops_service.dart';

/// Shared app-wide services. Configured once in [main.dart].
class AppApi {
  AppApi._();

  static ApiClient? _client;
  static StopsService? _stops;

  static ApiClient get client {
    final existing = _client;
    if (existing == null) {
      throw StateError('AppApi.client used before AppApi.configure() in main.dart');
    }
    return existing;
  }

  static StopsService get stops {
    final existing = _stops;
    if (existing == null) {
      throw StateError('AppApi.stops used before AppApi.configure() in main.dart');
    }
    return existing;
  }

  static void configure(ApiClient client) {
    _client = client;
    _stops = StopsService(client);
  }
}
