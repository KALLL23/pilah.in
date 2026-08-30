import 'package:dio/dio.dart';

class MapRepository {
  final Dio _dio;
  final String _baseUrl;

  MapRepository(this._dio, this._baseUrl);

  Future<Map<String, dynamic>> getReports({
    required String accessToken,
    bool includeResolved = false,
  }) async {
    final response = await _dio.get(
      '$_baseUrl/api/v1/map/reports',
      queryParameters: {'include_resolved': includeResolved},
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getFacilities({
    required String accessToken,
  }) async {
    final response = await _dio.get(
      '$_baseUrl/api/v1/map/facilities',
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getHotspots({
    required String accessToken,
  }) async {
    final response = await _dio.get(
      '$_baseUrl/api/v1/map/hotspots',
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getWaterways({
    required String accessToken,
  }) async {
    final response = await _dio.get(
      '$_baseUrl/api/v1/map/waterways',
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getPublicFacilities({
    required String accessToken,
  }) async {
    final response = await _dio.get(
      '$_baseUrl/api/v1/map/public-facilities',
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );
    return response.data as Map<String, dynamic>;
  }
}
