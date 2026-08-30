import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers/auth_provider.dart';
import 'data/admin_repository.dart';

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

class AdminKnowledgeScreen extends ConsumerStatefulWidget {
  const AdminKnowledgeScreen({super.key});

  @override
  ConsumerState<AdminKnowledgeScreen> createState() =>
      _AdminKnowledgeScreenState();
}

class _AdminKnowledgeScreenState extends ConsumerState<AdminKnowledgeScreen> {
  bool _loading = true;
  List<dynamic> _knowledge = [];
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
      final data = await _repo().listKnowledge(
        accessToken: _token,
        limit: _limit,
        offset: _offset,
      );
      setState(() {
        _knowledge = data['items'] ?? [];
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Gagal memuat knowledge: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Knowledge',
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
          : _knowledge.isEmpty
              ? const Center(child: Text('Tidak ada knowledge'))
              : RefreshIndicator(
                  onRefresh: _fetch,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _knowledge.length,
                    itemBuilder: (ctx, i) => _knowledgeTile(_knowledge[i]),
                  ),
                ),
    );
  }

  Widget _knowledgeTile(Map<String, dynamic> item) {
    final isActive = item['is_active'] != false;
    final category = item['category'] ?? '';
    final content = item['content'] ?? '';
    final source = item['source'] ?? '';
    final scope = item['condition_scope'] as Map<String, dynamic>? ?? {};

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        contentPadding: const EdgeInsets.all(14),
        title: Row(
          children: [
            Expanded(
              child: Text(
                category.replaceAll('_', ' '),
                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: (isActive ? Colors.green : Colors.red)
                    .withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                isActive ? 'Aktif' : 'Nonaktif',
                style: TextStyle(
                  color: isActive ? Colors.green : Colors.red,
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(
              content,
              style: TextStyle(color: Colors.grey[600], fontSize: 12),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                if (scope['is_reusable'] == true)
                  _scopeTag('Reusable'),
                if (scope['is_contaminated'] == true)
                  _scopeTag('Terkontaminasi'),
                if (scope['is_wet'] == true) _scopeTag('Basah'),
              ],
            ),
            const SizedBox(height: 2),
            Text(
              'Sumber: $source',
              style: TextStyle(color: Colors.grey[400], fontSize: 11),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
        trailing: PopupMenuButton<String>(
          onSelected: (value) {
            if (value == 'edit') _showForm(item);
            if (value == 'delete') _confirmDelete(item);
          },
          itemBuilder: (_) => [
            const PopupMenuItem(value: 'edit', child: Text('Edit')),
            const PopupMenuItem(value: 'delete', child: Text('Nonaktifkan')),
          ],
        ),
      ),
    );
  }

  Widget _scopeTag(String label) {
    return Container(
      margin: const EdgeInsets.only(right: 4),
      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
      decoration: BoxDecoration(
        color: Colors.grey[200],
        borderRadius: BorderRadius.circular(3),
      ),
      child: Text(label, style: const TextStyle(fontSize: 10)),
    );
  }

  void _confirmDelete(Map<String, dynamic> item) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Nonaktifkan Knowledge'),
        content:
            Text('Nonaktifkan knowledge untuk "${item['category']}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Batal'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await _repo().deleteKnowledge(
                  knowledgeId: item['id'],
                  accessToken: _token,
                );
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Knowledge dinonaktifkan')),
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
            child: const Text('Nonaktifkan',
                style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  void _showForm(Map<String, dynamic>? existing) {
    final isEdit = existing != null;
    final contentCtrl =
        TextEditingController(text: existing?['content'] ?? '');
    final sourceCtrl =
        TextEditingController(text: existing?['source'] ?? '');
    final sourceUrlCtrl =
        TextEditingController(text: existing?['source_url'] ?? '');
    String category = existing?['category'] ?? _categories.first;
    bool isReusable =
        (existing?['condition_scope'] as Map<String, dynamic>?)?['is_reusable'] ==
            true;
    bool isContaminated =
        (existing?['condition_scope'] as Map<String, dynamic>?)?['is_contaminated'] ==
            true;
    bool isWet =
        (existing?['condition_scope'] as Map<String, dynamic>?)?['is_wet'] ==
            true;

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
                  isEdit ? 'Edit Knowledge' : 'Tambah Knowledge',
                  style: const TextStyle(
                      fontWeight: FontWeight.bold, fontSize: 18),
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  initialValue: category,
                  decoration: _inputDecoration('Kategori'),
                  items: _categories
                      .map((c) => DropdownMenuItem(
                            value: c,
                            child: Text(c.replaceAll('_', ' ')),
                          ))
                      .toList(),
                  onChanged: (v) => setModalState(() => category = v!),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: contentCtrl,
                  maxLines: 3,
                  decoration: InputDecoration(
                    labelText: 'Panduan Pengelolaan',
                    border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8)),
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 10),
                    isDense: true,
                  ),
                ),
                const SizedBox(height: 12),
                _inputField('Sumber', sourceCtrl),
                const SizedBox(height: 12),
                _inputField('URL Sumber', sourceUrlCtrl),
                const SizedBox(height: 12),
                const Text('Kondisi:',
                    style:
                        TextStyle(fontWeight: FontWeight.w500, fontSize: 13)),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 12,
                  children: [
                    _checkbox('Reusable', isReusable,
                        (v) => setModalState(() => isReusable = v)),
                    _checkbox('Terkontaminasi', isContaminated,
                        (v) => setModalState(() => isContaminated = v)),
                    _checkbox('Basah', isWet,
                        (v) => setModalState(() => isWet = v)),
                  ],
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () async {
                      final data = {
                        'category': category,
                        'content': contentCtrl.text.trim(),
                        'source': sourceCtrl.text.trim(),
                        'source_url': sourceUrlCtrl.text.trim().isEmpty
                            ? null
                            : sourceUrlCtrl.text.trim(),
                        'condition_scope': {
                          'is_reusable': isReusable,
                          'is_contaminated': isContaminated,
                          'is_wet': isWet,
                        },
                        'last_reviewed_at':
                            DateTime.now().toUtc().toIso8601String(),
                      };
                      Navigator.pop(ctx);
                      try {
                        if (isEdit) {
                          await _repo().updateKnowledge(
                            knowledgeId: existing['id'],
                            accessToken: _token,
                            data: data,
                          );
                        } else {
                          await _repo().createKnowledge(
                            accessToken: _token,
                            data: data,
                          );
                        }
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(isEdit
                                  ? 'Knowledge diperbarui'
                                  : 'Knowledge ditambahkan'),
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

  Widget _inputField(String label, TextEditingController ctrl) {
    return TextField(
      controller: ctrl,
      decoration: InputDecoration(
        labelText: label,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        isDense: true,
      ),
    );
  }

  Widget _checkbox(String label, bool value, ValueChanged<bool> onChanged) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Checkbox(
          value: value,
          onChanged: (v) => onChanged(v ?? false),
          materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
        ),
        Text(label, style: const TextStyle(fontSize: 13)),
      ],
    );
  }

  InputDecoration _inputDecoration(String label) {
    return InputDecoration(
      labelText: label,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
      contentPadding:
          const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      isDense: true,
    );
  }
}
