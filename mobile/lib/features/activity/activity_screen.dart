import 'package:flutter/material.dart';

class ActivityScreen extends StatelessWidget {
  const ActivityScreen({super.key});

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);
    const backgroundColor = Color(0xFFF8F9FA);

    return Scaffold(
      backgroundColor: backgroundColor,
      appBar: AppBar(
        backgroundColor: backgroundColor,
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
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Total Poin Terkumpul
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'TOTAL POIN TERKUMPUL',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: Colors.grey[600],
                          letterSpacing: 1.1,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        '1,250',
                        style: TextStyle(
                          fontSize: 36,
                          fontWeight: FontWeight.bold,
                          color: primaryGreen,
                        ),
                      ),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: const BoxDecoration(
                      color: Color(0xFFE8F5E9),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.eco, color: primaryGreen, size: 28),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Filters
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _buildFilterChip('Semua', true, primaryGreen),
                  const SizedBox(width: 12),
                  _buildFilterChip('Plastik', false, primaryGreen),
                  const SizedBox(width: 12),
                  _buildFilterChip('Kertas', false, primaryGreen),
                  const SizedBox(width: 12),
                  _buildFilterChip('Kaca', false, primaryGreen),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // History List
            _buildHistoryItem(
              icon: Icons.water_drop,
              title: 'Botol Plastik PET',
              subtitle: 'Hari ini, 14:30 • Drop Box A',
              tag: 'Plastik',
              points: '+50 Pts',
              primaryGreen: primaryGreen,
            ),
            const SizedBox(height: 16),
            _buildHistoryItem(
              icon: Icons.description,
              title: 'Karton Bekas',
              subtitle: 'Kemarin, 09:15 • Drop Box B',
              tag: 'Kertas',
              points: '+30 Pts',
              primaryGreen: primaryGreen,
            ),
            const SizedBox(height: 16),
            _buildHistoryItem(
              icon: Icons.shopping_bag,
              title: 'Kantong Kresek',
              subtitle: '12 Okt 2023 • Bank Sampah Pusat',
              tag: 'Plastik',
              points: '+15 Pts',
              primaryGreen: primaryGreen,
            ),
            const SizedBox(height: 16),
            _buildHistoryItem(
              icon: Icons.local_cafe, // Close enough to glass icon
              title: 'Botol Kaca',
              subtitle: '10 Okt 2023 • Drop Box A',
              tag: 'Kaca',
              points: '+80 Pts',
              primaryGreen: primaryGreen,
            ),
            const SizedBox(height: 80),
          ],
        ),
      ),
    );
  }

  Widget _buildFilterChip(String label, bool isSelected, Color primaryGreen) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      decoration: BoxDecoration(
        color: isSelected ? primaryGreen : Colors.transparent,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: isSelected ? primaryGreen : Colors.grey[300]!),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: isSelected ? Colors.white : Colors.grey[700],
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  Widget _buildHistoryItem({
    required IconData icon,
    required String title,
    required String subtitle,
    required String tag,
    required String points,
    required Color primaryGreen,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.withOpacity(0.2)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFFE8F5E9),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: primaryGreen),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.grey[200],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    tag,
                    style: TextStyle(
                      color: Colors.grey[700],
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
          Column(
            children: [
              Text(
                points.split(' ')[0],
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 20,
                  color: Color(0xFF1E3F28),
                ),
              ),
              Text(
                points.split(' ')[1],
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                  color: Color(0xFF1E3F28),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
