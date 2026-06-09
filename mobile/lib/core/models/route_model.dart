import 'package:equatable/equatable.dart';

class RouteStopModel extends Equatable {
  const RouteStopModel({
    required this.stopName,
    required this.stopOrder,
    required this.distanceFromOriginKm,
    this.latitude,
    this.longitude,
    required this.scheduledMinutesFromOrigin,
    required this.isMajorStop,
  });

  factory RouteStopModel.fromJson(Map<String, dynamic> json) {
    return RouteStopModel(
      stopName: json['stop_name'] as String,
      stopOrder: json['stop_order'] as int,
      distanceFromOriginKm: (json['distance_from_origin_km'] as num).toDouble(),
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      scheduledMinutesFromOrigin: json['scheduled_minutes_from_origin'] as int,
      isMajorStop: json['is_major_stop'] as bool? ?? false,
    );
  }

  final String stopName;
  final int stopOrder;
  final double distanceFromOriginKm;
  final double? latitude;
  final double? longitude;
  final int scheduledMinutesFromOrigin;
  final bool isMajorStop;

  @override
  List<Object?> get props => [stopName, stopOrder];
}

class RouteModel extends Equatable {
  const RouteModel({
    required this.id,
    required this.routeNumber,
    required this.name,
    required this.origin,
    required this.destination,
    required this.totalDistanceKm,
    required this.estimatedDurationMinutes,
    required this.isActive,
    required this.stops,
  });

  factory RouteModel.fromJson(Map<String, dynamic> json) {
    return RouteModel(
      id: json['id'] as String,
      routeNumber: json['route_number'] as String,
      name: json['name'] as String,
      origin: json['origin'] as String,
      destination: json['destination'] as String,
      totalDistanceKm: (json['total_distance_km'] as num).toDouble(),
      estimatedDurationMinutes: json['estimated_duration_minutes'] as int,
      isActive: json['is_active'] as bool? ?? true,
      stops: (json['stops'] as List<dynamic>? ?? [])
          .map((e) => RouteStopModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  final String id;
  final String routeNumber;
  final String name;
  final String origin;
  final String destination;
  final double totalDistanceKm;
  final int estimatedDurationMinutes;
  final bool isActive;
  final List<RouteStopModel> stops;

  List<String> get stopNames => stops.map((s) => s.stopName).toList();

  @override
  List<Object?> get props => [id, routeNumber];
}
