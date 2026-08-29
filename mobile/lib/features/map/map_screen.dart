import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../../core/providers/auth_provider.dart';
import 'map_repository.dart';

class MapScreen extends ConsumerStatefulWidget {
  const MapScreen({super.key});

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen> {
  late MapRepository _repository;

  bool _showReports = true;
  bool _showFacilities = true;
  bool _showHotspots = true;

  List<Map<String, dynamic>> _reports = [];
  List<Map<String, dynamic>> _facilities = [];
  List<Map<String, dynamic>> _hotspots = [];

  final Set<Marker> _markers = {};

  bool _isLoading = true;
  String? _error;

  static const double _defaultLat = -6.9666;
  static const double _defaultLng = 110.4196;
  static const double _defaultZoom = 12.0;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final authSession = ref.read(authSessionProvider).value;
    if (authSession == null || !authSession.isAuthenticated) return;

    _repository = MapRepository(
      ref.read(dioProvider),
      authSession.serverUrl!,
    );

    try {
      final results = await Future.wait([
        _repository.getReports(accessToken: authSession.accessToken!),
        _repository.getFacilities(accessToken: authSession.accessToken!),
        _repository.getHotspots(accessToken: authSession.accessToken!),
      ]);

      if (mounted) {
        setState(() {
          _reports = (results[0]['features'] as List<dynamic>?)
                  ?.map((e) => Map<String, dynamic>.from(e as Map))
                  .toList() ??
              [];
          _facilities = (results[1]['features'] as List<dynamic>?)
                  ?.map((e) => Map<String, dynamic>.from(e as Map))
                  .toList() ??
              [];
          _hotspots = (results[2]['features'] as List<dynamic>?)
                  ?.map((e) => Map<String, dynamic>.from(e as Map))
                  .toList() ??
              [];
          _isLoading = false;
        });
        _updateMarkers();
      }
    } on DioException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message ?? 'Gagal memuat data peta';
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Error: $e';
          _isLoading = false;
        });
      }
    }
  }

  void _updateMarkers() {
    _markers.clear();

    if (_showReports) {
      _addReportMarkers();
    }
    if (_showFacilities) {
      _addFacilityMarkers();
    }
    if (_showHotspots) {
      _addHotspotMarkers();
    }

    setState(() {});
  }

  void _addReportMarkers() {
    for (final feature in _reports) {
      final geometry = feature['geometry'] as Map<String, dynamic>?;
      final properties = feature['properties'] as Map<String, dynamic>?;
      if (geometry == null || properties == null) continue;

      final coordinates = geometry['coordinates'] as List<dynamic>?;
      if (coordinates == null || coordinates.length < 2) continue;

      final lng = coordinates[0] as double;
      final lat = coordinates[1] as double;
      final riskLevel = properties['risk_level'] as String? ?? 'LOW';

      _markers.add(
        Marker(
          markerId: MarkerId('report_${feature['id']}'),
          position: LatLng(lat, lng),
          icon: _riskMarkerIcon(riskLevel),
          onTap: () => _showDetailPopup('report', {
            'type': 'report',
            'id': feature['id'],
            ...properties,
          }),
        ),
      );
    }
  }

  void _addFacilityMarkers() {
    for (final feature in _facilities) {
      final geometry = feature['geometry'] as Map<String, dynamic>?;
      final properties = feature['properties'] as Map<String, dynamic>?;
      if (geometry == null || properties == null) continue;

      final coordinates = geometry['coordinates'] as List<dynamic>?;
      if (coordinates == null || coordinates.length < 2) continue;

      final lng = coordinates[0] as double;
      final lat = coordinates[1] as double;

      _markers.add(
        Marker(
          markerId: MarkerId('facility_${feature['id']}'),
          position: LatLng(lat, lng),
          icon: BitmapDescriptor.defaultMarkerWithHue(
              BitmapDescriptor.hueGreen),
          onTap: () => _showDetailPopup('facility', {
            'type': 'facility',
            'id': feature['id'],
            ...properties,
          }),
        ),
      );
    }
  }

  void _addHotspotMarkers() {
    for (final feature in _hotspots) {
      final geometry = feature['geometry'] as Map<String, dynamic>?;
      final properties = feature['properties'] as Map<String, dynamic>?;
      if (geometry == null || properties == null) continue;

      final coordinates = geometry['coordinates'] as List<dynamic>?;
      if (coordinates == null || coordinates.length < 2) continue;

      final lng = coordinates[0] as double;
      final lat = coordinates[1] as double;

      _markers.add(
        Marker(
          markerId: MarkerId('hotspot_${feature['id']}'),
          position: LatLng(lat, lng),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
          onTap: () => _showDetailPopup('hotspot', {
            'type': 'hotspot',
            'id': feature['id'],
            ...properties,
          }),
        ),
      );
    }
  }

  BitmapDescriptor _riskMarkerIcon(String level) {
    switch (level) {
      case 'HIGH':
        return BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed);
      case 'MEDIUM':
        return BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueOrange);
      case 'LOW':
        return BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueCyan);
      default:
        return BitmapDescriptor.defaultMarker;
    }
  }

  void _showDetailPopup(String type, Map<String, dynamic> data) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _buildDetailPopup(type, data),
    );
  }

  Widget _buildDetailPopup(String type, Map<String, dynamic> data) {
    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.5,
      ),
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            if (type == 'report') ...[
              _buildReportDetail(data),
            ] else if (type == 'facility') ...[
              _buildFacilityDetail(data),
            ] else if (type == 'hotspot') ...[
              _buildHotspotDetail(data),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildReportDetail(Map<String, dynamic> data) {
    final riskLevel = data['risk_level'] as String? ?? 'LOW';
    final riskScore = (data['risk_score'] as num?)?.toDouble() ?? 0;
    final status = data['status'] as String? ?? '-';
    final riskReasons =
        (data['risk_reasons'] as List<dynamic>?)?.cast<String>() ?? [];
    final createdAt = data['created_at'] as String? ?? '';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(
              Icons.report_problem,
              color: _riskColor(riskLevel),
              size: 24,
            ),
            const SizedBox(width: 8),
            const Expanded(
              child: Text(
                'Laporan Sampah',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1E3F28),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        _buildDetailRow('Status', _statusText(status)),
        const SizedBox(height: 8),
        Row(
          children: [
            Text(
              'Risk Level: ',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 13),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: _riskColor(riskLevel).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                _riskLevelText(riskLevel),
                style: TextStyle(
                  color: _riskColor(riskLevel),
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Text(
              'Score: ${riskScore.toStringAsFixed(0)}/100',
              style: const TextStyle(fontSize: 13),
            ),
          ],
        ),
        if (riskReasons.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text(
            'Alasan Risiko:',
            style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
          ),
          const SizedBox(height: 4),
          ...riskReasons.map((reason) => Padding(
                padding: const EdgeInsets.only(bottom: 2),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber_rounded,
                        color: _riskColor(riskLevel), size: 14),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(reason, style: const TextStyle(fontSize: 12)),
                    ),
                  ],
                ),
              )),
        ],
        if (createdAt.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(
            'Dibuat: $createdAt',
            style: TextStyle(color: Colors.grey.shade500, fontSize: 11),
          ),
        ],
      ],
    );
  }

  Widget _buildFacilityDetail(Map<String, dynamic> data) {
    final name = data['name'] as String? ?? '-';
    final facilityType = data['facility_type'] as String? ?? '-';
    final address = data['address'] as String? ?? '-';
    final categories =
        (data['accepted_categories'] as List<dynamic>?)?.cast<String>() ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.location_city, color: Color(0xFF1E3F28), size: 24),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                name,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1E3F28),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        _buildDetailRow('Tipe', _facilityTypeText(facilityType)),
        const SizedBox(height: 8),
        _buildDetailRow('Alamat', address),
        if (categories.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text(
            'Kategori Diterima:',
            style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
          ),
          const SizedBox(height: 4),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: categories.map((cat) {
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFE8F5E9),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  _categoryName(cat),
                  style: const TextStyle(fontSize: 11, color: Color(0xFF1E3F28)),
                ),
              );
            }).toList(),
          ),
        ],
      ],
    );
  }

  Widget _buildHotspotDetail(Map<String, dynamic> data) {
    final reportCount = data['report_count'] as int? ?? 0;
    final avgRiskScore = (data['average_risk_score'] as num?)?.toDouble() ?? 0;
    final highestRisk = data['highest_risk_level'] as String? ?? 'LOW';
    final firstSeen = data['first_seen'] as String? ?? '';
    final lastSeen = data['last_seen'] as String? ?? '';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.whatshot, color: _riskColor(highestRisk), size: 24),
            const SizedBox(width: 8),
            const Expanded(
              child: Text(
                'Hotspot Sampah',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1E3F28),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        _buildDetailRow('Jumlah Laporan', '$reportCount laporan'),
        const SizedBox(height: 8),
        Row(
          children: [
            Text(
              'Risk Tertinggi: ',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 13),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: _riskColor(highestRisk).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                _riskLevelText(highestRisk),
                style: TextStyle(
                  color: _riskColor(highestRisk),
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        _buildDetailRow(
            'Rata-rata Score', avgRiskScore.toStringAsFixed(1)),
        if (firstSeen.isNotEmpty) ...[
          const SizedBox(height: 8),
          _buildDetailRow('Pertama Terlihat', firstSeen),
        ],
        if (lastSeen.isNotEmpty) ...[
          const SizedBox(height: 8),
          _buildDetailRow('Terakhir Terlihat', lastSeen),
        ],
      ],
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '$label: ',
          style: TextStyle(color: Colors.grey.shade600, fontSize: 13),
        ),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
          ),
        ),
      ],
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

  String _facilityTypeText(String type) {
    switch (type) {
      case 'BANK_SAMPAH':
        return 'Bank Sampah';
      case 'TPS3R':
        return 'TPS3R';
      case 'COLLECTOR':
        return 'Pengumpul';
      case 'RECYCLING_FACILITY':
        return 'Fasilitas Daur Ulang';
      case 'SPECIAL_WASTE_FACILITY':
        return 'Fasilitas Sampah Khusus';
      default:
        return type;
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

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      body: Stack(
        children: [
          if (!_isLoading && _error == null)
            GoogleMap(
              onMapCreated: (_) {},
              initialCameraPosition: const CameraPosition(
                target: LatLng(_defaultLat, _defaultLng),
                zoom: _defaultZoom,
              ),
              markers: _markers,
              myLocationEnabled: false,
              zoomControlsEnabled: false,
              mapToolbarEnabled: false,
              compassEnabled: true,
            ),

          if (_isLoading)
            const Center(
              child: CircularProgressIndicator(color: primaryGreen),
            ),

          if (_error != null && !_isLoading)
            Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.error_outline, size: 48, color: Colors.grey[400]),
                    const SizedBox(height: 16),
                    Text(
                      _error!,
                      style: TextStyle(color: Colors.grey[600], fontSize: 14),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () {
                        setState(() {
                          _isLoading = true;
                          _error = null;
                        });
                        _loadData();
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: primaryGreen,
                      ),
                      child: const Text('Coba Lagi',
                          style: TextStyle(color: Colors.white)),
                    ),
                  ],
                ),
              ),
            ),

          Positioned(
            top: MediaQuery.of(context).padding.top + 12,
            left: 12,
            right: 12,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _buildFilterChip(
                    label: 'Laporan',
                    icon: Icons.report_problem,
                    isSelected: _showReports,
                    color: Colors.orange,
                    onTap: () {
                      setState(() => _showReports = !_showReports);
                      _updateMarkers();
                    },
                  ),
                  const SizedBox(width: 8),
                  _buildFilterChip(
                    label: 'Fasilitas',
                    icon: Icons.location_city,
                    isSelected: _showFacilities,
                    color: const Color(0xFF1E3F28),
                    onTap: () {
                      setState(() => _showFacilities = !_showFacilities);
                      _updateMarkers();
                    },
                  ),
                  const SizedBox(width: 8),
                  _buildFilterChip(
                    label: 'Hotspot',
                    icon: Icons.whatshot,
                    isSelected: _showHotspots,
                    color: Colors.red,
                    onTap: () {
                      setState(() => _showHotspots = !_showHotspots);
                      _updateMarkers();
                    },
                  ),
                ],
              ),
            ),
          ),

          Positioned(
            bottom: 8,
            right: 8,
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.9),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  _buildLegendItem(Colors.red, 'HIGH'),
                  const SizedBox(height: 4),
                  _buildLegendItem(Colors.orange, 'MEDIUM'),
                  const SizedBox(height: 4),
                  _buildLegendItem(const Color(0xFF00BFA5), 'LOW'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip({
    required String label,
    required IconData icon,
    required bool isSelected,
    required Color color,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? color : Colors.white,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.1),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected ? Colors.white : color,
              size: 16,
            ),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? Colors.white : color,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLegendItem(Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 10)),
      ],
    );
  }
}
