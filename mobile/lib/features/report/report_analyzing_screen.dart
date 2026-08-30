import 'package:flutter/material.dart';
import 'report_result_screen.dart';

class ReportAnalyzingScreen extends StatefulWidget {
  final String imagePath;
  final Map<String, dynamic> reportData;

  const ReportAnalyzingScreen({
    super.key,
    required this.imagePath,
    required this.reportData,
  });

  @override
  State<ReportAnalyzingScreen> createState() => _ReportAnalyzingScreenState();
}

class _ReportAnalyzingScreenState extends State<ReportAnalyzingScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();

    // Navigate to result after a short delay (backend already processed)
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (context) => ReportResultScreen(
              imagePath: widget.imagePath,
              reportData: widget.reportData,
            ),
          ),
        );
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
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
                    valueColor: AlwaysStoppedAnimation<Color>(
                        accentGreen.withValues(alpha: 0.5)),
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
                  child: const Icon(Icons.analytics,
                      color: Colors.white, size: 40),
                ),
              ],
            ),
            const SizedBox(height: 32),
            const Text(
              'Menganalisis Laporan',
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
                    'Memproses laporan...',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 12,
                        color: Colors.black54),
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
