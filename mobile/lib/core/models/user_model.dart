import 'package:equatable/equatable.dart';

class UserModel extends Equatable {
  const UserModel({
    required this.id,
    required this.mobile,
    this.name,
    this.dateOfBirth,
    this.aadhaarVerified = false,
    this.profileComplete = false,
    this.isAdmin = false,
    this.isStaff = false,
    this.age,
    this.isSeniorCitizen = false,
    this.isChild = false,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String,
      mobile: json['mobile'] as String,
      name: json['name'] as String?,
      dateOfBirth: json['date_of_birth'] as String?,
      aadhaarVerified: json['aadhaar_verified'] as bool? ?? false,
      profileComplete: json['profile_complete'] as bool? ?? false,
      isAdmin: json['is_admin'] as bool? ?? false,
      isStaff: json['is_staff'] as bool? ?? false,
      age: json['age'] as int?,
      isSeniorCitizen: json['is_senior_citizen'] as bool? ?? false,
      isChild: json['is_child'] as bool? ?? false,
    );
  }

  final String id;
  final String mobile;
  final String? name;
  final String? dateOfBirth;
  final bool aadhaarVerified;
  final bool profileComplete;
  final bool isAdmin;
  final bool isStaff;
  final int? age;
  final bool isSeniorCitizen;
  final bool isChild;

  @override
  List<Object?> get props => [id, mobile, name, profileComplete];
}
