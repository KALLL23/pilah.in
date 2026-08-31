import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../core/providers/auth_provider.dart';
import 'recommend_screen.dart';

const List<Map<String, String>> wasteCategories = [
  {'code': 'PLASTIC', 'name': 'Plastik'},
  {'code': 'PAPER_CARDBOARD', 'name': 'Kertas & Karton'},
  {'code': 'GLASS', 'name': 'Kaca'},
  {'code': 'METAL', 'name': 'Logam'},
  {'code': 'ORGANIC', 'name': 'Organik'},
  {'code': 'TEXTILE', 'name': 'Tekstil'},
  {'code': 'ELECTRONIC_SPECIAL', 'name': 'Elektronik Khusus'},
  {'code': 'RESIDUAL_MIXED', 'name': 'Residu / Campuran'},
];

class ConfirmScreen extends ConsumerStatefulWidget {
  final String imagePath;
  final Map<String, dynamic> scanResponse;

  const ConfirmScreen({
    super.key,
    required this.imagePath,
    required this.scanResponse,
  });

  @override
  ConsumerState<ConfirmScreen> createState() => _ConfirmScreenState();
}

class _ConfirmScreenState extends ConsumerState<ConfirmScreen> {
  late String _selectedCategoryCode;
  bool? _isReusable;
  bool? _isContaminated;
  bool? _isWet;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    final predicted = widget.scanResponse['predicted_category'] as Map<String, dynamic>?;
    _selectedCategoryCode = predicted?['code'] ?? 'PLASTIC';
  }

  double get _confidence =>
      (widget.scanResponse['prediction_confidence'] as num).toDouble();

  bool get _isLowConfidence =>
      widget.scanResponse['low_confidence'] as bool;

  String get _categoryDisplayName {
    final match = wasteCategories.firstWhere(
      (c) => c['code'] == _selectedCategoryCode,
      orElse: () => wasteCategories.first,
    );
    return match['name']!;
  }

  Future<void> _submitConfirm() async {
    if (_isReusable == null || _isContaminated == null || _isWet == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Jawab semua pertanyaan kondisi terlebih dahulu.')),
      );
      return;
    }

    final dio = ref.read(dioProvider);
    final authSession = ref.read(authSessionProvider).value;
    if (authSession == null || !authSession.isAuthenticated) return;

    setState(() => _isSubmitting = true);

    try {
      final scanId = widget.scanResponse['id'];
      await dio.patch(
        '${authSession.serverUrl}/api/v1/scans/$scanId/confirm',
        data: {
          'confirmed_category': _selectedCategoryCode,
          'is_reusable': _isReusable,
          'is_contaminated': _isContaminated,
          'is_wet': _isWet,
        },
        options: Options(
          headers: {'Authorization': 'Bearer ${authSession.accessToken}'},
        ),
      );

      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (context) => RecommendScreen(
              imagePath: widget.imagePath,
              scanResponse: widget.scanResponse,
            ),
          ),
        );
      }
    } on DioException catch (e) {
      String errMsg = 'Gagal menyimpan konfirmasi.';
      if (e.response?.data != null) {
        try {
          errMsg = e.response?.data['error']['message'] ?? errMsg;
        } catch (_) {}
      }
      if (mounted) {
        setState(() => _isSubmitting = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(errMsg)));
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isSubmitting = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);
    const accentGreen = Color(0xFF00BFA5);

    return Scaffold(
      backgroundColor: Colors.white,
      body: Stack(
        children: [
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            height: MediaQuery.of(context).size.height * 0.35,
            child: Image.file(File(widget.imagePath), fit: BoxFit.cover),
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
              height: MediaQuery.of(context).size.height * 0.7,
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
                      child: Text(
                        _isLowConfidence ? 'Konfirmasi Kategori' : 'Kategori Terdeteksi',
                        style: const TextStyle(
                          color: primaryGreen,
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),

                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            _categoryDisplayName,
                            style: const TextStyle(
                              fontSize: 28,
                              fontWeight: FontWeight.bold,
                              color: primaryGreen,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: _isLowConfidence ? Colors.orange.shade50 : const Color(0xFFE8F5E9),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Row(
                            children: [
                              Icon(
                                _isLowConfidence ? Icons.warning_amber_rounded : Icons.check_circle,
                                size: 14,
                                color: _isLowConfidence ? Colors.orange : accentGreen,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                '${(_confidence * 100).toStringAsFixed(1)}%',
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.bold,
                                  color: _isLowConfidence ? Colors.orange.shade700 : primaryGreen,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),

                    if (_isLowConfidence) ...[
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.orange.shade50,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.orange.shade200),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.info_outline, size: 16, color: Colors.orange.shade700),
                            const SizedBox(width: 8),
                            const Expanded(
                              child: Text(
                                'Keyakinan model rendah. Pilih kategori yang benar.',
                                style: TextStyle(fontSize: 12, color: Colors.black87),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],

                    const SizedBox(height: 16),

                    const Text(
                      'Kategori Sampah',
                      style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.grey.shade300),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: DropdownButton<String>(
                        value: _selectedCategoryCode,
                        isExpanded: true,
                        underline: const SizedBox(),
                        items: wasteCategories.map((cat) {
                          return DropdownMenuItem(
                            value: cat['code'],
                            child: Text(cat['name']!),
                          );
                        }).toList(),
                        onChanged: (value) {
                          if (value != null) setState(() => _selectedCategoryCode = value);
                        },
                      ),
                    ),

                    const SizedBox(height: 24),
                    const Text(
                      'Kondisi Sampah',
                      style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
                    ),
                    const SizedBox(height: 12),

                    _ConditionQuestion(
                      question: 'Apakah masih dapat digunakan kembali?',
                      groupValue: _isReusable,
                      onChanged: (v) => setState(() => _isReusable = v),
                    ),
                    const SizedBox(height: 8),
                    _ConditionQuestion(
                      question: 'Apakah terkena sisa makanan / kotoran?',
                      groupValue: _isContaminated,
                      onChanged: (v) => setState(() => _isContaminated = v),
                    ),
                    const SizedBox(height: 8),
                    _ConditionQuestion(
                      question: 'Apakah basah?',
                      groupValue: _isWet,
                      onChanged: (v) => setState(() => _isWet = v),
                    ),

                    const SizedBox(height: 24),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _isSubmitting ? null : _submitConfirm,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: primaryGreen,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        child: _isSubmitting
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                              )
                            : const Text(
                                'Dapatkan Rekomendasi',
                                style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600),
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

class _ConditionQuestion extends StatelessWidget {
  final String question;
  final bool? groupValue;
  final ValueChanged<bool> onChanged;

  const _ConditionQuestion({
    required this.question,
    required this.groupValue,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(question, style: const TextStyle(fontSize: 13)),
          ),
          ChoiceChip(
            label: const Text('Ya', style: TextStyle(fontSize: 12)),
            selected: groupValue == true,
            selectedColor: const Color(0xFFE8F5E9),
            onSelected: (_) => onChanged(true),
          ),
          const SizedBox(width: 6),
          ChoiceChip(
            label: const Text('Tidak', style: TextStyle(fontSize: 12)),
            selected: groupValue == false,
            selectedColor: const Color(0xFFFFF3E0),
            onSelected: (_) => onChanged(false),
          ),
        ],
      ),
    );
  }
}
