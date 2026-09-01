import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/providers/auth_provider.dart';

class ResultScreen extends ConsumerStatefulWidget {
  final String imagePath;
  final Map<String, dynamic> scanResponse;
  final Map<String, dynamic>? recommendation;

  const ResultScreen({
    super.key,
    required this.imagePath,
    required this.scanResponse,
    this.recommendation,
  });

  @override
  ConsumerState<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends ConsumerState<ResultScreen>
    with SingleTickerProviderStateMixin {
  List<Map<String, dynamic>> _facilities = [];
  bool _loadingFacilities = true;

  bool _jualExpanded = false;
  bool _daurUlangExpanded = false;
  bool _buangExpanded = false;

  late TabController _productTabController;
  int _selectedProductIndex = 0;

  static const Map<String, String> _categoryPriceRanges = {
    'PLASTIC': 'Rp 2.000 – 5.000/kg',
    'PAPER_CARDBOARD': 'Rp 500 – 1.500/kg',
    'GLASS': 'Rp 200 – 500/kg',
    'METAL': 'Rp 5.000 – 15.000/kg',
    'TEXTILE': 'Rp 1.000 – 3.000/kg',
    'ELECTRONIC_SPECIAL': 'Rp 10.000 – 50.000/kg',
  };

  @override
  void initState() {
    super.initState();
    _determineExpanded();
    _fetchFacilities();

    final recyclingProducts = _getRecyclingProducts();
    _productTabController = TabController(
      length: recyclingProducts.length,
      vsync: this,
    );
    _productTabController.addListener(() {
      if (!_productTabController.indexIsChanging) {
        setState(() => _selectedProductIndex = _productTabController.index);
      }
    });
  }

  @override
  void dispose() {
    _productTabController.dispose();
    super.dispose();
  }

  List<Map<String, dynamic>> _getRecyclingProducts() {
    final products = widget.recommendation?['recycling_products'];
    if (products is List) {
      return products.map<Map<String, dynamic>>((e) => Map<String, dynamic>.from(e as Map)).toList();
    }
    return [];
  }

  void _determineExpanded() {
    final action = widget.recommendation?['action'] as String?;
    switch (action) {
      case 'REUSE':
        _jualExpanded = true;
        break;
      case 'RECYCLE':
      case 'COMPOST':
        _daurUlangExpanded = true;
        break;
      case 'RESIDUAL':
      case 'SPECIAL_HANDLING':
        _buangExpanded = true;
        break;
      default:
        _jualExpanded = true;
    }
  }

  String _getCategoryCode() {
    final predicted = widget.scanResponse['predicted_category'] as Map<String, dynamic>?;
    final confirmed = widget.scanResponse['confirmed_category'] as Map<String, dynamic>?;
    return (confirmed?['code'] ?? predicted?['code'] ?? 'PLASTIC') as String;
  }

  Future<void> _fetchFacilities() async {
    final session = ref.read(authSessionProvider).value;
    if (session == null || !session.isAuthenticated) {
      if (mounted) setState(() => _loadingFacilities = false);
      return;
    }

    final dio = ref.read(dioProvider);
    final category = _getCategoryCode();

    try {
      final response = await dio.get(
        '${session.serverUrl}/api/v1/facilities',
        queryParameters: {'category': category, 'limit': 20},
        options: Options(headers: {'Authorization': 'Bearer ${session.accessToken}'}),
      );

      if (mounted) {
        final data = response.data;
        setState(() {
          _facilities = (data is Map ? (data['items'] ?? []) : [])
              .map<Map<String, dynamic>>((e) => Map<String, dynamic>.from(e as Map))
              .toList();
          _loadingFacilities = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _loadingFacilities = false);
    }
  }

  Future<void> _openMaps(double lat, double lng) async {
    final url = Uri.parse('https://www.google.com/maps/dir/?api=1&destination=$lat,$lng');
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);

    final predictedCategory = widget.scanResponse['predicted_category'] as Map<String, dynamic>;
    final confidence = (widget.scanResponse['prediction_confidence'] as num).toDouble();
    final categoryName = predictedCategory['name'] as String;
    final categoryCode = _getCategoryCode();

    final action = widget.recommendation?['action'] as String?;
    final reason = widget.recommendation?['reason'] as String?;
    final recyclingTarget = widget.recommendation?['recycling_target'] as String?;
    final preparationSteps = (widget.recommendation?['preparation_steps'] as List<dynamic>?)
        ?.map((e) => e.toString())
        .toList();
    final warnings = (widget.recommendation?['warnings'] as List<dynamic>?)
        ?.map((e) => e.toString())
        .toList();
    final recyclingProducts = _getRecyclingProducts();

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
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
          Positioned(
            top: MediaQuery.of(context).size.height * 0.30,
            right: 20,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.95),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.1), blurRadius: 8)],
              ),
              child: Row(
                children: [
                  const Icon(Icons.check_circle, color: primaryGreen, size: 16),
                  const SizedBox(width: 4),
                  Text(
                    '${(confidence * 100).toStringAsFixed(1)}%',
                    style: const TextStyle(
                      color: primaryGreen,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
          ),
          Align(
            alignment: Alignment.bottomCenter,
            child: Container(
              height: MediaQuery.of(context).size.height * 0.68,
              padding: const EdgeInsets.all(20),
              decoration: const BoxDecoration(
                color: Color(0xFFF8F9FA),
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
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE8F5E9),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: const Text(
                        'Hasil Analisis',
                        style: TextStyle(
                          color: primaryGreen,
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      categoryName,
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: primaryGreen,
                      ),
                    ),

                    if (action != null) ...[
                      const SizedBox(height: 6),
                      Text(
                        'Rekomendasi: ${_actionLabel(action)}',
                        style: TextStyle(
                          fontSize: 13,
                          color: _actionColor(action),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],

                    const SizedBox(height: 16),

                    _buildExpandableCard(
                      title: 'Jual',
                      subtitle: 'Jual ke bank sampah atau pengumpul',
                      icon: Icons.sell_outlined,
                      color: const Color(0xFF2E7D32),
                      expanded: _jualExpanded,
                      onTap: () => setState(() => _jualExpanded = !_jualExpanded),
                      child: _buildJualContent(categoryCode),
                    ),
                    const SizedBox(height: 12),

                    _buildExpandableCard(
                      title: 'Daur Ulang',
                      subtitle: recyclingProducts.isNotEmpty
                          ? '${recyclingProducts.length} produk rekomendasi'
                          : 'Daur ulang atau kompos',
                      icon: Icons.recycling,
                      color: const Color(0xFF1565C0),
                      expanded: _daurUlangExpanded,
                      onTap: () => setState(() => _daurUlangExpanded = !_daurUlangExpanded),
                      child: _buildDaurUlangContent(recyclingTarget, preparationSteps, recyclingProducts, categoryCode),
                    ),
                    const SizedBox(height: 12),

                    _buildExpandableCard(
                      title: 'Buang',
                      subtitle: 'Buang ke tempat sampah atau TPS3R',
                      icon: Icons.delete_outline,
                      color: const Color(0xFF757575),
                      expanded: _buangExpanded,
                      onTap: () => setState(() => _buangExpanded = !_buangExpanded),
                      child: _buildBuangContent(categoryCode),
                    ),

                    if (reason != null && reason.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          const Icon(Icons.lightbulb_outline, color: primaryGreen, size: 18),
                          const SizedBox(width: 6),
                          const Text(
                            'Alasan AI',
                            style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        reason,
                        style: TextStyle(fontSize: 13, color: Colors.grey.shade700, height: 1.5),
                      ),
                    ],

                    if (warnings != null && warnings.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFF3E0),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.orange.shade200),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              children: [
                                Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 18),
                                SizedBox(width: 6),
                                Text(
                                  'Peringatan',
                                  style: TextStyle(
                                    fontWeight: FontWeight.w600,
                                    fontSize: 14,
                                    color: Colors.orange,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            ...warnings.map((w) => Padding(
                              padding: const EdgeInsets.only(bottom: 4),
                              child: Text(
                                '• $w',
                                style: TextStyle(fontSize: 12, color: Colors.orange.shade800),
                              ),
                            )),
                          ],
                        ),
                      ),
                    ],

                    if (action == null) ...[
                      const SizedBox(height: 24),
                      Center(
                        child: Column(
                          children: [
                            Icon(Icons.info_outline, size: 48, color: Colors.grey.shade400),
                            const SizedBox(height: 12),
                            Text(
                              'Rekomendasi belum tersedia.',
                              style: TextStyle(fontSize: 14, color: Colors.grey.shade500),
                            ),
                          ],
                        ),
                      ),
                    ],

                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        onPressed: () {
                          Navigator.of(context).popUntil((route) => route.isFirst);
                        },
                        icon: const Icon(Icons.home_outlined, color: primaryGreen),
                        label: const Text(
                          'Kembali ke Beranda',
                          style: TextStyle(color: primaryGreen, fontSize: 14, fontWeight: FontWeight.w600),
                        ),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          side: const BorderSide(color: Colors.grey),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildExpandableCard({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required bool expanded,
    required VoidCallback onTap,
    required Widget child,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: expanded ? color.withValues(alpha: 0.4) : Colors.grey.withValues(alpha: 0.2),
        ),
        boxShadow: expanded
            ? [BoxShadow(color: color.withValues(alpha: 0.1), blurRadius: 8, offset: const Offset(0, 2))]
            : [],
      ),
      child: Column(
        children: [
          GestureDetector(
            onTap: onTap,
            child: Container(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: 0.1),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(icon, color: color, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: color,
                          ),
                        ),
                        Text(
                          subtitle,
                          style: TextStyle(fontSize: 11, color: Colors.grey.shade500),
                        ),
                      ],
                    ),
                  ),
                  Icon(
                    expanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                    color: color,
                  ),
                ],
              ),
            ),
          ),
          if (expanded) ...[
            Divider(height: 1, color: Colors.grey.withValues(alpha: 0.2)),
            Padding(
              padding: const EdgeInsets.all(14),
              child: child,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildJualContent(String categoryCode) {
    final priceRange = _categoryPriceRanges[categoryCode];
    final sellingFacilities = _facilities.where((f) {
      final type = f['facility_type'] as String? ?? '';
      return type == 'BANK_SAMPAH' || type == 'COLLECTOR' || type == 'RECYCLING_FACILITY';
    }).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (priceRange != null) ...[
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: const Color(0xFFE8F5E9),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                const Icon(Icons.attach_money, color: Color(0xFF2E7D32), size: 18),
                const SizedBox(width: 8),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Estimasi Harga',
                      style: TextStyle(fontSize: 11, color: Color(0xFF2E7D32)),
                    ),
                    Text(
                      priceRange,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF2E7D32),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
        ],
        if (_loadingFacilities)
          const Center(
            child: Padding(
              padding: EdgeInsets.all(20),
              child: CircularProgressIndicator(color: Color(0xFF2E7D32), strokeWidth: 2),
            ),
          )
        else if (sellingFacilities.isEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              'Tidak ada fasilitas penjualan terdekat untuk kategori ini.',
              style: TextStyle(color: Colors.grey.shade500, fontSize: 13),
              textAlign: TextAlign.center,
            ),
          )
        else
          ...sellingFacilities.map((f) => _buildFacilityTile(f, const Color(0xFF2E7D32))),
      ],
    );
  }

  Widget _buildDaurUlangContent(String? recyclingTarget, List<String>? steps, List<Map<String, dynamic>> products, String categoryCode) {
    if (products.isNotEmpty) {
      return _buildRecyclingProductsTab(products);
    }

    final target = recyclingTarget ?? _recyclingInfo(categoryCode);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: const Color(0xFFE3F2FD),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Hasil Daur Ulang',
                style: TextStyle(fontSize: 11, color: Color(0xFF1565C0)),
              ),
              const SizedBox(height: 4),
              Text(
                target,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF1565C0),
                ),
              ),
            ],
          ),
        ),

        if (steps != null && steps.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text(
            'Langkah Daur Ulang:',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 13,
              color: Color(0xFF1565C0),
            ),
          ),
          const SizedBox(height: 6),
          ...steps.asMap().entries.map((entry) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    margin: const EdgeInsets.only(top: 4),
                    width: 20,
                    height: 20,
                    decoration: const BoxDecoration(
                      color: Color(0xFF1565C0),
                      shape: BoxShape.circle,
                    ),
                    child: Center(
                      child: Text(
                        '${entry.key + 1}',
                        style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      entry.value,
                      style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ],
    );
  }

  Widget _buildRecyclingProductsTab(List<Map<String, dynamic>> products) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          decoration: BoxDecoration(
            color: const Color(0xFFE3F2FD),
            borderRadius: BorderRadius.circular(8),
          ),
          child: TabBar(
            controller: _productTabController,
            isScrollable: true,
            labelColor: const Color(0xFF1565C0),
            unselectedLabelColor: Colors.grey.shade600,
            labelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
            unselectedLabelStyle: const TextStyle(fontSize: 12),
            indicatorColor: const Color(0xFF1565C0),
            indicatorWeight: 2,
            dividerColor: Colors.transparent,
            tabAlignment: TabAlignment.start,
            padding: const EdgeInsets.symmetric(horizontal: 4),
            tabs: products.asMap().entries.map((entry) {
              final product = entry.value;
              final name = product['name'] as String? ?? 'Produk ${entry.key + 1}';
              return Tab(text: name.length > 20 ? '${name.substring(0, 20)}...' : name);
            }).toList(),
          ),
        ),
        const SizedBox(height: 12),
        _buildProductDetail(products[_selectedProductIndex]),
      ],
    );
  }

  Widget _buildProductDetail(Map<String, dynamic> product) {
    final name = product['name'] as String? ?? '-';
    final description = product['description'] as String? ?? '-';
    final tools = (product['tools_needed'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];
    final steps = (product['steps'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];
    final difficulty = product['difficulty'] as String? ?? 'SEDANG';
    final estimatedTime = product['estimated_time'] as String? ?? '-';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFFE3F2FD),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                name,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1565C0),
                ),
              ),
              const SizedBox(height: 6),
              Text(
                description,
                style: TextStyle(fontSize: 13, color: Colors.grey.shade700, height: 1.4),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  _buildInfoBadge(
                    icon: Icons.signal_cellular_alt,
                    label: difficulty,
                    color: _difficultyColor(difficulty),
                  ),
                  const SizedBox(width: 8),
                  _buildInfoBadge(
                    icon: Icons.access_time,
                    label: estimatedTime,
                    color: const Color(0xFF1565C0),
                  ),
                ],
              ),
            ],
          ),
        ),

        if (tools.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text(
            'Alat & Bahan:',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 13,
              color: Color(0xFF1565C0),
            ),
          ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: tools.map((tool) => Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFFE8EAF6),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                tool,
                style: const TextStyle(fontSize: 11, color: Color(0xFF3F51B5)),
              ),
            )).toList(),
          ),
        ],

        if (steps.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text(
            'Langkah Pembuatan:',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 13,
              color: Color(0xFF1565C0),
            ),
          ),
          const SizedBox(height: 6),
          ...steps.asMap().entries.map((entry) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    margin: const EdgeInsets.only(top: 4),
                    width: 22,
                    height: 22,
                    decoration: const BoxDecoration(
                      color: Color(0xFF1565C0),
                      shape: BoxShape.circle,
                    ),
                    child: Center(
                      child: Text(
                        '${entry.key + 1}',
                        style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      entry.value,
                      style: TextStyle(fontSize: 13, color: Colors.grey.shade700, height: 1.4),
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ],
    );
  }

  Widget _buildInfoBadge({required IconData icon, required String label, required Color color}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color),
          ),
        ],
      ),
    );
  }

  Color _difficultyColor(String difficulty) {
    switch (difficulty) {
      case 'MUDAH': return const Color(0xFF4CAF50);
      case 'SEDANG': return const Color(0xFFFF9800);
      case 'SULIT': return const Color(0xFFF44336);
      default: return const Color(0xFFFF9800);
    }
  }

  Widget _buildBuangContent(String categoryCode) {
    final disposalSteps = _disposalSteps(categoryCode);
    final disposalFacilities = _facilities.where((f) {
      final type = f['facility_type'] as String? ?? '';
      return type == 'TPS3R' || type == 'SPECIAL_WASTE_FACILITY';
    }).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: Colors.grey.shade50,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Langkah Pembuangan:',
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: Color(0xFF616161)),
              ),
              const SizedBox(height: 6),
              ...disposalSteps.asMap().entries.map((entry) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.check_circle_outline, color: Color(0xFF757575), size: 16),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          entry.value,
                          style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
                        ),
                      ),
                    ],
                  ),
                );
              }),
            ],
          ),
        ),

        if (!_loadingFacilities && disposalFacilities.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text(
            'TPS3R / Tempat Pembuangan Terdekat:',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 13,
              color: Color(0xFF616161),
            ),
          ),
          const SizedBox(height: 6),
          ...disposalFacilities.map((f) => _buildFacilityTile(f, const Color(0xFF757575))),
        ],
      ],
    );
  }

  Widget _buildFacilityTile(Map<String, dynamic> facility, Color color) {
    final name = facility['name'] as String? ?? '-';
    final address = facility['address'] as String? ?? '-';
    final lat = (facility['latitude'] as num?)?.toDouble();
    final lng = (facility['longitude'] as num?)?.toDouble();
    final phone = facility['phone'] as String?;
    final openingHours = facility['opening_hours'] as Map<String, dynamic>?;
    final distance = (facility['distance_m'] as num?)?.toDouble();

    String hoursText = '';
    if (openingHours != null && openingHours.isNotEmpty) {
      final now = DateTime.now();
      final dayNames = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
      final today = dayNames[now.weekday - 1];
      final todayHours = openingHours[today];
      if (todayHours != null) {
        hoursText = 'Hari ini: $todayHours';
      }
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.location_city, color: color, size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  name,
                  style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14, color: color),
                ),
              ),
              if (distance != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    _formatDistance(distance),
                    style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.w600),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 4),
          Text(address, style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
          if (phone != null && phone.isNotEmpty) ...[
            const SizedBox(height: 2),
            Row(
              children: [
                Icon(Icons.phone, color: Colors.grey.shade400, size: 12),
                const SizedBox(width: 4),
                Text(phone, style: TextStyle(fontSize: 11, color: Colors.grey.shade500)),
              ],
            ),
          ],
          if (hoursText.isNotEmpty) ...[
            const SizedBox(height: 2),
            Row(
              children: [
                Icon(Icons.access_time, color: Colors.grey.shade400, size: 12),
                const SizedBox(width: 4),
                Text(hoursText, style: TextStyle(fontSize: 11, color: Colors.grey.shade500)),
              ],
            ),
          ],
          if (lat != null && lng != null) ...[
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => _openMaps(lat, lng),
                icon: const Icon(Icons.directions, size: 16),
                label: const Text('Buka di Maps', style: TextStyle(fontSize: 12)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: color,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _formatDistance(double meters) {
    if (meters < 1000) return '${meters.toStringAsFixed(0)} m';
    return '${(meters / 1000).toStringAsFixed(1)} km';
  }

  String _actionLabel(String action) {
    switch (action) {
      case 'REUSE': return 'Gunakan Kembali';
      case 'RECYCLE': return 'Daur Ulang';
      case 'COMPOST': return 'Kompos';
      case 'RESIDUAL': return 'Buang ke Tempat Sampah';
      case 'SPECIAL_HANDLING': return 'Penanganan Khusus';
      default: return action;
    }
  }

  Color _actionColor(String action) {
    switch (action) {
      case 'REUSE': return const Color(0xFF2E7D32);
      case 'RECYCLE': return const Color(0xFF1565C0);
      case 'COMPOST': return const Color(0xFF558B2F);
      case 'RESIDUAL': return const Color(0xFF757575);
      case 'SPECIAL_HANDLING': return const Color(0xFFC62828);
      default: return Colors.grey;
    }
  }

  String _recyclingInfo(String categoryCode) {
    switch (categoryCode) {
      case 'PLASTIC':
        return 'Plastik dapat dilelehkan dan dicetak ulang menjadi produk baru seperti wadah, tas, atau bangunan ringan.';
      case 'PAPER_CARDBOARD':
        return 'Kertas dan karton dapat didaur ulang menjadi kertas baru, tisu, atau produk kertas lainnya.';
      case 'GLASS':
        return 'Kaca dapat dilelehkan dan dibentuk ulang menjadi botol, gelas, atau dekorasi baru.';
      case 'METAL':
        return 'Logam dapat dilelehkan dan digunakan kembali untuk membuat produk logam baru.';
      case 'ORGANIC':
        return 'Bahan organik dapat dikompos menjadi pupuk alami untuk tanaman.';
      case 'TEXTILE':
        return 'Tekstil dapat dijahit ulang menjadi produk baru atau diolah menjadi kain daur ulang.';
      case 'ELECTRONIC_SPECIAL':
        return 'Elektronik harus diserahkan ke fasilitas khusus untuk ekstraksi logam berharga dan penanganan limbah B3.';
      default:
        return 'Bahan ini dapat diolah melalui proses daur ulang yang sesuai.';
    }
  }

  List<String> _disposalSteps(String categoryCode) {
    switch (categoryCode) {
      case 'RESIDUAL_MIXED':
        return [
          'Pisahkan sampah yang masih bisa didaur ulang',
          'Bungkus sampah dengan kantong plastik',
          'Buang ke tempat sampah umum atau TPS3R terdekat',
          'Pastikan tidak membuang sampah sembarangan',
        ];
      case 'ELECTRONIC_SPECIAL':
        return [
          'Jangan buang elektronik ke tempat sampah biasa',
          'Simpan di tempat kering dan aman',
          'Serahkan ke fasilitas penanganan limbah B3 terdekat',
          'Pastikan data pribadi sudah dihapus dari perangkat',
        ];
      default:
        return [
          'Pisahkan sampah berdasarkan jenisnya',
          'Buang ke tempat sampah yang sesuai',
          'Pastikan sampah tidak berserakan',
          'Jaga kebersihan lingkungan sekitar',
        ];
    }
  }
}
