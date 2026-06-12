import '../../core/api/api_client.dart';
import '../../core/models/bus_model.dart';
import '../../core/models/route_model.dart';

class BusRepository {
  BusRepository(this._api);

  final ApiClient _api;

  Future<List<String>> getAllStops() async {
    try {
      final response = await _api.get<Map<String, dynamic>>('/buses/stops/all');
      final stops = response.data?['stops'] as List<dynamic>? ?? [];
      if (stops.isNotEmpty) {
        return stops.map((e) => e as String).toList();
      }
    } on ApiException catch (e) {
      if (e.statusCode != 404) rethrow;
    }

    // Backward compatible fallback for older API builds.
    final routes = await getAllRoutes();
    final stops = <String>{};
    for (final route in routes) {
      stops.addAll(route.stopNames);
    }
    return stops.toList()..sort();
  }

  Future<List<RouteModel>> getAllRoutes() async {
    final response = await _api.get<List<dynamic>>('/buses/routes/all');
    return (response.data ?? [])
        .map((e) => RouteModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<BusSearchResult>> searchBuses({
    required String boardingStop,
    required String destinationStop,
  }) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/buses/search',
      data: {
        'boarding_stop': boardingStop,
        'destination_stop': destinationStop,
      },
    );
    final buses = response.data?['buses'] as List<dynamic>? ?? [];
    return buses
        .map((e) => BusSearchResult.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<BusDetailModel> getBusDetail(String busId) async {
    final response =
        await _api.get<Map<String, dynamic>>('/buses/$busId');
    return BusDetailModel.fromJson(response.data!);
  }

  Future<BusLocationModel> getBusLocation(String busId) async {
    final response =
        await _api.get<Map<String, dynamic>>('/buses/$busId/location');
    return BusLocationModel.fromJson(response.data!);
  }
}
