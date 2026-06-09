import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/models/pass_model.dart';

class PassRepository {
  PassRepository(this._api);

  final ApiClient _api;

  Future<PassApplicationModel> applyForPass({
    required String passType,
    required String applicantName,
    required String applicantDob,
    String passCategory = 'ordinary',
    String? routeId,
    String? fromStop,
    String? toStop,
    String? institutionName,
    String? institutionAddress,
    String? studentIdNumber,
  }) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/passes/apply',
      data: {
        'pass_type': passType,
        'pass_category': passCategory,
        'applicant_name': applicantName,
        'applicant_dob': applicantDob,
        if (routeId != null) 'route_id': routeId,
        if (fromStop != null) 'from_stop': fromStop,
        if (toStop != null) 'to_stop': toStop,
        if (institutionName != null) 'institution_name': institutionName,
        if (institutionAddress != null)
          'institution_address': institutionAddress,
        if (studentIdNumber != null) 'student_id_number': studentIdNumber,
      },
    );
    return PassApplicationModel.fromJson(response.data!);
  }

  Future<void> uploadDocument({
    required String passId,
    required String docType,
    required String filePath,
    required String fileName,
  }) async {
    final formData = FormData.fromMap({
      'doc_type': docType,
      'file': await MultipartFile.fromFile(filePath, filename: fileName),
    });
    await _api.postMultipart('/passes/$passId/upload', data: formData);
  }

  Future<ActivePassModel> getActivePass() async {
    final response = await _api.get<Map<String, dynamic>>('/passes/active');
    return ActivePassModel.fromJson(response.data!);
  }

  Future<List<PassListItemModel>> getPassHistory() async {
    final response = await _api.get<Map<String, dynamic>>('/passes/history');
    final passes = response.data?['passes'] as List<dynamic>? ?? [];
    return passes
        .map((e) => PassListItemModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<PassStatusModel> getPassStatus(String passId) async {
    final response =
        await _api.get<Map<String, dynamic>>('/passes/$passId/status');
    return PassStatusModel.fromJson(response.data!);
  }
}
