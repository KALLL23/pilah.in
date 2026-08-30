import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/providers/auth_provider.dart';
import 'data/admin_repository.dart';

class AdminHotspotScreen extends ConsumerStatefulWidget {
  const AdminHotspotScreen({super.key});

  @override
  ConsumerState<AdminHotspotScreen> createState() =>
      _AdminHotspotScreenState();
}

class _AdminHotspotScreenState extends ConsumerState<AdminHotspotScreen> {
  bool _loading = true;
  List<dynamic> _hotspots = [];

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  AdminRepository _repo() {
    final dio = ref.read(dioProvider);
    final session = ref.read(authSessionProvider).value!;
    return AdminRepository(dio, session.serverUrl!);
  }

  String get _token => ref.read(authSessionProvider).value!.accessToken!;

  Future<void> _fetch() async {
    setState(() => _loading = true);
    try {
      final data = await _repo().listHotspots(accessToken: _token);
      final features = data['features'] as List<dynamic>? ?? [];
      setState(() {
        _hotspots = features;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Gagal memuat hotspot: $e')),
        );
      }
    }
  }

  Color _riskColor(String? level) {
    switch (level) {
      case 'HIGH':
        return Colors.red;
      case 'MEDIUM':
        return Colors.orange;
      case 'LOW':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  String _formatDate(String? iso) {
    if (iso == null || iso.isEmpty) return '-';
    try {
      return DateFormat('dd MMM yyyy').format(DateTime.parse(iso));
    } catch (_) {
      return iso;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Hotspot',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        automaticallyImplyLeading: false,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _hotspots.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.map_outlined,
                          size: 48, color: Colors.grey),
                      SizedBox(height: 12),
                      Text('Belum ada hotspot terdeteksi'),
                      SizedBox(height: 4),
                      Text(
                        'Hotspot muncul ketika 3+ laporan aktif dalam radius 50m',
                        style: TextStyle(color: Colors.grey, fontSize: 12),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _fetch,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _hotspots.length,
                    itemBuilder: (ctx, i) =>
                        _hotspotTile(_hotspots[i]),
                  ),
                ),
    );
  }

  Widget _hotspotTile(Map<String, dynamic> feature) {
    final props = feature['properties'] as Map<String, dynamic>? ?? {};
    final clusterId = props['cluster_id'] ?? '-';
    final reportCount = props['report_count'] ?? 0;
    final avgRisk = props['average_risk_score'];
    final highestLevel = props['highest_risk_level'] as String?;
    final firstSeen = props['first_seen'] as String?;
    final lastSeen = props['last_seen'] as String?;

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: _riskColor(highestLevel).withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    highestLevel ?? '-',
                    style: TextStyle(
                      color: _riskColor(highestLevel),
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  'Cluster #$clusterId',
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 12,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                _statItem(Icons.article_outlined, '$reportCount laporan'),
                const SizedBox(width: 16),
                _statItem(Icons.speed, 'Risko: $avgRisk'),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.calendar_today, size: 14, color: Colors.grey[400]),
                const SizedBox(width: 4),
                Text(
                  '${_formatDate(firstSeen)} — ${_formatDate(lastSeen)}',
                  style: TextStyle(fontSize: 11, color: Colors.grey[500]),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _statItem(IconData icon, String text) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: Colors.grey[500]),
        const SizedBox(width: 4),
        Text(text, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
      ],
    );
  }
}
