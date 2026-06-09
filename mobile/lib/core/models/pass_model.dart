import 'package:equatable/equatable.dart';

class PassApplicationModel extends Equatable {
  const PassApplicationModel({
    required this.passId,
    required this.passType,
    required this.status,
    required this.requiredDocuments,
  });

  factory PassApplicationModel.fromJson(Map<String, dynamic> json) {
    return PassApplicationModel(
      passId: json['pass_id'] as String,
      passType: json['pass_type'] as String,
      status: json['status'] as String,
      requiredDocuments: (json['required_documents'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
    );
  }

  final String passId;
  final String passType;
  final String status;
  final List<String> requiredDocuments;

  @override
  List<Object?> get props => [passId];
}

class ActivePassModel extends Equatable {
  const ActivePassModel({
    required this.passId,
    required this.passNumber,
    required this.passType,
    required this.passCategory,
    required this.applicantName,
    required this.applicantMobile,
    this.applicantDob,
    this.routeNumber,
    this.routeName,
    this.fromStop,
    this.toStop,
    required this.validFrom,
    required this.validUntil,
    this.daysRemaining,
    required this.isValid,
    required this.status,
    this.verificationToken,
    this.verificationTokenExpires,
    required this.currentTimestamp,
    required this.verificationBanner,
  });

  factory ActivePassModel.fromJson(Map<String, dynamic> json) {
    return ActivePassModel(
      passId: json['pass_id'] as String,
      passNumber: json['pass_number'] as String,
      passType: json['pass_type'] as String,
      passCategory: json['pass_category'] as String? ?? 'ordinary',
      applicantName: json['applicant_name'] as String,
      applicantMobile: json['applicant_mobile'] as String,
      applicantDob: json['applicant_dob'] as String?,
      routeNumber: json['route_number'] as String?,
      routeName: json['route_name'] as String?,
      fromStop: json['from_stop'] as String?,
      toStop: json['to_stop'] as String?,
      validFrom: json['valid_from'] as String,
      validUntil: json['valid_until'] as String,
      daysRemaining: json['days_remaining'] as int?,
      isValid: json['is_valid'] as bool? ?? false,
      status: json['status'] as String,
      verificationToken: json['verification_token'] as String?,
      verificationTokenExpires: json['verification_token_expires'] as String?,
      currentTimestamp: json['current_timestamp'] as String? ?? '',
      verificationBanner: json['verification_banner'] as String? ??
          'LIVE VERIFIED • HARYANA ROADWAYS',
    );
  }

  final String passId;
  final String passNumber;
  final String passType;
  final String passCategory;
  final String applicantName;
  final String applicantMobile;
  final String? applicantDob;
  final String? routeNumber;
  final String? routeName;
  final String? fromStop;
  final String? toStop;
  final String validFrom;
  final String validUntil;
  final int? daysRemaining;
  final bool isValid;
  final String status;
  final String? verificationToken;
  final String? verificationTokenExpires;
  final String currentTimestamp;
  final String verificationBanner;

  @override
  List<Object?> get props => [passId, verificationToken];
}

class PassStatusModel extends Equatable {
  const PassStatusModel({
    required this.passId,
    this.passNumber,
    required this.passType,
    required this.status,
    this.rejectionReason,
    this.reviewedAt,
    this.validFrom,
    this.validUntil,
    required this.requiredDocuments,
    required this.uploadedDocuments,
  });

  factory PassStatusModel.fromJson(Map<String, dynamic> json) {
    return PassStatusModel(
      passId: json['pass_id'] as String,
      passNumber: json['pass_number'] as String?,
      passType: json['pass_type'] as String,
      status: json['status'] as String,
      rejectionReason: json['rejection_reason'] as String?,
      reviewedAt: json['reviewed_at'] as String?,
      validFrom: json['valid_from'] as String?,
      validUntil: json['valid_until'] as String?,
      requiredDocuments: (json['required_documents'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
      uploadedDocuments: Map<String, bool>.from(
        json['uploaded_documents'] as Map? ?? {},
      ),
    );
  }

  final String passId;
  final String? passNumber;
  final String passType;
  final String status;
  final String? rejectionReason;
  final String? reviewedAt;
  final String? validFrom;
  final String? validUntil;
  final List<String> requiredDocuments;
  final Map<String, bool> uploadedDocuments;

  @override
  List<Object?> get props => [passId, status];
}

class PassListItemModel extends Equatable {
  const PassListItemModel({
    required this.passId,
    this.passNumber,
    required this.passType,
    required this.passCategory,
    required this.status,
    this.validFrom,
    this.validUntil,
    required this.isValid,
    this.daysRemaining,
    required this.createdAt,
  });

  factory PassListItemModel.fromJson(Map<String, dynamic> json) {
    return PassListItemModel(
      passId: json['pass_id'] as String,
      passNumber: json['pass_number'] as String?,
      passType: json['pass_type'] as String,
      passCategory: json['pass_category'] as String? ?? 'ordinary',
      status: json['status'] as String,
      validFrom: json['valid_from'] as String?,
      validUntil: json['valid_until'] as String?,
      isValid: json['is_valid'] as bool? ?? false,
      daysRemaining: json['days_remaining'] as int?,
      createdAt: json['created_at'] as String? ?? '',
    );
  }

  final String passId;
  final String? passNumber;
  final String passType;
  final String passCategory;
  final String status;
  final String? validFrom;
  final String? validUntil;
  final bool isValid;
  final int? daysRemaining;
  final String createdAt;

  @override
  List<Object?> get props => [passId];
}
