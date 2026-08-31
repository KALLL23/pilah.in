import 'package:dio/dio.dart';

class ReportRepository {
  final Dio _dio;
  final String _baseUrl;

  ReportRepository(this._dio, this._baseUrl);

  Future<Map<String, dynamic>> detectImage({
    required String imagePath,
    required String accessToken,
  }) async {
    final formData = FormData.fromMap({
      'image': await MultipartFile.fromFile(imagePath),
    });

    final response = await _dio.post(
      '$_baseUrl/api/v1/detect',
      data: formData,
      options: Options(
        headers: {'Authorization': 'Bearer $accessToken'},
      ),
    );

    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createReport({
    required String imagePath,
    required double latitude,
    required double longitude,
    double? locationAccuracyM,
    String? userDescription,
    String? wasteVolume,
    bool? standingWater,
    bool? drainageBlockage,
    required String accessToken,
  }) async {
    final formData = FormData.fromMap({
      'image': await MultipartFile.fromFile(imagePath),
      'latitude': latitude,
      'longitude': longitude,
      if (locationAccuracyM != null) 'location_accuracy_m': locationAccuracyM,
      if (userDescription != null && userDescription.isNotEmpty)
        'user_description': userDescription,
      if (wasteVolume != null) 'waste_volume': wasteVolume,
      if (standingWater != null) 'standing_water': standingWater,
      if (drainageBlockage != null) 'drainage_blockage': drainageBlockage,
    });

    final response = await _dio.post(
      '$_baseUrl/api/v1/reports',
      data: formData,
      options: Options(
        headers: {'Authorization': 'Bearer $accessToken'},
      ),
    );

    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getReport({
    required String reportId,
    required String accessToken,
  }) async {
    final response = await _dio.get(
      '$_baseUrl/api/v1/reports/$reportId',
      options: Options(
        headers: {'Authorization': 'Bearer $accessToken'},
      ),
    );

    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> listReports({
    required String accessToken,
    int limit = 20,
    int offset = 0,
  }) async {
    final response = await _dio.get(
      '$_baseUrl/api/v1/reports',
      queryParameters: {'limit': limit, 'offset': offset},
      options: Options(
        headers: {'Authorization': 'Bearer $accessToken'},
      ),
    );

    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> confirmReport({
    required String reportId,
    required String accessToken,
  }) async {
    final response = await _dio.post(
      '$_baseUrl/api/v1/reports/$reportId/confirm',
      options: Options(
        headers: {'Authorization': 'Bearer $accessToken'},
      ),
    );

    return response.data as Map<String, dynamic>;
  }
}
