import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:go_router/go_router.dart';

final secureStorageProvider = Provider((ref) => const FlutterSecureStorage());
final dioProvider = Provider((ref) => Dio());

class ServerConfigScreen extends ConsumerStatefulWidget {
  const ServerConfigScreen({super.key});

  @override
  ConsumerState<ServerConfigScreen> createState() => _ServerConfigScreenState();
}

class _ServerConfigScreenState extends ConsumerState<ServerConfigScreen> {
  // Input URL yang wajib ditanyakan pada first launch aplikasi[cite: 1]
  final _urlController = TextEditingController(text: "http://192.168.1.10:8000");
  bool _isLoading = false;
  String _statusMessage = "";

  Future<void> _testConnection() async {
    setState(() {
      _isLoading = true;
      _statusMessage = "Menghubungkan...";
    });

    final dio = ref.read(dioProvider);
    final storage = ref.read(secureStorageProvider);
    final serverUrl = _urlController.text.trim();

    try {
      // Memanggil endpoint health check sesuai spesifikasi pilah.in[cite: 1]
      final response = await dio.get('$serverUrl/api/health');
      
      if (response.statusCode == 200) {
        // Menyimpan URL server ke penyimpanan aman lokal[cite: 1]
        await storage.write(key: 'server_url', value: serverUrl);
        
        setState(() {
          _statusMessage = "Koneksi Berhasil!";
          _isLoading = false;
        });
        
        if (mounted) context.go('/login');
      }
    } catch (e) {
      setState(() {
        _statusMessage = "Gagal terhubung. Pastikan backend Docker Anda berjalan.";
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Konfigurasi Peladen pilah.in')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _urlController,
              decoration: const InputDecoration(
                labelText: 'Server URL',
                border: OutlineInputBorder(),
                hintText: 'http://192.168.1.10:8000',
              ),
              keyboardType: TextInputType.url,
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _isLoading ? null : _testConnection,
              // Tombol pengujian koneksi wajib disediakan[cite: 1]
              child: _isLoading 
                  ? const CircularProgressIndicator() 
                  : const Text('Test Connection'),
            ),
            const SizedBox(height: 20),
            Text(
              _statusMessage,
              style: TextStyle(
                color: _statusMessage.contains('Berhasil') ? Colors.green : Colors.red,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}