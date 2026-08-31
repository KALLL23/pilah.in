import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/providers/auth_provider.dart';

enum _FilterType { all, scan, report }

class ActivityScreen extends ConsumerStatefulWidget {
  const ActivityScreen({super.key});

  @override
  ConsumerState<ActivityScreen> createState() => _ActivityScreenState();
}

class _ActivityScreenState extends ConsumerState<ActivityScreen> {
  _FilterType _filter = _FilterType.all;
  List<Map<String, dynamic>> _scans = [];
  List<Map<String, dynamic>> _reports = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchData();
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
        dio.get('$base/api/v1/scans?limit=50&offset=0',
            options: Options(headers: headers)),
        dio.get('$base/api/v1/reports?limit=50&offset=0',
            options: Options(headers: headers)),
      ]);

      if (mounted) {
        final scanData = results[0].data;
        final reportData = results[1].data;
        setState(() {
          _scans = (scanData is Map ? (scanData['items'] ?? []) : [])
              .map<Map<String, dynamic>>((e) => Map<String, dynamic>.from(e as Map))
              .toList();
          _reports = (reportData is Map ? (reportData['items'] ?? []) : [])
              .map<Map<String, dynamic>>((e) => Map<String, dynamic>.from(e as Map))
              .toList();
          _loading = false;
        });
      }
    } on DioException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message ?? 'Gagal memuat data aktivitas';
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Error: $e';
          _loading = false;
        });
      }
    }
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
    if (str.isEmpty) return '-';
    return str.replaceAll('_', ' ');
  }

  List<_ActivityItem> _getFilteredItems() {
    final items = <_ActivityItem>[];

    if (_filter == _FilterType.all || _filter == _FilterType.scan) {
      for (final scan in _scans) {
        final cat = scan['confirmed_category'] ?? scan['predicted_category'];
        items.add(_ActivityItem(
          type: _ActivityItemType.scan,
          title: _categoryLabel(cat),
          subtitle: 'Scan sampah',
          time: _formatDate(scan['created_at']),
          raw: scan,
        ));
      }
    }

    if (_filter == _FilterType.all || _filter == _FilterType.report) {
      for (final report in _reports) {
        final volume = _safeString(report['waste_volume']);
        final status = _safeString(report['status']);
        items.add(_ActivityItem(
          type: _ActivityItemType.report,
          title: 'Laporan ${volume.isNotEmpty ? volume : "Sampah"}',
          subtitle: _safeString(report['address'], 'Laporan sampah'),
          time: _formatDate(report['created_at']),
          status: status,
          raw: report,
        ));
      }
    }

    items.sort((a, b) {
      final aTime = a.raw['created_at']?.toString() ?? '';
      final bTime = b.raw['created_at']?.toString() ?? '';
      return bTime.compareTo(aTime);
    });

    return items;
  }

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF8F9FA),
        elevation: 0,
        title: const Text(
          'Riwayat Aktivitas',
          style: TextStyle(
            color: primaryGreen,
            fontWeight: FontWeight.bold,
            fontSize: 20,
          ),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: primaryGreen),
          onPressed: () {
            if (Navigator.canPop(context)) {
              Navigator.pop(context);
            }
          },
        ),
      ),
      body: Column(
        children: [
          // Filter chips
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: Row(
              children: [
                _buildFilterChip('Semua', _FilterType.all),
                const SizedBox(width: 12),
                _buildFilterChip('Scan', _FilterType.scan),
                const SizedBox(width: 12),
                _buildFilterChip('Laporan', _FilterType.report),
              ],
            ),
          ),
          const SizedBox(height: 8),

          // Content
          Expanded(
            child: _loading
                ? const Center(
                    child: CircularProgressIndicator(color: primaryGreen),
                  )
                : _error != null
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(24),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.error_outline,
                                  size: 48, color: Colors.grey[400]),
                              const SizedBox(height: 16),
                              Text(
                                _error!,
                                style: TextStyle(
                                    color: Colors.grey[600], fontSize: 14),
                                textAlign: TextAlign.center,
                              ),
                              const SizedBox(height: 16),
                              ElevatedButton(
                                onPressed: _fetchData,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: primaryGreen,
                                ),
                                child: const Text('Coba Lagi',
                                    style: TextStyle(color: Colors.white)),
                              ),
                            ],
                          ),
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _fetchData,
                        child: _buildActivityList(),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildActivityList() {
    const primaryGreen = Color(0xFF1E3F28);
    final items = _getFilteredItems();

    if (items.isEmpty) {
      return ListView(
        children: [
          const SizedBox(height: 80),
          Center(
            child: Column(
              children: [
                Icon(Icons.history, size: 48, color: Colors.grey[300]),
                const SizedBox(height: 16),
                Text(
                  'Belum ada aktivitas',
                  style: TextStyle(color: Colors.grey[500], fontSize: 14),
                ),
                const SizedBox(height: 4),
                Text(
                  'Mulai scan atau laporkan sampah',
                  style: TextStyle(color: Colors.grey[400], fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        final isScan = item.type == _ActivityItemType.scan;

        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.withValues(alpha: 0.15)),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: isScan
                      ? const Color(0xFFE8F5E9)
                      : const Color(0xFFE3F2FD),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  isScan ? Icons.qr_code_scanner : Icons.report_outlined,
                  color: isScan ? primaryGreen : Colors.blue,
                  size: 20,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.title,
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      item.subtitle,
                      style: TextStyle(color: Colors.grey[500], fontSize: 12),
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
                    item.time,
                    style: TextStyle(color: Colors.grey[400], fontSize: 11),
                  ),
                  if (item.status != null && item.status!.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: _statusColor(item.status!).withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        _statusText(item.status!),
                        style: TextStyle(
                          color: _statusColor(item.status!),
                          fontSize: 10,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildFilterChip(String label, _FilterType type) {
    const primaryGreen = Color(0xFF1E3F28);
    final isSelected = _filter == type;

    return GestureDetector(
      onTap: () => setState(() => _filter = type),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? primaryGreen : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? primaryGreen : Colors.grey[300]!,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.grey[700],
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'REPORTED':
        return Colors.orange;
      case 'VERIFIED':
        return Colors.blue;
      case 'IN_PROGRESS':
        return Colors.purple;
      case 'RESOLVED':
        return const Color(0xFF00BFA5);
      default:
        return Colors.grey;
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
}

enum _ActivityItemType { scan, report }

class _ActivityItem {
  final _ActivityItemType type;
  final String title;
  final String subtitle;
  final String time;
  final String? status;
  final Map<String, dynamic> raw;

  _ActivityItem({
    required this.type,
    required this.title,
    required this.subtitle,
    required this.time,
    this.status,
    required this.raw,
  });
}
