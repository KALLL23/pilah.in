import 'dart:io';
import 'package:flutter/material.dart';

class ResultScreen extends StatelessWidget {
  final String imagePath;
  final Map<String, dynamic> scanResponse;
  final Map<String, dynamic>? recommendation;

  const ResultScreen({
    super.key,
    required this.imagePath,
    required this.scanResponse,
    this.recommendation,
  });

  static const Map<String, Color> _actionColors = {
    'REUSE': Color(0xFF2E7D32),
    'RECYCLE': Color(0xFF1565C0),
    'COMPOST': Color(0xFF558B2F),
    'RESIDUAL': Color(0xFF757575),
    'SPECIAL_HANDLING': Color(0xFFC62828),
  };

  static const Map<String, String> _actionLabels = {
    'REUSE': 'Gunakan Kembali',
    'RECYCLE': 'Daur Ulang',
    'COMPOST': 'Kompos',
    'RESIDUAL': 'Buang ke Tempat Sampah',
    'SPECIAL_HANDLING': 'Penanganan Khusus',
  };

  static const Map<String, IconData> _actionIcons = {
    'REUSE': Icons.replay,
    'RECYCLE': Icons.recycling,
    'COMPOST': Icons.eco,
    'RESIDUAL': Icons.delete_outline,
    'SPECIAL_HANDLING': Icons.warning_amber,
  };

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);

    final predictedCategory = scanResponse['predicted_category'] as Map<String, dynamic>;
    final confidence = (scanResponse['prediction_confidence'] as num).toDouble();
    final categoryName = predictedCategory['name'] as String;

    final action = recommendation?['action'] as String?;
    final reason = recommendation?['reason'] as String?;
    final preparationSteps = (recommendation?['preparation_steps'] as List<dynamic>?)
        ?.map((e) => e.toString())
        .toList();
    final warnings = (recommendation?['warnings'] as List<dynamic>?)
        ?.map((e) => e.toString())
        .toList();

    final actionColor = _actionColors[action] ?? Colors.grey;
    final actionLabel = _actionLabels[action] ?? action ?? '-';
    final actionIcon = _actionIcons[action] ?? Icons.help_outline;

    return Scaffold(
      backgroundColor: Colors.white,
      body: Stack(
        children: [
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            height: MediaQuery.of(context).size.height * 0.4,
            child: Image.file(File(imagePath), fit: BoxFit.cover),
          ),
          Positioned(
            top: 40,
            left: 8,
            child: IconButton(
              icon: const Icon(Icons.arrow_back, color: Colors.white),
              onPressed: () => Navigator.pop(context),
            ),
          ),
          Positioned(
            top: MediaQuery.of(context).size.height * 0.35,
            right: 20,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.95),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.1), blurRadius: 8)],
              ),
              child: Row(
                children: [
                  const Icon(Icons.check_circle, color: primaryGreen, size: 16),
                  const SizedBox(width: 4),
                  Text(
                    '${(confidence * 100).toStringAsFixed(1)}%',
                    style: const TextStyle(
                      color: primaryGreen,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
          ),
          Align(
            alignment: Alignment.bottomCenter,
            child: Container(
              height: MediaQuery.of(context).size.height * 0.65,
              padding: const EdgeInsets.all(24),
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(24),
                  topRight: Radius.circular(24),
                ),
              ),
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE8F5E9),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: const Text(
                        'Hasil Analisis',
                        style: TextStyle(
                          color: primaryGreen,
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      categoryName,
                      style: const TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: primaryGreen,
                      ),
                    ),
                    const SizedBox(height: 16),

                    if (action != null) ...[
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: actionColor.withValues(alpha: 0.08),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: actionColor.withValues(alpha: 0.3)),
                        ),
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: actionColor.withValues(alpha: 0.15),
                                shape: BoxShape.circle,
                              ),
                              child: Icon(actionIcon, color: actionColor, size: 22),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Tindakan',
                                    style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                                  ),
                                  Text(
                                    actionLabel,
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                      color: actionColor,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    if (reason != null && reason.isNotEmpty) ...[
                      Row(
                        children: [
                          const Icon(Icons.lightbulb_outline, color: primaryGreen, size: 18),
                          const SizedBox(width: 6),
                          const Text(
                            'Alasan',
                            style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        reason,
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.grey.shade700,
                          height: 1.5,
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    if (preparationSteps != null && preparationSteps.isNotEmpty) ...[
                      Row(
                        children: [
                          const Icon(Icons.checklist, color: primaryGreen, size: 18),
                          const SizedBox(width: 6),
                          const Text(
                            'Langkah Persiapan',
                            style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      ...preparationSteps.asMap().entries.map((entry) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                margin: const EdgeInsets.only(top: 5),
                                width: 6,
                                height: 6,
                                decoration: const BoxDecoration(
                                  color: primaryGreen,
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  entry.value,
                                  style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
                                ),
                              ),
                            ],
                          ),
                        );
                      }),
                      const SizedBox(height: 16),
                    ],

                    if (warnings != null && warnings.isNotEmpty) ...[
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFF3E0),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.orange.shade200),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              children: [
                                Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 18),
                                SizedBox(width: 6),
                                Text(
                                  'Peringatan',
                                  style: TextStyle(
                                    fontWeight: FontWeight.w600,
                                    fontSize: 14,
                                    color: Colors.orange,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            ...warnings.map((w) => Padding(
                              padding: const EdgeInsets.only(bottom: 4),
                              child: Text(
                                '• $w',
                                style: TextStyle(fontSize: 12, color: Colors.orange.shade800),
                              ),
                            )),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    if (action == null) ...[
                      Center(
                        child: Column(
                          children: [
                            Icon(Icons.info_outline, size: 48, color: Colors.grey.shade400),
                            const SizedBox(height: 12),
                            Text(
                              'Rekomendasi belum tersedia.',
                              style: TextStyle(fontSize: 14, color: Colors.grey.shade500),
                            ),
                          ],
                        ),
                      ),
                    ],

                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        onPressed: () {
                          Navigator.of(context).popUntil((route) => route.isFirst);
                        },
                        icon: const Icon(Icons.home_outlined, color: primaryGreen),
                        label: const Text(
                          'Kembali ke Beranda',
                          style: TextStyle(color: primaryGreen, fontSize: 14, fontWeight: FontWeight.w600),
                        ),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          side: const BorderSide(color: Colors.grey),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
