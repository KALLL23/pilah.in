import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../core/providers/auth_provider.dart';
import 'confirm_screen.dart';

class AnalyzingScreen extends ConsumerStatefulWidget {
  final String imagePath;
  const AnalyzingScreen({super.key, required this.imagePath});

  @override
  ConsumerState<AnalyzingScreen> createState() => _AnalyzingScreenState();
}

class _AnalyzingScreenState extends ConsumerState<AnalyzingScreen> {
  @override
  void initState() {
    super.initState();
    _processImage();
  }

  Future<void> _processImage() async {
    final dio = ref.read(dioProvider);
    final authSession = ref.read(authSessionProvider).value;

    if (authSession == null || !authSession.isAuthenticated || authSession.serverUrl == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Anda belum terhubung ke server.')),
        );
        Navigator.of(context).pop();
      }
      return;
    }

    try {
      final formData = FormData.fromMap({
        'image': await MultipartFile.fromFile(widget.imagePath),
      });

      final response = await dio.post(
        '${authSession.serverUrl}/api/v1/scans/infer',
        data: formData,
        options: Options(
          headers: {
            'Authorization': 'Bearer ${authSession.accessToken}',
          },
        ),
      );

      if (mounted) {
        final scanData = response.data as Map<String, dynamic>;
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (context) => ConfirmScreen(
              imagePath: widget.imagePath,
              scanResponse: scanData,
            ),
          ),
        );
      }
    } on DioException catch (e) {
      String errMsg = 'Terjadi kesalahan.';
      if (e.response != null && e.response?.data != null) {
        try {
          errMsg = e.response?.data['error']['message'] ?? errMsg;
        } catch (_) {}
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Gagal menganalisis gambar: $errMsg')),
        );
        Navigator.of(context).pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
        Navigator.of(context).pop();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);
    const accentGreen = Color(0xFF00BFA5);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Stack(
              alignment: Alignment.center,
              children: [
                SizedBox(
                  width: 120,
                  height: 120,
                  child: CircularProgressIndicator(
                    valueColor: AlwaysStoppedAnimation<Color>(accentGreen.withValues(alpha: 0.5)),
                    strokeWidth: 8,
                  ),
                ),
                Container(
                  width: 80,
                  height: 80,
                  decoration: const BoxDecoration(
                    color: primaryGreen,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.auto_awesome, color: Colors.white, size: 40),
                ),
              ],
            ),
            const SizedBox(height: 32),
            const Text(
              'Menganalisis Sampah',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: primaryGreen,
              ),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey.withValues(alpha: 0.2)),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.sync, color: accentGreen, size: 16),
                  SizedBox(width: 8),
                  Text(
                    'AI sedang mengenali jenis\nsampah...',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontFamily: 'monospace', fontSize: 12, color: Colors.black54),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
