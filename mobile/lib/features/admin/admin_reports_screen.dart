import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/providers/auth_provider.dart';
import 'data/admin_repository.dart';

class AdminReportsScreen extends ConsumerStatefulWidget {
  const AdminReportsScreen({super.key});

  @override
  ConsumerState<AdminReportsScreen> createState() =>
      _AdminReportsScreenState();
}

class _AdminReportsScreenState extends ConsumerState<AdminReportsScreen> {
  String? _selectedStatus;
  bool _loading = true;
  List<dynamic> _reports = [];
  int _offset = 0;
  static const _limit = 50;

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

  String get _token =>
      ref.read(authSessionProvider).value!.accessToken!;

  Future<void> _fetch() async {
    setState(() => _loading = true);
    try {
      final data = await _repo().listReports(
        accessToken: _token,
        status: _selectedStatus,
        limit: _limit,
        offset: _offset,
      );
      setState(() {
        _reports = data['items'] ?? [];
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Gagal memuat laporan: $e')),
        );
      }
    }
  }

  void _onFilterChanged(String? status) {
    setState(() {
      _selectedStatus = status;
      _offset = 0;
    });
    _fetch();
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
        return Colors.green;
      default:
        return Colors.grey;
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

  String _statusLabel(String status) {
    switch (status) {
      case 'REPORTED':
        return 'Dilaporkan';
      case 'VERIFIED':
        return 'Terverifikasi';
      case 'IN_PROGRESS':
        return 'Diproses';
      case 'RESOLVED':
        return 'Selesai';
      default:
        return status;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Laporan',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        automaticallyImplyLeading: false,
      ),
      body: Column(
        children: [
          SizedBox(
            height: 52,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              children: [
                _filterChip('Semua', null),
                _filterChip('Dilaporkan', 'REPORTED'),
                _filterChip('Terverifikasi', 'VERIFIED'),
                _filterChip('Diproses', 'IN_PROGRESS'),
                _filterChip('Selesai', 'RESOLVED'),
              ],
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _reports.isEmpty
                    ? const Center(child: Text('Tidak ada laporan'))
                    : RefreshIndicator(
                        onRefresh: _fetch,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(12),
                          itemCount: _reports.length,
                          itemBuilder: (ctx, i) =>
                              _reportTile(_reports[i]),
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _filterChip(String label, String? status) {
    final selected = _selectedStatus == status;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text(label),
        selected: selected,
        onSelected: (_) => _onFilterChanged(status),
        selectedColor: const Color(0xFF1E3F28),
        labelStyle: TextStyle(
          color: selected ? Colors.white : Colors.black87,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  Widget _reportTile(Map<String, dynamic> report) {
    final status = report['status'] ?? 'REPORTED';
    final riskLevel = report['risk_level'] as String?;
    final riskScore = report['risk_score'];
    final volume = report['waste_volume'] ?? '';
    final addr = report['address'] ?? '';
    final confirmCount = report['confirmation_count'] ?? 0;
    final createdAt = report['created_at'] ?? '';
    String dateStr = '';
    if (createdAt is String && createdAt.isNotEmpty) {
      try {
        dateStr = DateFormat('dd MMM yyyy, HH:mm')
            .format(DateTime.parse(createdAt));
      } catch (_) {
        dateStr = createdAt;
      }
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => _showReportDetail(report),
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
                      color: _statusColor(status).withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      _statusLabel(status),
                      style: TextStyle(
                        color: _statusColor(status),
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  if (riskLevel != null)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: _riskColor(riskLevel).withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        '$riskLevel ${riskScore != null ? '($riskScore)' : ''}',
                        style: TextStyle(
                          color: _riskColor(riskLevel),
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  const Spacer(),
                  Icon(Icons.chevron_right, color: Colors.grey[400], size: 20),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                addr.isNotEmpty ? addr : 'Lokasi tidak diketahui',
                style: const TextStyle(
                    fontWeight: FontWeight.w600, fontSize: 14),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 6),
              Row(
                children: [
                  Icon(Icons.delete_outline, size: 14, color: Colors.grey[500]),
                  const SizedBox(width: 4),
                  Text(volume, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                  const SizedBox(width: 12),
                  Icon(Icons.people_outline, size: 14, color: Colors.grey[500]),
                  const SizedBox(width: 4),
                  Text('$confirmCount konfirmasi',
                      style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                  const Spacer(),
                  Text(dateStr,
                      style: TextStyle(fontSize: 11, color: Colors.grey[400])),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showReportDetail(Map<String, dynamic> report) {
    final status = report['status'] ?? 'REPORTED';
    final nextStatus = _nextStatus(status);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (ctx, scrollController) => SingleChildScrollView(
          controller: scrollController,
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: _statusColor(status).withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      _statusLabel(status),
                      style: TextStyle(
                        color: _statusColor(status),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              _detailRow('Alamat', report['address'] ?? '-'),
              _detailRow('Volume', report['waste_volume'] ?? '-'),
              _detailRow('Genangan Air',
                  report['standing_water'] == true ? 'Ya' : 'Tidak'),
              _detailRow('Saluran Tersumbat',
                  report['drainage_blockage'] == true ? 'Ya' : 'Tidak'),
              _detailRow('Skor Risiko',
                  '${report['risk_score'] ?? '-'} (${report['risk_level'] ?? '-'})'),
              _detailRow('Konfirmasi',
                  '${report['confirmation_count'] ?? 0} orang'),
              const SizedBox(height: 20),
              if (nextStatus != null)
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () =>
                        _changeStatus(report['id'], nextStatus),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1E3F28),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                    child: Text(
                      'Ubah ke ${_statusLabel(nextStatus)}',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  String? _nextStatus(String current) {
    switch (current) {
      case 'REPORTED':
        return 'VERIFIED';
      case 'VERIFIED':
        return 'IN_PROGRESS';
      case 'IN_PROGRESS':
        return 'RESOLVED';
      default:
        return null;
    }
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 130,
            child: Text(label,
                style: TextStyle(color: Colors.grey[600], fontSize: 13)),
          ),
          Expanded(
            child: Text(value,
                style: const TextStyle(
                    fontWeight: FontWeight.w500, fontSize: 13)),
          ),
        ],
      ),
    );
  }

  Future<void> _changeStatus(String reportId, String newStatus) async {
    Navigator.pop(context);
    try {
      await _repo().changeReportStatus(
        reportId: reportId,
        status: newStatus,
        accessToken: _token,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Status diubah ke ${_statusLabel(newStatus)}')),
        );
        _fetch();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Gagal mengubah status: $e')),
        );
      }
    }
  }
}
