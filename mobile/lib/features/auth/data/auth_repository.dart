import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../../core/config/app_config.dart';
import '../../../core/providers/auth_provider.dart';

class AuthException implements Exception {
  const AuthException(this.message);

  final String message;

  @override
  String toString() => message;
}

class AuthRepository {
  final Dio _dio;
  final FlutterSecureStorage _storage;

  AuthRepository(this._dio, this._storage);

  Future<Map<String, dynamic>> login(String email, String password) async {
    final baseUrl = await _serverUrl();

    try {
      final response = await _dio.post(
        '$baseUrl/api/v1/auth/login',
        data: {'email': email, 'password': password},
      );
      return _responseMap(response.data);
    } on DioException catch (error) {
      throw AuthException(
        _messageFrom(error, 'Email atau sandi salah.'),
      );
    }
  }

  Future<Map<String, dynamic>> register(
    String name,
    String email,
    String password,
  ) async {
    final baseUrl = await _serverUrl();

    try {
      final response = await _dio.post(
        '$baseUrl/api/v1/auth/register',
        data: {'name': name, 'email': email, 'password': password},
      );
      return _responseMap(response.data);
    } on DioException catch (error) {
      throw AuthException(
        _messageFrom(error, 'Pendaftaran gagal. Silakan coba kembali.'),
      );
    }
  }

  Future<String> _serverUrl() async {
    final value = await _storage.read(key: 'server_url');
    if (value == null || value.isEmpty) {
      return AppConfig.defaultServerUrl;
    }
    return value;
  }

  Map<String, dynamic> _responseMap(dynamic data) {
    if (data is Map<String, dynamic>) {
      return data;
    }
    if (data is Map) {
      return Map<String, dynamic>.from(data);
    }
    throw const AuthException('Respons autentikasi server tidak valid.');
  }

  String _messageFrom(DioException error, String fallback) {
    final data = error.response?.data;
    if (data is Map) {
      final apiError = data['error'];
      if (apiError is Map && apiError['message'] is String) {
        return apiError['message'] as String;
      }
      if (data['detail'] is String) {
        return data['detail'] as String;
      }
    }
    if (error.type == DioExceptionType.connectionError ||
        error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout) {
      return 'Server tidak dapat dihubungi.';
    }
    return fallback;
  }
}

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(
    ref.watch(dioProvider),
    ref.watch(secureStorageProvider),
  );
});
