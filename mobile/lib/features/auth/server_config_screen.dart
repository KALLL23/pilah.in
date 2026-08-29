import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/providers/auth_provider.dart';

class ServerConfigScreen extends ConsumerStatefulWidget {
  const ServerConfigScreen({super.key});

  @override
  ConsumerState<ServerConfigScreen> createState() => _ServerConfigScreenState();
}

class _ServerConfigScreenState extends ConsumerState<ServerConfigScreen> {
  final _urlController = TextEditingController(
    text: 'http://192.168.1.10:8000',
  );
  bool _isLoading = false;
  String _statusMessage = '';

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  String? _normalizeServerUrl(String value) {
    final normalized = value.trim().replaceFirst(RegExp(r'/+$'), '');
    final uri = Uri.tryParse(normalized);
    if (uri == null ||
        !{'http', 'https'}.contains(uri.scheme) ||
        uri.host.isEmpty) {
      return null;
    }
    return normalized;
  }

  Future<void> _testConnection() async {
    setState(() {
      _isLoading = true;
      _statusMessage = 'Menghubungkan...';
    });

    final dio = ref.read(dioProvider);
    final serverUrl = _normalizeServerUrl(_urlController.text);
    if (serverUrl == null) {
      setState(() {
        _isLoading = false;
        _statusMessage = 'Masukkan URL server HTTP/HTTPS yang valid.';
      });
      return;
    }

    try {
      final response = await dio.get('$serverUrl/health');

      if (response.statusCode == 200) {
        await ref
            .read(authSessionProvider.notifier)
            .configureServer(serverUrl);
        if (!mounted) return;
        setState(() {
          _statusMessage = 'Koneksi berhasil!';
          _isLoading = false;
        });
        context.go('/login');
      }
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _statusMessage =
            'Gagal terhubung. Pastikan backend Docker berjalan dan HP berada di jaringan yang sama.';
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
              child: _isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Test Connection'),
            ),
            const SizedBox(height: 20),
            Text(
              _statusMessage,
              style: TextStyle(
                color: _statusMessage.contains('berhasil')
                    ? Colors.green
                    : Colors.red,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
