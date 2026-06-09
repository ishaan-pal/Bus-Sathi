import 'package:equatable/equatable.dart';

class FareBreakdownModel extends Equatable {
  const FareBreakdownModel({
    required this.boardingStop,
    required this.destinationStop,
    required this.distanceKm,
    required this.totalFareRupees,
    required this.totalFarePaise,
    required this.breakdown,
  });

  factory FareBreakdownModel.fromJson(Map<String, dynamic> json) {
    return FareBreakdownModel(
      boardingStop: json['boarding_stop'] as String? ?? '',
      destinationStop: json['destination_stop'] as String? ?? '',
      distanceKm: (json['distance_km'] as num?)?.toDouble() ?? 0,
      totalFareRupees: (json['total_fare_rupees'] as num).toDouble(),
      totalFarePaise: json['total_fare_paise'] as int? ?? 0,
      breakdown: Map<String, dynamic>.from(json['breakdown'] as Map? ?? {}),
    );
  }

  final String boardingStop;
  final String destinationStop;
  final double distanceKm;
  final double totalFareRupees;
  final int totalFarePaise;
  final Map<String, dynamic> breakdown;

  @override
  List<Object?> get props => [totalFareRupees];
}

class BookingInitiatedModel extends Equatable {
  const BookingInitiatedModel({
    required this.ticketId,
    required this.ticketNumber,
    required this.fare,
    this.paymentOrder,
    this.razorpayKeyId,
  });

  factory BookingInitiatedModel.fromJson(Map<String, dynamic> json) {
    return BookingInitiatedModel(
      ticketId: json['ticket_id'] as String,
      ticketNumber: json['ticket_number'] as String,
      fare: FareBreakdownModel.fromJson(json['fare'] as Map<String, dynamic>),
      paymentOrder: json['payment_order'] as Map<String, dynamic>?,
      razorpayKeyId: json['razorpay_key_id'] as String?,
    );
  }

  final String ticketId;
  final String ticketNumber;
  final FareBreakdownModel fare;
  final Map<String, dynamic>? paymentOrder;
  final String? razorpayKeyId;

  @override
  List<Object?> get props => [ticketId];
}

class ActiveTicketModel extends Equatable {
  const ActiveTicketModel({
    required this.ticketId,
    required this.ticketNumber,
    required this.busNumber,
    required this.boardingStop,
    required this.destinationStop,
    required this.journeyDate,
    required this.journeyTime,
    required this.adultCount,
    required this.childCount,
    required this.seniorCount,
    required this.totalPassengers,
    required this.totalFareRupees,
    required this.status,
    this.paidAt,
  });

  factory ActiveTicketModel.fromJson(Map<String, dynamic> json) {
    return ActiveTicketModel(
      ticketId: json['ticket_id'] as String,
      ticketNumber: json['ticket_number'] as String,
      busNumber: json['bus_number'] as String,
      boardingStop: json['boarding_stop'] as String,
      destinationStop: json['destination_stop'] as String,
      journeyDate: json['journey_date'] as String,
      journeyTime: json['journey_time'] as String,
      adultCount: json['adult_count'] as int? ?? 0,
      childCount: json['child_count'] as int? ?? 0,
      seniorCount: json['senior_count'] as int? ?? 0,
      totalPassengers: json['total_passengers'] as int? ?? 0,
      totalFareRupees: (json['total_fare_rupees'] as num).toDouble(),
      status: json['status'] as String,
      paidAt: json['paid_at'] as String?,
    );
  }

  final String ticketId;
  final String ticketNumber;
  final String busNumber;
  final String boardingStop;
  final String destinationStop;
  final String journeyDate;
  final String journeyTime;
  final int adultCount;
  final int childCount;
  final int seniorCount;
  final int totalPassengers;
  final double totalFareRupees;
  final String status;
  final String? paidAt;

  @override
  List<Object?> get props => [ticketId];
}

class TicketDetailModel extends Equatable {
  const TicketDetailModel({
    required this.ticketId,
    required this.ticketNumber,
    required this.passengerName,
    required this.passengerMobile,
    required this.busNumber,
    this.routeNumber,
    required this.boardingStop,
    required this.destinationStop,
    required this.journeyDate,
    required this.journeyTime,
    required this.adultCount,
    required this.childCount,
    required this.seniorCount,
    required this.totalPassengers,
    required this.adultFareRupees,
    required this.childFareRupees,
    required this.seniorFareRupees,
    required this.totalFareRupees,
    this.paymentMethod,
    this.paidAt,
    required this.status,
    required this.isValidForTravel,
    this.expiresAt,
    this.verificationToken,
    this.verificationTokenExpires,
    required this.currentTimestamp,
    required this.verificationBanner,
  });

  factory TicketDetailModel.fromJson(Map<String, dynamic> json) {
    return TicketDetailModel(
      ticketId: json['ticket_id'] as String,
      ticketNumber: json['ticket_number'] as String,
      passengerName: json['passenger_name'] as String,
      passengerMobile: json['passenger_mobile'] as String,
      busNumber: json['bus_number'] as String,
      routeNumber: json['route_number'] as String?,
      boardingStop: json['boarding_stop'] as String,
      destinationStop: json['destination_stop'] as String,
      journeyDate: json['journey_date'] as String,
      journeyTime: json['journey_time'] as String,
      adultCount: json['adult_count'] as int? ?? 0,
      childCount: json['child_count'] as int? ?? 0,
      seniorCount: json['senior_count'] as int? ?? 0,
      totalPassengers: json['total_passengers'] as int? ?? 0,
      adultFareRupees: (json['adult_fare_rupees'] as num?)?.toDouble() ?? 0,
      childFareRupees: (json['child_fare_rupees'] as num?)?.toDouble() ?? 0,
      seniorFareRupees: (json['senior_fare_rupees'] as num?)?.toDouble() ?? 0,
      totalFareRupees: (json['total_fare_rupees'] as num).toDouble(),
      paymentMethod: json['payment_method'] as String?,
      paidAt: json['paid_at'] as String?,
      status: json['status'] as String,
      isValidForTravel: json['is_valid_for_travel'] as bool? ?? false,
      expiresAt: json['expires_at'] as String?,
      verificationToken: json['verification_token'] as String?,
      verificationTokenExpires: json['verification_token_expires'] as String?,
      currentTimestamp: json['current_timestamp'] as String? ?? '',
      verificationBanner: json['verification_banner'] as String? ??
          'LIVE VERIFIED • HARYANA ROADWAYS',
    );
  }

  final String ticketId;
  final String ticketNumber;
  final String passengerName;
  final String passengerMobile;
  final String busNumber;
  final String? routeNumber;
  final String boardingStop;
  final String destinationStop;
  final String journeyDate;
  final String journeyTime;
  final int adultCount;
  final int childCount;
  final int seniorCount;
  final int totalPassengers;
  final double adultFareRupees;
  final double childFareRupees;
  final double seniorFareRupees;
  final double totalFareRupees;
  final String? paymentMethod;
  final String? paidAt;
  final String status;
  final bool isValidForTravel;
  final String? expiresAt;
  final String? verificationToken;
  final String? verificationTokenExpires;
  final String currentTimestamp;
  final String verificationBanner;

  @override
  List<Object?> get props => [ticketId, verificationToken];
}
