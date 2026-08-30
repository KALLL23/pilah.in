import 'package:dio/dio.dart';

class KnowledgeRepository {
  final Dio _dio;
  final String _baseUrl;

  KnowledgeRepository(this._dio, this._baseUrl);

  Options _auth(String token) => Options(
        headers: {'Authorization': 'Bearer $token'},
      );

  Future<Map<String, dynamic>> listKnowledge({
    required String accessToken,
    int limit = 50,
    int offset = 0,
  }) async {
    final response = await _dio.get(
      '$_baseUrl/api/v1/knowledge',
      queryParameters: {'limit': limit, 'offset': offset},
      options: _auth(accessToken),
    );
    return response.data as Map<String, dynamic>;
  }
}
