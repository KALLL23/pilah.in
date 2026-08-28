import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthRepository {
  final Dio _dio;
  final FlutterSecureStorage _storage;

  AuthRepository(this._dio, this._storage);

  Future<Map<String, dynamic>> login(String email, String password) async {
    final baseUrl = await _storage.read(key: 'server_url');
    
    try {
      final response = await _dio.post(
        '$baseUrl/api/v1/auth/login',
        data: {'email': email, 'password': password},
      );

      if (response.statusCode == 200) {
        final data = response.data;
        await _storage.write(key: 'access_token', value: data['access_token']);
        await _storage.write(key: 'refresh_token', value: data['refresh_token']);
        return data;
      }
      throw Exception('Gagal login');
    } catch (e) {
      throw Exception('Email atau sandi salah. Pastikan akun sudah terdaftar.');
    }
  }

  Future<bool> register(String name, String email, String password) async {
    final baseUrl = await _storage.read(key: 'server_url');
    
    try {
      final response = await _dio.post(
        '$baseUrl/api/v1/auth/register', 
        data: {'name': name, 'email': email, 'password': password},
      );
      
      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      throw Exception('Pendaftaran gagal. Email mungkin sudah terdaftar atau terjadi kesalahan server.');
    }
  }
}