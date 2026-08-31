import 'dart:async';
import 'dart:ui' as ui;
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
  bool _showWaterways = true;
  bool _showPublicFacilities = true;

  List<Map<String, dynamic>> _reports = [];
  List<Map<String, dynamic>> _facilities = [];
  List<Map<String, dynamic>> _hotspots = [];
  List<Map<String, dynamic>> _waterways = [];
  List<Map<String, dynamic>> _publicFacilities = [];

  final Set<Marker> _markers = {};
  final Set<Polyline> _polylines = {};

  BitmapDescriptor? _markerExclamation;
  BitmapDescriptor? _markerBankSampah;
  BitmapDescriptor? _markerTps3r;
  BitmapDescriptor? _markerRecycling;
  BitmapDescriptor? _markerHotspot;
  BitmapDescriptor? _markerPublic;

  bool _isLoading = true;
  bool _markersReady = false;
  String? _error;

  static const double _defaultLat = -6.9666;
  static const double _defaultLng = 110.4196;
  static const double _defaultZoom = 12.0;

  @override
  void initState() {
    super.initState();
    _initMarkers();
  }

  Future<void> _initMarkers() async {
    _markerExclamation = await _createIconMarker(
      color: const Color(0xFFD32F2F),
      icon: Icons.report_problem,
      size: 50,
    );
    _markerBankSampah = await _createIconMarker(
      color: const Color(0xFF2E7D32),
      icon: Icons.recycling,
      size: 50,
    );
    _markerTps3r = await _createIconMarker(
      color: const Color(0xFF1565C0),
      icon: Icons.delete_outline,
      size: 50,
    );
    _markerRecycling = await _createIconMarker(
      color: const Color(0xFF6A1B9A),
      icon: Icons.autorenew,
      size: 50,
    );
    _markerHotspot = await _createIconMarker(
      color: const Color(0xFFE65100),
      icon: Icons.local_fire_department,
      size: 50,
    );
    _markerPublic = await _createIconMarker(
      color: const Color(0xFF00838F),
      icon: Icons.apartment,
      size: 50,
    );

    if (mounted) {
      setState(() => _markersReady = true);
      _loadData();
    }
  }

  Future<BitmapDescriptor> _createIconMarker({
    required Color color,
    required IconData icon,
    required int size,
  }) async {
    final recorder = ui.PictureRecorder();
    final canvas = Canvas(recorder);
    final paint = Paint()..style = PaintingStyle.fill;

    final center = Offset(size / 2, size / 2);
    final radius = size / 2.0;

    canvas.drawCircle(center, radius, paint..color = color);

    final shadowPaint = Paint()
      ..color = Colors.black.withValues(alpha: 0.2)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center + const Offset(0, 2), radius, shadowPaint);
    canvas.drawCircle(center, radius, paint..color = color);

    final textPainter = TextPainter(textDirection: TextDirection.ltr);
    textPainter.text = TextSpan(
      text: String.fromCharCode(icon.codePoint),
      style: TextStyle(
        fontSize: size * 0.45,
        color: Colors.white,
        fontFamily: icon.fontFamily,
      ),
    );
    textPainter.layout();
    final textOffset = Offset(
      center.dx - textPainter.width / 2,
      center.dy - textPainter.height / 2,
    );
    textPainter.paint(canvas, textOffset);

    final picture = recorder.endRecording();
    final image = await picture.toImage(size, size);
    final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
    final bytes = byteData!.buffer.asUint8List();

    return BitmapDescriptor.bytes(bytes);
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
        _repository.getWaterways(accessToken: authSession.accessToken!),
        _repository.getPublicFacilities(accessToken: authSession.accessToken!),
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
          _waterways = (results[3]['features'] as List<dynamic>?)
                  ?.map((e) => Map<String, dynamic>.from(e as Map))
                  .toList() ??
              [];
          _publicFacilities = (results[4]['features'] as List<dynamic>?)
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
    _polylines.clear();

    if (_showReports) _addReportMarkers();
    if (_showFacilities) _addFacilityMarkers();
    if (_showHotspots) _addHotspotMarkers();
    if (_showWaterways) _addWaterwayPolylines();
    if (_showPublicFacilities) _addPublicFacilityMarkers();

    setState(() {});
  }

  void _addReportMarkers() {
    for (final feature in _reports) {
      final geometry = feature['geometry'] as Map<String, dynamic>?;
      final properties = feature['properties'] as Map<String, dynamic>?;
      if (geometry == null || properties == null) continue;
      final coords = geometry['coordinates'] as List<dynamic>?;
      if (coords == null || coords.length < 2) continue;

      _markers.add(
        Marker(
          markerId: MarkerId('report_${feature['id']}'),
          position: LatLng(coords[1] as double, coords[0] as double),
          icon: _markerExclamation ?? BitmapDescriptor.defaultMarker,
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
      final coords = geometry['coordinates'] as List<dynamic>?;
      if (coords == null || coords.length < 2) continue;

      final facilityType = properties['facility_type'] as String? ?? 'OTHER';
      BitmapDescriptor icon;
      switch (facilityType) {
        case 'BANK_SAMPAH':
          icon = _markerBankSampah ?? BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen);
          break;
        case 'TPS3R':
          icon = _markerTps3r ?? BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue);
          break;
        case 'RECYCLING_FACILITY':
          icon = _markerRecycling ?? BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueViolet);
          break;
        default:
          icon = BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen);
      }

      _markers.add(
        Marker(
          markerId: MarkerId('facility_${feature['id']}'),
          position: LatLng(coords[1] as double, coords[0] as double),
          icon: icon,
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
      final coords = geometry['coordinates'] as List<dynamic>?;
      if (coords == null || coords.length < 2) continue;

      _markers.add(
        Marker(
          markerId: MarkerId('hotspot_${feature['id']}'),
          position: LatLng(coords[1] as double, coords[0] as double),
          icon: _markerHotspot ?? BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueOrange),
          onTap: () => _showDetailPopup('hotspot', {
            'type': 'hotspot',
            'id': feature['id'],
            ...properties,
          }),
        ),
      );
    }
  }

  void _addWaterwayPolylines() {
    int idx = 0;
    for (final feature in _waterways) {
      final geometry = feature['geometry'] as Map<String, dynamic>?;
      if (geometry == null) continue;

      final coords = geometry['coordinates'] as List<dynamic>?;
      if (coords == null || coords.length < 2) continue;

      final points = coords
          .map((c) => LatLng((c as List<dynamic>)[1] as double, c[0] as double))
          .toList();

      _polylines.add(
        Polyline(
          polylineId: PolylineId('waterway_${feature['id'] ?? idx}'),
          points: points,
          color: const Color(0xFF1E88E5).withValues(alpha: 0.7),
          width: 3,
        ),
      );
      idx++;
    }
  }

  void _addPublicFacilityMarkers() {
    for (final feature in _publicFacilities) {
      final geometry = feature['geometry'] as Map<String, dynamic>?;
      final props = feature['properties'] as Map<String, dynamic>?;
      if (geometry == null || props == null) continue;
      final coords = geometry['coordinates'] as List<dynamic>?;
      if (coords == null || coords.length < 2) continue;

      _markers.add(
        Marker(
          markerId: MarkerId('public_${feature['id']}'),
          position: LatLng(coords[1] as double, coords[0] as double),
          icon: _markerPublic ?? BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueCyan),
          onTap: () => _showDetailPopup('public_facility', {
            'type': 'public_facility',
            'id': feature['id'],
            ...props,
          }),
        ),
      );
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
            if (type == 'report') _buildReportDetail(data),
            if (type == 'facility') _buildFacilityDetail(data),
            if (type == 'hotspot') _buildHotspotDetail(data),
            if (type == 'public_facility') _buildPublicFacilityDetail(data),
          ],
        ),
      ),
    );
  }

  Widget _buildReportDetail(Map<String, dynamic> data) {
    final riskLevel = data['risk_level'] as String? ?? 'LOW';
    final riskScore = (data['risk_score'] as num?)?.toDouble() ?? 0;
    final status = data['status'] as String? ?? '-';
    final riskReasons = (data['risk_reasons'] as List<dynamic>?)?.cast<String>() ?? [];
    final createdAt = data['created_at'] as String? ?? '';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.report_problem, color: Color(0xFFD32F2F), size: 24),
            const SizedBox(width: 8),
            const Expanded(
              child: Text(
                'Laporan Sampah',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1E3F28)),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        _buildDetailRow('Status', _statusText(status)),
        const SizedBox(height: 8),
        Row(
          children: [
            Text('Risk Level: ', style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: _riskColor(riskLevel).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                _riskLevelText(riskLevel),
                style: TextStyle(color: _riskColor(riskLevel), fontSize: 12, fontWeight: FontWeight.w600),
              ),
            ),
            const SizedBox(width: 8),
            Text('Score: ${riskScore.toStringAsFixed(0)}/100', style: const TextStyle(fontSize: 13)),
          ],
        ),
        if (riskReasons.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text('Alasan Risiko:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
          const SizedBox(height: 4),
          ...riskReasons.map((reason) => Padding(
                padding: const EdgeInsets.only(bottom: 2),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber_rounded, color: _riskColor(riskLevel), size: 14),
                    const SizedBox(width: 6),
                    Expanded(child: Text(reason, style: const TextStyle(fontSize: 12))),
                  ],
                ),
              )),
        ],
        if (createdAt.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text('Dibuat: $createdAt', style: TextStyle(color: Colors.grey.shade500, fontSize: 11)),
        ],
      ],
    );
  }

  Widget _buildFacilityDetail(Map<String, dynamic> data) {
    final name = data['name'] as String? ?? '-';
    final facilityType = data['facility_type'] as String? ?? '-';
    final address = data['address'] as String? ?? '-';
    final categories = (data['accepted_categories'] as List<dynamic>?)?.cast<String>() ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.location_city, color: Color(0xFF2E7D32), size: 24),
            const SizedBox(width: 8),
            Expanded(
              child: Text(name, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1E3F28))),
            ),
          ],
        ),
        const SizedBox(height: 12),
        _buildDetailRow('Tipe', _facilityTypeText(facilityType)),
        const SizedBox(height: 8),
        _buildDetailRow('Alamat', address),
        if (categories.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text('Kategori Diterima:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
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
                child: Text(_categoryName(cat), style: const TextStyle(fontSize: 11, color: Color(0xFF1E3F28))),
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
            Icon(Icons.local_fire_department, color: _riskColor(highestRisk), size: 24),
            const SizedBox(width: 8),
            const Expanded(
              child: Text(
                'Hotspot Sampah',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1E3F28)),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        _buildDetailRow('Jumlah Laporan', '$reportCount laporan'),
        const SizedBox(height: 8),
        Row(
          children: [
            Text('Risk Tertinggi: ', style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: _riskColor(highestRisk).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                _riskLevelText(highestRisk),
                style: TextStyle(color: _riskColor(highestRisk), fontSize: 12, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        _buildDetailRow('Rata-rata Score', avgRiskScore.toStringAsFixed(1)),
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

  Widget _buildPublicFacilityDetail(Map<String, dynamic> data) {
    final name = data['name'] as String? ?? '-';
    final kind = data['facility_kind'] as String? ?? '-';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.apartment, color: Color(0xFF00838F), size: 24),
            const SizedBox(width: 8),
            Expanded(
              child: Text(name, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1E3F28))),
            ),
          ],
        ),
        const SizedBox(height: 12),
        _buildDetailRow('Jenis', _facilityKindText(kind)),
      ],
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('$label: ', style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
        Expanded(child: Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500))),
      ],
    );
  }

  Color _riskColor(String level) {
    switch (level) {
      case 'HIGH': return Colors.red;
      case 'MEDIUM': return Colors.orange;
      case 'LOW': return const Color(0xFF00BFA5);
      default: return Colors.grey;
    }
  }

  String _riskLevelText(String level) {
    switch (level) {
      case 'HIGH': return 'TINGGI';
      case 'MEDIUM': return 'SEDANG';
      case 'LOW': return 'RENDAH';
      default: return level;
    }
  }

  String _statusText(String status) {
    switch (status) {
      case 'REPORTED': return 'Dilaporkan';
      case 'VERIFIED': return 'Diverifikasi';
      case 'IN_PROGRESS': return 'Ditangani';
      case 'RESOLVED': return 'Selesai';
      default: return status;
    }
  }

  String _facilityTypeText(String type) {
    switch (type) {
      case 'BANK_SAMPAH': return 'Bank Sampah';
      case 'TPS3R': return 'TPS3R';
      case 'COLLECTOR': return 'Pengumpul';
      case 'RECYCLING_FACILITY': return 'Fasilitas Daur Ulang';
      case 'SPECIAL_WASTE_FACILITY': return 'Fasilitas Sampah Khusus';
      default: return type;
    }
  }

  String _facilityKindText(String kind) {
    switch (kind) {
      case 'health_facility': return 'Fasilitas Kesehatan';
      case 'market': return 'Pasar';
      case 'school': return 'Sekolah / Universitas';
      case 'government': return 'Pemerintahan';
      case 'public_gathering': return 'Tempat Umum';
      case 'transportation': return 'Transportasi';
      default: return kind;
    }
  }

  String _categoryName(String code) {
    switch (code) {
      case 'PLASTIC': return 'Plastik';
      case 'PAPER_CARDBOARD': return 'Kertas';
      case 'GLASS': return 'Kaca';
      case 'METAL': return 'Logam';
      case 'ORGANIC': return 'Organik';
      case 'TEXTILE': return 'Tekstil';
      case 'ELECTRONIC_SPECIAL': return 'Elektronik';
      case 'RESIDUAL_MIXED': return 'Residu';
      default: return code;
    }
  }

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      body: Stack(
        children: [
          if (!_isLoading && _error == null && _markersReady)
            GoogleMap(
              onMapCreated: (_) {},
              initialCameraPosition: const CameraPosition(
                target: LatLng(_defaultLat, _defaultLng),
                zoom: _defaultZoom,
              ),
              markers: _markers,
              polylines: _polylines,
              myLocationEnabled: false,
              zoomControlsEnabled: false,
              mapToolbarEnabled: false,
              compassEnabled: true,
            ),

          if (_isLoading || !_markersReady)
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
                    Text(_error!, style: TextStyle(color: Colors.grey[600], fontSize: 14), textAlign: TextAlign.center),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () {
                        setState(() { _isLoading = true; _error = null; });
                        _loadData();
                      },
                      style: ElevatedButton.styleFrom(backgroundColor: primaryGreen),
                      child: const Text('Coba Lagi', style: TextStyle(color: Colors.white)),
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
                    color: const Color(0xFFD32F2F),
                    onTap: () { setState(() => _showReports = !_showReports); _updateMarkers(); },
                  ),
                  const SizedBox(width: 8),
                  _buildFilterChip(
                    label: 'Bank Sampah',
                    icon: Icons.recycling,
                    isSelected: _showFacilities,
                    color: const Color(0xFF2E7D32),
                    onTap: () { setState(() => _showFacilities = !_showFacilities); _updateMarkers(); },
                  ),
                  const SizedBox(width: 8),
                  _buildFilterChip(
                    label: 'Hotspot',
                    icon: Icons.local_fire_department,
                    isSelected: _showHotspots,
                    color: const Color(0xFFE65100),
                    onTap: () { setState(() => _showHotspots = !_showHotspots); _updateMarkers(); },
                  ),
                  const SizedBox(width: 8),
                  _buildFilterChip(
                    label: 'Saluran Air',
                    icon: Icons.water,
                    isSelected: _showWaterways,
                    color: const Color(0xFF1E88E5),
                    onTap: () { setState(() => _showWaterways = !_showWaterways); _updateMarkers(); },
                  ),
                  const SizedBox(width: 8),
                  _buildFilterChip(
                    label: 'Fasilitas Umum',
                    icon: Icons.apartment,
                    isSelected: _showPublicFacilities,
                    color: const Color(0xFF00838F),
                    onTap: () { setState(() => _showPublicFacilities = !_showPublicFacilities); _updateMarkers(); },
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
                  _buildLegendItem(const Color(0xFFD32F2F), 'Laporan'),
                  const SizedBox(height: 4),
                  _buildLegendItem(const Color(0xFF2E7D32), 'Bank Sampah'),
                  const SizedBox(height: 4),
                  _buildLegendItem(const Color(0xFF1565C0), 'TPS3R'),
                  const SizedBox(height: 4),
                  _buildLegendItem(const Color(0xFF6A1B9A), 'Daur Ulang'),
                  const SizedBox(height: 4),
                  _buildLegendItem(const Color(0xFFE65100), 'Hotspot'),
                  const SizedBox(height: 4),
                  _buildLegendItem(const Color(0xFF1E88E5), 'Saluran Air'),
                  const SizedBox(height: 4),
                  _buildLegendItem(const Color(0xFF00838F), 'Fasilitas Umum'),
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
            Icon(icon, color: isSelected ? Colors.white : color, size: 16),
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
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 10)),
      ],
    );
  }
}
