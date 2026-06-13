import 'dart:async';

import 'package:shared_preferences/shared_preferences.dart';

import '../api/api_client.dart';
import '../demo_stops.dart';

/// Cached stop names with instant local search and background API refresh.
class StopsService {
  StopsService(this._api);

  final ApiClient _api;

  static const _cacheKey = 'cached_stop_names_v1';

  List<String> _stops = List<String>.from(DemoStops.all);
  bool _initialized = false;
  bool _refreshing = false;
  Timer? _debounce;

  List<String> get cachedStops => List.unmodifiable(_stops);

  /// Load bundled/cache stops immediately; refresh from API in background.
  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;

    try {
      final prefs = await SharedPreferences.getInstance();
      final cached = prefs.getStringList(_cacheKey);
      if (cached != null && cached.isNotEmpty) {
        _stops = List<String>.from(cached)..sort();
      }
    } catch (_) {
      // SharedPreferences unavailable — bundled demo stops remain.
    }

    unawaited(_refreshFromApi());
  }

  Future<void> _refreshFromApi() async {
    if (_refreshing) return;
    _refreshing = true;
    try {
      final response =
          await _api.get<Map<String, dynamic>>('/buses/stops/all');
      final stops = response.data?['stops'] as List<dynamic>? ?? [];
      if (stops.isNotEmpty) {
        _stops = stops.map((e) => e as String).toList()..sort();
        final prefs = await SharedPreferences.getInstance();
        await prefs.setStringList(_cacheKey, _stops);
      }
    } catch (_) {
      // Keep cached / demo stops when offline.
    } finally {
      _refreshing = false;
    }
  }

  /// Instant local filter — used when query is empty or as offline fallback.
  List<String> filterLocal(
    String query, {
    int limit = 12,
    Set<String> exclude = const {},
  }) {
    final q = query.trim().toLowerCase();
    if (q.isEmpty) return [];

    final results = <String>[];
    for (final stop in _stops) {
      if (exclude.contains(stop)) continue;
      if (stop.toLowerCase().contains(q)) {
        results.add(stop);
        if (results.length >= limit) break;
      }
    }
    return results;
  }

  /// Debounced search: tries API first, falls back to local cache.
  Future<List<String>> search(
    String query, {
    int limit = 12,
    Set<String> exclude = const {},
  }) async {
    final q = query.trim();
    if (q.isEmpty) return [];

    try {
      final response = await _api.get<Map<String, dynamic>>(
        '/buses/stops/search',
        queryParameters: {'q': q, 'limit': limit},
      );
      final stops = (response.data?['stops'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .where((s) => !exclude.contains(s))
          .toList();
      if (stops.isNotEmpty) return stops;
    } catch (_) {
      // Offline or older backend — use local cache.
    }

    return filterLocal(q, limit: limit, exclude: exclude);
  }

  void dispose() {
    _debounce?.cancel();
  }
}
