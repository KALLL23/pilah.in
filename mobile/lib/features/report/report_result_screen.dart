import 'dart:io';
import 'package:flutter/material.dart';

class ReportResultScreen extends StatelessWidget {
  final String imagePath;
  final Map<String, dynamic> reportData;

  const ReportResultScreen({
    super.key,
    required this.imagePath,
    required this.reportData,
  });

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);

    final riskLevel = reportData['risk_level'] as String? ?? 'LOW';
    final riskScore = (reportData['risk_score'] as num?)?.toDouble() ?? 0;
    final riskReasons =
        (reportData['risk_reasons'] as List<dynamic>?)?.cast<String>() ?? [];
    final objects =
        (reportData['objects'] as List<dynamic>?)?.cast<Map<String, dynamic>>() ??
            [];
    final address = reportData['address'] as String? ?? '-';
    final status = reportData['status'] as String? ?? 'REPORTED';
    final wasteVolume = reportData['waste_volume'] as String? ?? '-';
    final standingWater = reportData['standing_water'] as bool? ?? false;
    final drainageBlockage = reportData['drainage_blockage'] as bool? ?? false;
    final organicPresence = reportData['organic_presence'] as bool? ?? false;

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      body: Stack(
        children: [
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            height: MediaQuery.of(context).size.height * 0.3,
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
          Align(
            alignment: Alignment.bottomCenter,
            child: Container(
              height: MediaQuery.of(context).size.height * 0.75,
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
                    // Status badge
                    Center(
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 16, vertical: 8),
                        decoration: BoxDecoration(
                          color: const Color(0xFFE8F5E9),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.check_circle,
                                color: primaryGreen, size: 16),
                            const SizedBox(width: 8),
                            Text(
                              'Laporan Tercatat - ${_statusText(status)}',
                              style: const TextStyle(
                                color: primaryGreen,
                                fontWeight: FontWeight.w600,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Risk Score Card
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: _riskColor(riskLevel).withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: _riskColor(riskLevel).withValues(alpha: 0.3),
                        ),
                      ),
                      child: Column(
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.shield,
                                  color: _riskColor(riskLevel), size: 24),
                              const SizedBox(width: 8),
                              Text(
                                'Risk Level: ${_riskLevelText(riskLevel)}',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                  color: _riskColor(riskLevel),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          // Progress bar
                          ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: riskScore / 100,
                              backgroundColor: Colors.grey.shade200,
                              valueColor: AlwaysStoppedAnimation<Color>(
                                _riskColor(riskLevel),
                              ),
                              minHeight: 8,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Score: ${riskScore.toStringAsFixed(0)}/100',
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Risk Reasons
                    if (riskReasons.isNotEmpty) ...[
                      const Text(
                        'Alasan Risiko',
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                        ),
                      ),
                      const SizedBox(height: 8),
                      ...riskReasons.map((reason) => Padding(
                            padding: const EdgeInsets.only(bottom: 4),
                            child: Row(
                              children: [
                                Icon(Icons.warning_amber_rounded,
                                    color: _riskColor(riskLevel), size: 16),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    reason,
                                    style: const TextStyle(fontSize: 13),
                                  ),
                                ),
                              ],
                            ),
                          )),
                      const SizedBox(height: 16),
                    ],

                    // Detected Objects
                    if (objects.isNotEmpty) ...[
                      Text(
                        'Objek Terdeteksi (${objects.length})',
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: objects.map((obj) {
                          final category = obj['category'] as String? ?? '-';
                          final confidence =
                              (obj['confidence'] as num?)?.toDouble() ?? 0;
                          return Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 6),
                            decoration: BoxDecoration(
                              color: Colors.grey.shade100,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(color: Colors.grey.shade300),
                            ),
                            child: Text(
                              '${_categoryName(category)} ${(confidence * 100).toStringAsFixed(0)}%',
                              style: const TextStyle(fontSize: 12),
                            ),
                          );
                        }).toList(),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // Environment Info
                    const Text(
                      'Kondisi Lingkungan',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 8),
                    _buildInfoRow('Volume', _volumeText(wasteVolume)),
                    _buildInfoRow('Genangan Air', standingWater ? 'Ya' : 'Tidak'),
                    _buildInfoRow('Saluran Tersumbat', drainageBlockage ? 'Ya' : 'Tidak'),
                    _buildInfoRow('Organik', organicPresence ? 'Terdeteksi' : 'Tidak'),
                    const SizedBox(height: 12),

                    // Address
                    const Text(
                      'Lokasi',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Icon(Icons.location_on,
                            color: Colors.grey.shade500, size: 16),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            address,
                            style: const TextStyle(fontSize: 13),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),

                    // Back button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () {
                          Navigator.of(context)
                              .popUntil((route) => route.isFirst);
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: primaryGreen,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8)),
                        ),
                        child: const Text(
                          'Kembali ke Beranda',
                          style: TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              fontWeight: FontWeight.w600),
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

  Color _riskColor(String level) {
    switch (level) {
      case 'HIGH':
        return Colors.red;
      case 'MEDIUM':
        return Colors.orange;
      case 'LOW':
        return const Color(0xFF00BFA5);
      default:
        return Colors.grey;
    }
  }

  String _riskLevelText(String level) {
    switch (level) {
      case 'HIGH':
        return 'TINGGI';
      case 'MEDIUM':
        return 'SEDANG';
      case 'LOW':
        return 'RENDAH';
      default:
        return level;
    }
  }

  String _statusText(String status) {
    switch (status) {
      case 'REPORTED':
        return 'Dilaporkan';
      case 'VERIFIED':
        return 'Diverifikasi';
      case 'IN_PROGRESS':
        return 'Ditangani';
      case 'RESOLVED':
        return 'Selesai';
      default:
        return status;
    }
  }

  String _volumeText(String volume) {
    switch (volume) {
      case 'SMALL':
        return 'Kecil';
      case 'MEDIUM':
        return 'Sedang';
      case 'LARGE':
        return 'Besar';
      default:
        return volume;
    }
  }

  String _categoryName(String code) {
    switch (code) {
      case 'PLASTIC':
        return 'Plastik';
      case 'PAPER_CARDBOARD':
        return 'Kertas';
      case 'GLASS':
        return 'Kaca';
      case 'METAL':
        return 'Logam';
      case 'ORGANIC':
        return 'Organik';
      case 'TEXTILE':
        return 'Tekstil';
      case 'ELECTRONIC_SPECIAL':
        return 'Elektronik';
      case 'RESIDUAL_MIXED':
        return 'Residu';
      default:
        return code;
    }
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          Text(
            '$label: ',
            style: TextStyle(
              fontSize: 13,
              color: Colors.grey.shade600,
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
