import 'package:equatable/equatable.dart';

class BusLocationModel extends Equatable {
  const BusLocationModel({
    required this.busId,
    required this.busNumber,
    required this.latitude,
    required this.longitude,
    this.speedKmh,
    this.heading,
    required this.status,
    required this.delayMinutes,
    this.currentStop,
    this.nextStop,
    this.lastUpdated,
    required this.isStale,
  });

  factory BusLocationModel.fromJson(Map<String, dynamic> json) {
    return BusLocationModel(
      busId: json['bus_id'] as String,
      busNumber: json['bus_number'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      speedKmh: (json['speed_kmh'] as num?)?.toDouble(),
      heading: (json['heading'] as num?)?.toDouble(),
      status: json['status'] as String,
      delayMinutes: json['delay_minutes'] as int? ?? 0,
      currentStop: json['current_stop'] as String?,
      nextStop: json['next_stop'] as String?,
      lastUpdated: json['last_updated'] as String?,
      isStale: json['is_stale'] as bool? ?? false,
    );
  }

  final String busId;
  final String busNumber;
  final double latitude;
  final double longitude;
  final double? speedKmh;
  final double? heading;
  final String status;
  final int delayMinutes;
  final String? currentStop;
  final String? nextStop;
  final String? lastUpdated;
  final bool isStale;

  @override
  List<Object?> get props => [busId, latitude, longitude];
}

class FareInfoModel extends Equatable {
  const FareInfoModel({this.adultFareRupees, this.distanceKm});

  factory FareInfoModel.fromJson(Map<String, dynamic> json) {
    return FareInfoModel(
      adultFareRupees: (json['adult_fare_rupees'] as num?)?.toDouble(),
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
    );
  }

  final double? adultFareRupees;
  final double? distanceKm;

  @override
  List<Object?> get props => [adultFareRupees, distanceKm];
}

class BusSearchResult extends Equatable {
  const BusSearchResult({
    required this.busId,
    required this.busNumber,
    required this.busType,
    required this.status,
    required this.delayMinutes,
    required this.etaDisplay,
    this.currentStop,
    this.nextStop,
    required this.routeNumber,
    required this.routeName,
    required this.boardingStop,
    required this.destinationStop,
    required this.fareInfo,
    this.location,
    this.conductorName,
    this.conductorMobile,
    required this.seatingCapacity,
    required this.standingCapacity,
  });

  factory BusSearchResult.fromJson(Map<String, dynamic> json) {
    return BusSearchResult(
      busId: json['bus_id'] as String,
      busNumber: json['bus_number'] as String,
      busType: json['bus_type'] as String,
      status: json['status'] as String,
      delayMinutes: json['delay_minutes'] as int? ?? 0,
      etaDisplay: json['eta_display'] as String? ?? '',
      currentStop: json['current_stop'] as String?,
      nextStop: json['next_stop'] as String?,
      routeNumber: json['route_number'] as String,
      routeName: json['route_name'] as String,
      boardingStop: json['boarding_stop'] as String,
      destinationStop: json['destination_stop'] as String,
      fareInfo: FareInfoModel.fromJson(
        json['fare_info'] as Map<String, dynamic>? ?? {},
      ),
      location: json['location'] != null
          ? BusLocationModel.fromJson(json['location'] as Map<String, dynamic>)
          : null,
      conductorName: json['conductor_name'] as String?,
      conductorMobile: json['conductor_mobile'] as String?,
      seatingCapacity: json['seating_capacity'] as int? ?? 0,
      standingCapacity: json['standing_capacity'] as int? ?? 0,
    );
  }

  final String busId;
  final String busNumber;
  final String busType;
  final String status;
  final int delayMinutes;
  final String etaDisplay;
  final String? currentStop;
  final String? nextStop;
  final String routeNumber;
  final String routeName;
  final String boardingStop;
  final String destinationStop;
  final FareInfoModel fareInfo;
  final BusLocationModel? location;
  final String? conductorName;
  final String? conductorMobile;
  final int seatingCapacity;
  final int standingCapacity;

  @override
  List<Object?> get props => [busId, busNumber];
}

class BusDetailModel extends Equatable {
  const BusDetailModel({
    required this.busId,
    required this.busNumber,
    required this.registrationNumber,
    required this.busType,
    required this.status,
    required this.delayMinutes,
    required this.etaDisplay,
    this.currentStop,
    this.nextStop,
    required this.distanceCoveredKm,
    this.driverName,
    this.conductorName,
    this.conductorMobile,
    required this.seatingCapacity,
    required this.standingCapacity,
    required this.trackingSource,
    this.routeNumber,
    this.routeName,
    this.location,
    required this.isLocationStale,
  });

  factory BusDetailModel.fromJson(Map<String, dynamic> json) {
    return BusDetailModel(
      busId: json['bus_id'] as String,
      busNumber: json['bus_number'] as String,
      registrationNumber: json['registration_number'] as String? ?? '',
      busType: json['bus_type'] as String,
      status: json['status'] as String,
      delayMinutes: json['delay_minutes'] as int? ?? 0,
      etaDisplay: json['eta_display'] as String? ?? '',
      currentStop: json['current_stop'] as String?,
      nextStop: json['next_stop'] as String?,
      distanceCoveredKm: (json['distance_covered_km'] as num?)?.toDouble() ?? 0,
      driverName: json['driver_name'] as String?,
      conductorName: json['conductor_name'] as String?,
      conductorMobile: json['conductor_mobile'] as String?,
      seatingCapacity: json['seating_capacity'] as int? ?? 0,
      standingCapacity: json['standing_capacity'] as int? ?? 0,
      trackingSource: json['tracking_source'] as String? ?? '',
      routeNumber: json['route_number'] as String?,
      routeName: json['route_name'] as String?,
      location: json['location'] != null
          ? BusLocationModel.fromJson(json['location'] as Map<String, dynamic>)
          : null,
      isLocationStale: json['is_location_stale'] as bool? ?? false,
    );
  }

  final String busId;
  final String busNumber;
  final String registrationNumber;
  final String busType;
  final String status;
  final int delayMinutes;
  final String etaDisplay;
  final String? currentStop;
  final String? nextStop;
  final double distanceCoveredKm;
  final String? driverName;
  final String? conductorName;
  final String? conductorMobile;
  final int seatingCapacity;
  final int standingCapacity;
  final String trackingSource;
  final String? routeNumber;
  final String? routeName;
  final BusLocationModel? location;
  final bool isLocationStale;

  @override
  List<Object?> get props => [busId];
}
