import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers/auth_provider.dart';
import '../../core/widgets/location_picker.dart';
import 'data/admin_repository.dart';

const _facilityTypes = [
  'BANK_SAMPAH',
  'TPS3R',
  'COLLECTOR',
  'RECYCLING_FACILITY',
  'SPECIAL_WASTE_FACILITY',
];

const _accessScopes = ['PUBLIC', 'RESTRICTED', 'UNKNOWN'];

String _accessScopeLabel(String scope) {
  switch (scope) {
    case 'PUBLIC':
      return 'Publik';
    case 'RESTRICTED':
      return 'Terbatas';
    case 'UNKNOWN':
      return 'Tidak Diketahui';
    default:
      return scope;
  }
}

const _categories = [
  'PLASTIC',
  'PAPER_CARDBOARD',
  'GLASS',
  'METAL',
  'ORGANIC',
  'TEXTILE',
  'ELECTRONIC_SPECIAL',
  'RESIDUAL_MIXED',
];

class AdminFacilitiesScreen extends ConsumerStatefulWidget {
  const AdminFacilitiesScreen({super.key});

  @override
  ConsumerState<AdminFacilitiesScreen> createState() =>
      _AdminFacilitiesScreenState();
}

class _AdminFacilitiesScreenState
    extends ConsumerState<AdminFacilitiesScreen> {
  bool _loading = true;
  List<dynamic> _facilities = [];
  static const _limit = 50;
  final int _offset = 0;

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
      final data = await _repo().listFacilities(
        accessToken: _token,
        limit: _limit,
        offset: _offset,
      );
      setState(() {
        _facilities = data['items'] ?? [];
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Gagal memuat fasilitas: $e')),
        );
      }
    }
  }

  String _facilityTypeLabel(String type) {
    switch (type) {
      case 'BANK_SAMPAH':
        return 'Bank Sampah';
      case 'TPS3R':
        return 'TPS3R';
      case 'COLLECTOR':
        return 'Pengumpul';
      case 'RECYCLING_FACILITY':
        return 'Daur Ulang';
      case 'SPECIAL_WASTE_FACILITY':
        return 'Limbah Khusus';
      default:
        return type;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Fasilitas',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        automaticallyImplyLeading: false,
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFF1E3F28),
        foregroundColor: Colors.white,
        onPressed: () => _showForm(null),
        child: const Icon(Icons.add),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _facilities.isEmpty
              ? const Center(child: Text('Tidak ada fasilitas'))
              : RefreshIndicator(
                  onRefresh: _fetch,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _facilities.length,
                    itemBuilder: (ctx, i) => _facilityTile(_facilities[i]),
                  ),
                ),
    );
  }

  Widget _facilityTile(Map<String, dynamic> facility) {
    final verified = facility['verified'] == true;
    final isActive = facility['is_active'] != false;
    final type = facility['facility_type'] ?? '';
    final name = facility['name'] ?? '';
    final addr = facility['address'] ?? '';

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        contentPadding: const EdgeInsets.all(14),
        title: Row(
          children: [
            Expanded(
              child: Text(
                name,
                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            if (verified)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.green.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text(
                  'Verified',
                  style: TextStyle(
                      color: Colors.green,
                      fontSize: 10,
                      fontWeight: FontWeight.w600),
                ),
              ),
            if (!isActive)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                margin: const EdgeInsets.only(left: 4),
                decoration: BoxDecoration(
                  color: Colors.red.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text(
                  'Nonaktif',
                  style: TextStyle(
                      color: Colors.red,
                      fontSize: 10,
                      fontWeight: FontWeight.w600),
                ),
              ),
          ],
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(
              _facilityTypeLabel(type),
              style: TextStyle(color: Colors.grey[600], fontSize: 12),
            ),
            const SizedBox(height: 2),
            Text(
              addr,
              style: TextStyle(color: Colors.grey[500], fontSize: 12),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
        trailing: PopupMenuButton<String>(
          onSelected: (value) {
            if (value == 'edit') _showForm(facility);
            if (value == 'delete') _confirmDelete(facility);
          },
          itemBuilder: (_) => [
            const PopupMenuItem(value: 'edit', child: Text('Edit')),
            const PopupMenuItem(value: 'delete', child: Text('Hapus')),
          ],
        ),
      ),
    );
  }

  void _confirmDelete(Map<String, dynamic> facility) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Hapus Fasilitas'),
        content: Text('Hapus "${facility['name']}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Batal'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await _repo().deleteFacility(
                  facilityId: facility['id'],
                  accessToken: _token,
                );
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Fasilitas dihapus')),
                  );
                  _fetch();
                }
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Gagal menghapus: $e')),
                  );
                }
              }
            },
            child: const Text('Hapus', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  void _showForm(Map<String, dynamic>? existing) {
    final isEdit = existing != null;
    final nameCtrl =
        TextEditingController(text: existing?['name'] ?? '');
    final addrCtrl =
        TextEditingController(text: existing?['address'] ?? '');
    final phoneCtrl =
        TextEditingController(text: existing?['phone'] ?? '');
    final latCtrl = TextEditingController(
        text: existing?['latitude']?.toString() ?? '');
    final lngCtrl = TextEditingController(
        text: existing?['longitude']?.toString() ?? '');
    final sourceCtrl =
        TextEditingController(text: existing?['source'] ?? '');
    String facilityType = existing?['facility_type'] ?? _facilityTypes.first;
    bool verified = existing?['verified'] ?? false;
    String accessScope = existing?['access_scope'] ?? 'PUBLIC';
    List<String> selectedCats =
        (existing?['accepted_categories'] as List<dynamic>?)
                ?.map((e) => e.toString())
                .toList() ??
            [];

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) => Padding(
          padding: EdgeInsets.only(
            left: 20,
            right: 20,
            top: 20,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
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
                Text(
                  isEdit ? 'Edit Fasilitas' : 'Tambah Fasilitas',
                  style: const TextStyle(
                      fontWeight: FontWeight.bold, fontSize: 18),
                ),
                const SizedBox(height: 16),
                _inputField('Nama', nameCtrl),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: facilityType,
                  decoration: _inputDecoration('Tipe'),
                  items: _facilityTypes
                      .map((t) => DropdownMenuItem(
                            value: t,
                            child: Text(_facilityTypeLabel(t)),
                          ))
                      .toList(),
                  onChanged: (v) => setModalState(() => facilityType = v!),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: accessScope,
                  decoration: _inputDecoration('Visibilitas'),
                  items: _accessScopes
                      .map((s) => DropdownMenuItem(
                            value: s,
                            child: Text(_accessScopeLabel(s)),
                          ))
                      .toList(),
                  onChanged: (v) => setModalState(() => accessScope = v!),
                ),
                const SizedBox(height: 12),
                _inputField('Alamat', addrCtrl),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                        child: _inputField('Latitude', latCtrl, isNum: true)),
                    const SizedBox(width: 12),
                    Expanded(
                        child: _inputField('Longitude', lngCtrl, isNum: true)),
                    const SizedBox(width: 8),
                    IconButton(
                      onPressed: () async {
                        final result = await Navigator.push<LocationResult>(
                          context,
                          MaterialPageRoute(
                            builder: (_) => LocationPicker(
                              initialLat: double.tryParse(latCtrl.text) ?? -6.9666,
                              initialLng: double.tryParse(lngCtrl.text) ?? 110.4196,
                            ),
                          ),
                        );
                        if (result != null) {
                          setModalState(() {
                            latCtrl.text = result.latitude.toString();
                            lngCtrl.text = result.longitude.toString();
                            addrCtrl.text = result.address;
                          });
                        }
                      },
                      icon: const Icon(Icons.map, color: Color(0xFF1E3F28)),
                      tooltip: 'Cari di Peta',
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                _inputField('Telepon', phoneCtrl),
                const SizedBox(height: 12),
                _inputField('Sumber', sourceCtrl),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: _categories.map((cat) {
                    final selected = selectedCats.contains(cat);
                    return FilterChip(
                      label: Text(cat.replaceAll('_', ' '),
                          style: const TextStyle(fontSize: 11)),
                      selected: selected,
                      onSelected: (val) {
                        setModalState(() {
                          if (val) {
                            selectedCats.add(cat);
                          } else {
                            selectedCats.remove(cat);
                          }
                        });
                      },
                      selectedColor: const Color(0xFF1E3F28),
                      labelStyle: TextStyle(
                        color: selected ? Colors.white : Colors.black87,
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 12),
                SwitchListTile(
                  title: const Text('Verified'),
                  value: verified,
                  onChanged: (v) => setModalState(() => verified = v),
                  contentPadding: EdgeInsets.zero,
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () async {
                      final data = {
                        'name': nameCtrl.text.trim(),
                        'facility_type': facilityType,
                        'access_scope': accessScope,
                        'address': addrCtrl.text.trim(),
                        'latitude': double.tryParse(latCtrl.text) ?? 0,
                        'longitude': double.tryParse(lngCtrl.text) ?? 0,
                        'phone': phoneCtrl.text.trim().isEmpty
                            ? null
                            : phoneCtrl.text.trim(),
                        'source': sourceCtrl.text.trim(),
                        'verified': verified,
                        'accepted_categories': selectedCats,
                      };
                      Navigator.pop(ctx);
                      try {
                        if (isEdit) {
                          await _repo().updateFacility(
                            facilityId: existing['id'],
                            accessToken: _token,
                            data: data,
                          );
                        } else {
                          await _repo().createFacility(
                            accessToken: _token,
                            data: data,
                          );
                        }
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(isEdit
                                  ? 'Fasilitas diperbarui'
                                  : 'Fasilitas ditambahkan'),
                            ),
                          );
                          _fetch();
                        }
                      } catch (e) {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Gagal: $e')),
                          );
                        }
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1E3F28),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                    child: Text(isEdit ? 'Simpan' : 'Tambah'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _inputField(String label, TextEditingController ctrl,
      {bool isNum = false}) {
    return TextField(
      controller: ctrl,
      keyboardType: isNum ? TextInputType.numberWithOptions(decimal: true) : null,
      decoration: InputDecoration(
        labelText: label,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        isDense: true,
      ),
    );
  }

  InputDecoration _inputDecoration(String label) {
    return InputDecoration(
      labelText: label,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      isDense: true,
    );
  }
}
