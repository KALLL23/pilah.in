import 'package:flutter/material.dart';
import '../result/result_screen.dart';

class AnalyzingScreen extends StatefulWidget {
  final String imagePath;
  const AnalyzingScreen({super.key, required this.imagePath});

  @override
  State<AnalyzingScreen> createState() => _AnalyzingScreenState();
}

class _AnalyzingScreenState extends State<AnalyzingScreen> {
  @override
  void initState() {
    super.initState();
    _simulateAIProcessing();
  }

  Future<void> _simulateAIProcessing() async {
    // Simulasi jeda waktu pemrosesan API (3 detik)
    await Future.delayed(const Duration(seconds: 3));
    
    if (mounted) {
      // Pindah ke layar hasil dan hapus layar loading dari tumpukan navigasi
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => ResultScreen(imagePath: widget.imagePath),
        ),
      );
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
            // Animasi Radar/Scanner sederhana
            Stack(
              alignment: Alignment.center,
              children: [
                SizedBox(
                  width: 120,
                  height: 120,
                  child: CircularProgressIndicator(
                    valueColor: AlwaysStoppedAnimation<Color>(accentGreen.withOpacity(0.5)),
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
              'Analyzing Item',
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
                border: Border.all(color: Colors.grey.withOpacity(0.2)),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.sync, color: accentGreen, size: 16),
                  SizedBox(width: 8),
                  Text(
                    'AI is analyzing material\nand circularity...',
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