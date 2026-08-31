import 'package:dio/dio.dart';

class AdminRepository {
  final Dio _dio;
  final String _baseUrl;

  AdminRepository(this._dio, this._baseUrl);

  Options _auth(String token) => Options(
        headers: {'Authorization': 'Bearer $token'},
      );

  // ── Reports ──

  Future<Map<String, dynamic>> listReports({
    required String accessToken,
    String? status,
    int limit = 50,
    int offset = 0,
  }) async {
    final params = <String, dynamic>{'limit': limit, 'offset': offset};
    if (status != null) params['status'] = status;
    final response = await _dio.get(
      '$_baseUrl/api/v1/admin/reports',
      queryParameters: params,
      options: _auth(accessToken),
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getReport({
    required String reportId,
    required String accessToken,
  }) async {
    final response = await _dio.get(
      '$_baseUrl/api/v1/admin/reports/$reportId',
      options: _auth(accessToken),
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> changeReportStatus({
    required String reportId,
    required String status,
    required String accessToken,
  }) async {
    final response = await _dio.patch(
      '$_baseUrl/api/v1/admin/reports/$reportId/status',
      data: {'status': status},
      options: _auth(accessToken),
    );
    return response.data as Map<String, dynamic>;
  }

  // ── Facilities ──

  Future<Map<String, dynamic>> listFacilities({
    required String accessToken,
    int limit = 50,
    int offset = 0,
  }) async {
    final response = await _dio.get(
      '$_baseUrl/api/v1/admin/facilities',
      queryParameters: {'limit': limit, 'offset': offset},
      options: _auth(accessToken),
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createFacility({
    required String accessToken,
    required Map<String, dynamic> data,
  }) async {
    final response = await _dio.post(
      '$_baseUrl/api/v1/admin/facilities',
      data: data,
      options: _auth(accessToken),
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateFacility({
    required String facilityId,
    required String accessToken,
    required Map<String, dynamic> data,
  }) async {
    final response = await _dio.patch(
      '$_baseUrl/api/v1/admin/facilities/$facilityId',
      data: data,
      options: _auth(accessToken),
    );
    return response.data as Map<String, dynamic>;
  }

  Future<void> deleteFacility({
    required String facilityId,
    required String accessToken,
  }) async {
    await _dio.delete(
      '$_baseUrl/api/v1/admin/facilities/$facilityId',
      options: _auth(accessToken),
    );
  }

  // ── Knowledge ──

  Future<Map<String, dynamic>> listKnowledge({
    required String accessToken,
    int limit = 50,
    int offset = 0,
  }) async {
    final response = await _dio.get(
      '$_baseUrl/api/v1/admin/knowledge',
      queryParameters: {'limit': limit, 'offset': offset},
      options: _auth(accessToken),
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createKnowledge({
    required String accessToken,
    required Map<String, dynamic> data,
  }) async {
    final response = await _dio.post(
      '$_baseUrl/api/v1/admin/knowledge',
      data: data,
      options: _auth(accessToken),
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateKnowledge({
    required String knowledgeId,
    required String accessToken,
    required Map<String, dynamic> data,
  }) async {
    final response = await _dio.patch(
      '$_baseUrl/api/v1/admin/knowledge/$knowledgeId',
      data: data,
      options: _auth(accessToken),
    );
    return response.data as Map<String, dynamic>;
  }

  Future<void> deleteKnowledge({
    required String knowledgeId,
    required String accessToken,
  }) async {
    await _dio.delete(
      '$_baseUrl/api/v1/admin/knowledge/$knowledgeId',
      options: _auth(accessToken),
    );
  }

  // ── Hotspot ──

  Future<Map<String, dynamic>> listHotspots({
    required String accessToken,
  }) async {
    final response = await _dio.get(
      '$_baseUrl/api/v1/map/hotspots',
      options: _auth(accessToken),
    );
    return response.data as Map<String, dynamic>;
  }
}
