import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../core/providers/auth_provider.dart';
import '../report/report_screen.dart';

class HomeDashboard extends ConsumerStatefulWidget {
  const HomeDashboard({super.key});

  @override
  ConsumerState<HomeDashboard> createState() => _HomeDashboardState();
}

class _HomeDashboardState extends ConsumerState<HomeDashboard> {
  List<dynamic> _scans = [];
  List<dynamic> _reports = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  String _safeString(dynamic value, [String fallback = '']) {
    if (value == null) return fallback;
    if (value is String) return value;
    if (value is Map) {
      return value['name']?.toString() ??
          value['code']?.toString() ??
          fallback;
    }
    return value.toString();
  }

  Future<void> _fetchData() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    final session = ref.read(authSessionProvider).value;
    if (session == null || !session.isAuthenticated) {
      if (mounted) setState(() => _loading = false);
      return;
    }
    final dio = ref.read(dioProvider);
    final base = session.serverUrl!;
    final headers = {'Authorization': 'Bearer ${session.accessToken}'};

    try {
      final results = await Future.wait([
        dio.get('$base/api/v1/scans?limit=5&offset=0',
            options: Options(headers: headers)),
        dio.get('$base/api/v1/reports?limit=5&offset=0',
            options: Options(headers: headers)),
      ]);
      if (mounted) {
        final scanData = results[0].data;
        final reportData = results[1].data;
        setState(() {
          _scans = scanData is Map ? (scanData['items'] ?? []) : [];
          _reports = reportData is Map ? (reportData['items'] ?? []) : [];
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _loading = false;
        });
      }
    }
  }

  String _userInitial(String? name) {
    if (name == null || name.isEmpty) return '?';
    return name[0].toUpperCase();
  }

  String _formatDate(dynamic value) {
    if (value == null) return '';
    final str = value.toString();
    if (str.isEmpty) return '';
    try {
      final dt = DateTime.parse(str);
      return DateFormat('dd MMM, HH:mm').format(dt);
    } catch (_) {
      return str;
    }
  }

  String _categoryLabel(dynamic value) {
    final str = _safeString(value);
    if (str.isEmpty) return '';
    return str.replaceAll('_', ' ');
  }

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);

    final session = ref.watch(authSessionProvider).value;
    final userName = session?.name ?? 'User';

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF8F9FA),
        elevation: 0,
        title: Row(
          children: [
            CircleAvatar(
              radius: 20,
              backgroundColor: primaryGreen,
              child: Text(
                _userInitial(userName),
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Halo,',
                  style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                ),
                Text(
                  userName,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: primaryGreen,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
      body: RefreshIndicator(
        onRefresh: _fetchData,
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 16,
                crossAxisSpacing: 16,
                childAspectRatio: 1.1,
                children: [
                  _buildGridItem(
                    icon: Icons.qr_code_scanner,
                    iconBg: const Color(0xFFE8F5E9),
                    iconColor: primaryGreen,
                    title: 'Scan Sampah',
                    onTap: () => context.push('/scan'),
                  ),
                  _buildGridItem(
                    icon: Icons.map_outlined,
                    iconBg: const Color(0xFFE3F2FD),
                    iconColor: Colors.blue,
                    title: 'Peta Sampah',
                    onTap: () => context.push('/map'),
                  ),
                  _buildGridItem(
                    icon: Icons.school_outlined,
                    iconBg: const Color(0xFFFFEBEE),
                    iconColor: Colors.redAccent,
                    title: 'Edukasi',
                    onTap: () => context.push('/knowledge'),
                  ),
                  _buildGridItem(
                    icon: Icons.history,
                    iconBg: const Color(0xFFECEFF1),
                    iconColor: Colors.blueGrey,
                    title: 'Aktivitas',
                    onTap: () => context.push('/activity'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              // Laporkan Sampah prominent button
              GestureDetector(
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const ReportScreen(),
                    ),
                  );
                },
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF1E3F28), Color(0xFF2E7D32)],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF1E3F28).withValues(alpha: 0.3),
                        blurRadius: 8,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.2),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.report_outlined,
                          color: Colors.white,
                          size: 24,
                        ),
                      ),
                      const SizedBox(width: 14),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Laporkan Sampah',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 16,
                              ),
                            ),
                            SizedBox(height: 2),
                            Text(
                              'Foto & laporkan tumpukan sampah di lingkunganmu',
                              style: TextStyle(
                                color: Colors.white70,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Icon(
                        Icons.arrow_forward_ios,
                        color: Colors.white70,
                        size: 16,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Aktivitas Terkini',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  TextButton(
                    onPressed: () => context.push('/activity'),
                    child: const Text(
                      'Lihat Semua',
                      style: TextStyle(
                        color: primaryGreen,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (_loading)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(40),
                    child: CircularProgressIndicator(),
                  ),
                )
              else if (_error != null)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(32),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    children: [
                      Icon(Icons.error_outline,
                          size: 48, color: Colors.red[300]),
                      const SizedBox(height: 12),
                      Text(
                        'Gagal memuat data',
                        style:
                            TextStyle(color: Colors.grey[500], fontSize: 14),
                      ),
                      const SizedBox(height: 8),
                      TextButton(
                        onPressed: _fetchData,
                        child: const Text('Coba Lagi'),
                      ),
                    ],
                  ),
                )
              else if (_scans.isEmpty && _reports.isEmpty)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(32),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    children: [
                      Icon(Icons.eco_outlined,
                          size: 48, color: Colors.grey[300]),
                      const SizedBox(height: 12),
                      Text(
                        'Belum ada aktivitas',
                        style:
                            TextStyle(color: Colors.grey[500], fontSize: 14),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Mulai scan atau lapor sampah',
                        style:
                            TextStyle(color: Colors.grey[400], fontSize: 12),
                      ),
                    ],
                  ),
                )
              else ...[
                ..._scans.map((scan) {
                  final cat = scan is Map
                      ? (scan['confirmed_category'] ??
                          scan['predicted_category'])
                      : null;
                  return _activityTile(
                    icon: Icons.qr_code_scanner,
                    title: _categoryLabel(cat).isEmpty
                        ? 'Scan Sampah'
                        : _categoryLabel(cat),
                    subtitle: 'Scan sampah',
                    time: _formatDate(
                        scan is Map ? scan['created_at'] : null),
                    status: scan is Map
                        ? scan['recommendation_status']?.toString()
                        : null,
                  );
                }),
                ..._reports.map((report) {
                  return _activityTile(
                    icon: Icons.report_outlined,
                    title: _safeString(
                                report is Map ? report['waste_volume'] : null)
                            .isEmpty
                        ? 'Laporan Sampah'
                        : _safeString(
                            report is Map ? report['waste_volume'] : null),
                    subtitle: _safeString(
                        report is Map ? report['address'] : null,
                        'Laporan sampah'),
                    time: _formatDate(
                        report is Map ? report['created_at'] : null),
                    status: report is Map
                        ? report['status']?.toString()
                        : null,
                  );
                }),
              ],
              const SizedBox(height: 80),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildGridItem({
    required IconData icon,
    required Color iconBg,
    required Color iconColor,
    required String title,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.grey.withValues(alpha: 0.1)),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: iconBg, shape: BoxShape.circle),
              child: Icon(icon, color: iconColor, size: 28),
            ),
            const SizedBox(height: 16),
            Text(
              title,
              style:
                  const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }

  Widget _activityTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required String time,
    String? status,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: const BoxDecoration(
              color: Color(0xFFE8F5E9),
              shape: BoxShape.circle,
            ),
            child:
                Icon(icon, color: const Color(0xFF1E3F28), size: 20),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                      fontWeight: FontWeight.w600, fontSize: 14),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style:
                      TextStyle(color: Colors.grey[500], fontSize: 12),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                time,
                style:
                    TextStyle(color: Colors.grey[400], fontSize: 11),
              ),
              if (status != null && status.isNotEmpty) ...[
                const SizedBox(height: 4),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    status,
                    style: TextStyle(
                        color: Colors.grey[600], fontSize: 10),
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}
