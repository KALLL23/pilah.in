import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:geolocator/geolocator.dart';
import '../../core/providers/auth_provider.dart';
import 'report_repository.dart';
import 'report_analyzing_screen.dart';

class ReportFormScreen extends ConsumerStatefulWidget {
  final String imagePath;

  const ReportFormScreen({super.key, required this.imagePath});

  @override
  ConsumerState<ReportFormScreen> createState() => _ReportFormScreenState();
}

class _ReportFormScreenState extends ConsumerState<ReportFormScreen> {
  String _wasteVolume = 'MEDIUM';
  bool? _standingWater;
  bool? _drainageBlockage;
  final TextEditingController _descriptionController = TextEditingController();
  bool _isSubmitting = false;
  Position? _currentPosition;
  bool _isLoadingLocation = true;
  String? _locationError;

  @override
  void initState() {
    super.initState();
    _getCurrentLocation();
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _getCurrentLocation() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        setState(() {
          _locationError = 'Layanan lokasi tidak aktif';
          _isLoadingLocation = false;
        });
        return;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          setState(() {
            _locationError = 'Izin lokasi ditolak';
            _isLoadingLocation = false;
          });
          return;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        setState(() {
          _locationError = 'Izin lokasi ditolak permanen';
          _isLoadingLocation = false;
        });
        return;
      }

      Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );

      setState(() {
        _currentPosition = position;
        _isLoadingLocation = false;
      });
    } catch (e) {
      setState(() {
        _locationError = 'Gagal mendapatkan lokasi: $e';
        _isLoadingLocation = false;
      });
    }
  }

  Future<void> _submitReport() async {
    if (_standingWater == null || _drainageBlockage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Jawab semua pertanyaan kondisi terlebih dahulu.')),
      );
      return;
    }

    if (_currentPosition == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Lokasi belum tersedia.')),
      );
      return;
    }

    final dio = ref.read(dioProvider);
    final authSession = ref.read(authSessionProvider).value;
    if (authSession == null || !authSession.isAuthenticated) return;

    setState(() => _isSubmitting = true);

    try {
      final repository = ReportRepository(dio, authSession.serverUrl!);
      final reportData = await repository.createReport(
        imagePath: widget.imagePath,
        latitude: _currentPosition!.latitude,
        longitude: _currentPosition!.longitude,
        locationAccuracyM: _currentPosition!.accuracy,
        userDescription: _descriptionController.text,
        wasteVolume: _wasteVolume,
        standingWater: _standingWater!,
        drainageBlockage: _drainageBlockage!,
        accessToken: authSession.accessToken!,
      );

      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (context) => ReportAnalyzingScreen(
              imagePath: widget.imagePath,
              reportData: reportData,
            ),
          ),
        );
      }
    } on DioException catch (e) {
      String errMsg = 'Gagal mengirim laporan.';
      if (e.response?.data != null) {
        try {
          errMsg = e.response?.data['error']['message'] ?? errMsg;
        } catch (_) {}
      }
      if (mounted) {
        setState(() => _isSubmitting = false);
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(errMsg)));
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isSubmitting = false);
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);

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
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE8F5E9),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: const Text(
                        'Laporan Sampah',
                        style: TextStyle(
                          color: primaryGreen,
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Informasi Lingkungan',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: primaryGreen,
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Location status
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: _currentPosition != null
                            ? const Color(0xFFE8F5E9)
                            : _locationError != null
                                ? const Color(0xFFFFF3E0)
                                : Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                          color: _currentPosition != null
                              ? const Color(0xFF00BFA5)
                              : _locationError != null
                                  ? Colors.orange
                                  : Colors.grey.shade300,
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            _currentPosition != null
                                ? Icons.location_on
                                : _locationError != null
                                    ? Icons.location_off
                                    : Icons.location_searching,
                            color: _currentPosition != null
                                ? const Color(0xFF00BFA5)
                                : _locationError != null
                                    ? Colors.orange
                                    : Colors.grey,
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _isLoadingLocation
                                  ? 'Mendapatkan lokasi...'
                                  : _currentPosition != null
                                      ? 'Lokasi: ${_currentPosition!.latitude.toStringAsFixed(5)}, ${_currentPosition!.longitude.toStringAsFixed(5)}'
                                      : _locationError ?? 'Lokasi tidak diketahui',
                              style: const TextStyle(fontSize: 12),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Waste Volume
                    const Text(
                      'Volume Sampah',
                      style:
                          TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        _buildVolumeChip('SMALL', 'Kecil'),
                        const SizedBox(width: 8),
                        _buildVolumeChip('MEDIUM', 'Sedang'),
                        const SizedBox(width: 8),
                        _buildVolumeChip('LARGE', 'Besar'),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // Standing Water
                    const Text(
                      'Genangan Air',
                      style:
                          TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                    ),
                    const SizedBox(height: 8),
                    _buildYesNoQuestion(
                      question: 'Apakah terdapat genangan air di sekitar?',
                      groupValue: _standingWater,
                      onChanged: (v) => setState(() => _standingWater = v),
                    ),
                    const SizedBox(height: 12),

                    // Drainage Blockage
                    const Text(
                      'Saluran Tersumbat',
                      style:
                          TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                    ),
                    const SizedBox(height: 8),
                    _buildYesNoQuestion(
                      question: 'Apakah saluran air tersumbat?',
                      groupValue: _drainageBlockage,
                      onChanged: (v) => setState(() => _drainageBlockage = v),
                    ),
                    const SizedBox(height: 12),

                    // Description
                    const Text(
                      'Deskripsi (Opsional)',
                      style:
                          TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _descriptionController,
                      maxLines: 3,
                      decoration: InputDecoration(
                        hintText: 'Tambahkan detail laporan...',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                        contentPadding: const EdgeInsets.all(12),
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Submit button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _isSubmitting ? null : _submitReport,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: primaryGreen,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8)),
                        ),
                        child: _isSubmitting
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(
                                    color: Colors.white, strokeWidth: 2),
                              )
                            : const Text(
                                'Kirim Laporan',
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

  Widget _buildVolumeChip(String value, String label) {
    const primaryGreen = Color(0xFF1E3F28);
    final isSelected = _wasteVolume == value;

    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _wasteVolume = value),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSelected ? primaryGreen : Colors.grey.shade100,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: isSelected ? primaryGreen : Colors.grey.shade300,
            ),
          ),
          child: Center(
            child: Text(
              label,
              style: TextStyle(
                color: isSelected ? Colors.white : Colors.black87,
                fontWeight: FontWeight.w600,
                fontSize: 14,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildYesNoQuestion({
    required String question,
    required bool? groupValue,
    required ValueChanged<bool> onChanged,
  }) {
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
