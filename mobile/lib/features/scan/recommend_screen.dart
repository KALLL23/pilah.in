import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../core/providers/auth_provider.dart';
import '../result/result_screen.dart';

class RecommendScreen extends ConsumerStatefulWidget {
  final String imagePath;
  final Map<String, dynamic> scanResponse;

  const RecommendScreen({
    super.key,
    required this.imagePath,
    required this.scanResponse,
  });

  @override
  ConsumerState<RecommendScreen> createState() => _RecommendScreenState();
}

class _RecommendScreenState extends ConsumerState<RecommendScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _rotationAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();
    _rotationAnimation = Tween<double>(begin: 0, end: 1).animate(_controller);
    _fetchRecommendation();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _fetchRecommendation() async {
    final dio = ref.read(dioProvider);
    final authSession = ref.read(authSessionProvider).value;

    if (authSession == null || !authSession.isAuthenticated) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Sesi tidak valid.')),
        );
        Navigator.of(context).pop();
      }
      return;
    }

    try {
      final scanId = widget.scanResponse['id'];
      final response = await dio.post(
        '${authSession.serverUrl}/api/v1/scans/$scanId/recommend',
        options: Options(
          headers: {'Authorization': 'Bearer ${authSession.accessToken}'},
        ),
      );

      if (mounted) {
        final recommendation = response.data as Map<String, dynamic>;
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (context) => ResultScreen(
              imagePath: widget.imagePath,
              scanResponse: widget.scanResponse,
              recommendation: recommendation,
            ),
          ),
        );
      }
    } on DioException catch (e) {
      String errMsg = 'Gagal mendapatkan rekomendasi.';
      if (e.response?.data != null) {
        try {
          errMsg = e.response?.data['error']['message'] ?? errMsg;
        } catch (_) {}
      }
      if (mounted) {
        _showError(errMsg);
      }
    } catch (e) {
      if (mounted) {
        _showError('Error: $e');
      }
    }
  }

  void _showError(String message) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Gagal'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              Navigator.of(context).pop();
            },
            child: const Text('Kembali'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              _fetchRecommendation();
            },
            child: const Text('Coba Lagi'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            RotationTransition(
              turns: _rotationAnimation,
              child: Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: primaryGreen, width: 3),
                ),
                child: const Icon(Icons.psychology, color: primaryGreen, size: 40),
              ),
            ),
            const SizedBox(height: 32),
            const Text(
              'Mendapatkan Rekomendasi',
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: primaryGreen,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'AI sedang menganalisis kondisi\nuntuk rekomendasi terbaik...',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade600,
                height: 1.5,
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: 200,
              child: LinearProgressIndicator(
                backgroundColor: Colors.grey.shade200,
                valueColor: const AlwaysStoppedAnimation<Color>(primaryGreen),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
