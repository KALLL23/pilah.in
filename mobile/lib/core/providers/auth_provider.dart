import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../config/app_config.dart';

enum UserRole { user, admin }

class AuthSession {
  const AuthSession({
    this.serverUrl,
    this.accessToken,
    this.refreshToken,
    this.role = UserRole.user,
  });

  final String? serverUrl;
  final String? accessToken;
  final String? refreshToken;
  final UserRole role;

  bool get hasServer => serverUrl != null && serverUrl!.isNotEmpty;

  bool get isAuthenticated =>
      accessToken != null &&
      accessToken!.isNotEmpty &&
      refreshToken != null &&
      refreshToken!.isNotEmpty;
}

final secureStorageProvider = Provider<FlutterSecureStorage>(
  (ref) => const FlutterSecureStorage(),
);

final dioProvider = Provider<Dio>(
  (ref) => Dio(
    BaseOptions(
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 15),
      sendTimeout: const Duration(seconds: 15),
    ),
  ),
);

class AuthSessionNotifier extends AsyncNotifier<AuthSession> {
  AuthSession? _current;

  @override
  Future<AuthSession> build() async {
    final storage = ref.read(secureStorageProvider);
    final session = AuthSession(
      serverUrl: await storage.read(key: 'server_url') ?? AppConfig.defaultServerUrl,
    );
    _current = session;
    return session;
  }

  Future<void> configureServer(String serverUrl) async {
    final storage = ref.read(secureStorageProvider);
    await storage.write(key: 'server_url', value: serverUrl);
    await storage.delete(key: 'access_token');
    await storage.delete(key: 'refresh_token');
    await storage.delete(key: 'user_role');

    final session = AuthSession(serverUrl: serverUrl);
    _current = session;
    state = AsyncData(session);
  }

  Future<void> authenticate(Map<String, dynamic> response) async {
    final accessToken = response['access_token'];
    final refreshToken = response['refresh_token'];
    final user = response['user'];
    final roleValue = user is Map ? user['role'] : null;

    if (accessToken is! String ||
        accessToken.isEmpty ||
        refreshToken is! String ||
        refreshToken.isEmpty ||
        roleValue is! String) {
      throw const FormatException('Respons autentikasi server tidak valid.');
    }

    final current = _current ?? const AuthSession();
    if (!current.hasServer) {
      throw StateError('Server belum dikonfigurasi.');
    }

    final role = roleValue == 'ADMIN' ? UserRole.admin : UserRole.user;
    final storage = ref.read(secureStorageProvider);
    await storage.write(key: 'access_token', value: accessToken);
    await storage.write(key: 'refresh_token', value: refreshToken);
    await storage.write(key: 'user_role', value: roleValue);

    final session = AuthSession(
      serverUrl: current.serverUrl,
      accessToken: accessToken,
      refreshToken: refreshToken,
      role: role,
    );
    _current = session;
    state = AsyncData(session);
  }

  Future<void> clearAuthentication() async {
    final storage = ref.read(secureStorageProvider);
    await storage.delete(key: 'access_token');
    await storage.delete(key: 'refresh_token');
    await storage.delete(key: 'user_role');

    final current = _current ?? const AuthSession();
    final session = AuthSession(serverUrl: current.serverUrl);
    _current = session;
    state = AsyncData(session);
  }
}

final authSessionProvider =
    AsyncNotifierProvider<AuthSessionNotifier, AuthSession>(
      AuthSessionNotifier.new,
    );
