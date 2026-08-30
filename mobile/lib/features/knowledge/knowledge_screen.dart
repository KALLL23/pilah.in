import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers/auth_provider.dart';
import 'knowledge_repository.dart';

class KnowledgeScreen extends ConsumerStatefulWidget {
  const KnowledgeScreen({super.key});

  @override
  ConsumerState<KnowledgeScreen> createState() => _KnowledgeScreenState();
}

class _KnowledgeScreenState extends ConsumerState<KnowledgeScreen> {
  List<dynamic> _items = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  KnowledgeRepository _repo() {
    final dio = ref.read(dioProvider);
    final session = ref.read(authSessionProvider).value!;
    return KnowledgeRepository(dio, session.serverUrl!);
  }

  String get _token => ref.read(authSessionProvider).value!.accessToken!;

  Future<void> _fetch() async {
    setState(() => _loading = true);
    try {
      final data = await _repo().listKnowledge(accessToken: _token);
      setState(() {
        _items = data['items'] ?? [];
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  String _categoryLabel(String code) {
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

  IconData _categoryIcon(String code) {
    switch (code) {
      case 'PLASTIC':
        return Icons.water_drop_outlined;
      case 'PAPER_CARDBOARD':
        return Icons.description_outlined;
      case 'GLASS':
        return Icons.wine_bar_outlined;
      case 'METAL':
        return Icons.build_outlined;
      case 'ORGANIC':
        return Icons.eco_outlined;
      case 'TEXTILE':
        return Icons.checkroom_outlined;
      case 'ELECTRONIC_SPECIAL':
        return Icons.devices_outlined;
      case 'RESIDUAL_MIXED':
        return Icons.delete_outline;
      default:
        return Icons.info_outline;
    }
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
          'Edukasi Sampah',
          style: TextStyle(
            color: primaryGreen,
            fontWeight: FontWeight.bold,
            fontSize: 20,
          ),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: primaryGreen))
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline, size: 48, color: Colors.grey[400]),
                      const SizedBox(height: 16),
                      Text('Gagal memuat data',
                          style: TextStyle(color: Colors.grey[600])),
                      const SizedBox(height: 12),
                      ElevatedButton(
                        onPressed: _fetch,
                        style: ElevatedButton.styleFrom(backgroundColor: primaryGreen),
                        child: const Text('Coba Lagi', style: TextStyle(color: Colors.white)),
                      ),
                    ],
                  ),
                )
              : _items.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.school_outlined, size: 48, color: Colors.grey[300]),
                          const SizedBox(height: 16),
                          Text('Belum ada edukasi',
                              style: TextStyle(color: Colors.grey[500])),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _fetch,
                      child: ListView.separated(
                        padding: const EdgeInsets.all(16),
                        itemCount: _items.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 12),
                        itemBuilder: (ctx, i) => _knowledgeCard(_items[i]),
                      ),
                    ),
    );
  }

  Widget _knowledgeCard(Map<String, dynamic> item) {
    const primaryGreen = Color(0xFF1E3F28);
    final category = item['category'] ?? '';
    final content = item['content'] ?? '';
    final source = item['source'] ?? '';
    final scope = item['condition_scope'] as Map<String, dynamic>? ?? {};

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.grey.withValues(alpha: 0.1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: const BoxDecoration(
                  color: Color(0xFFE8F5E9),
                  shape: BoxShape.circle,
                ),
                child: Icon(_categoryIcon(category), color: primaryGreen, size: 18),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  _categoryLabel(category),
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                    color: primaryGreen,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            content,
            style: const TextStyle(fontSize: 13, height: 1.5),
          ),
          if (scope.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: [
                if (scope['is_reusable'] == true)
                  _tag('Reusable', Colors.green),
                if (scope['is_contaminated'] == true)
                  _tag('Terkontaminasi', Colors.orange),
                if (scope['is_wet'] == true)
                  _tag('Basah', Colors.blue),
              ],
            ),
          ],
          const SizedBox(height: 10),
          Row(
            children: [
              Icon(Icons.source, size: 14, color: Colors.grey[400]),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  source,
                  style: TextStyle(fontSize: 11, color: Colors.grey[500]),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _tag(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 10, color: color, fontWeight: FontWeight.w500),
      ),
    );
  }
}
