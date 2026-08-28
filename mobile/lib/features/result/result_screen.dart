import 'package:flutter/material.dart';

class ResultScreen extends StatelessWidget {
  final String imagePath;
  const ResultScreen({super.key, required this.imagePath});

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);
    const accentGreen = Color(0xFF00BFA5);
    const backgroundColor = Color(0xFFF8F9FA);

    return Scaffold(
      backgroundColor: backgroundColor,
      appBar: AppBar(
        backgroundColor: backgroundColor,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: primaryGreen),
          onPressed: () => Navigator.pop(context), // Kembali ke dashboard
        ),
        title: const Text(
          'Scan Result',
          style: TextStyle(color: primaryGreen, fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.more_vert, color: primaryGreen),
            onPressed: () {},
          )
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // --- Gambar & Material Terdeteksi ---
            Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey.withOpacity(0.2)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Dummy Gambar (Ganti dengan Image.file jika menggunakan path asli)
                  Container(
                    height: 150,
                    decoration: const BoxDecoration(
                      color: Colors.grey,
                      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
                    ),
                    child: Stack(
                      children: [
                        Positioned(
                          top: 12,
                          right: 12,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: primaryGreen.withOpacity(0.8),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: const Row(
                              children: [
                                Icon(Icons.check_circle, color: Colors.white, size: 14),
                                SizedBox(width: 6),
                                Text('AI Match: 94%', style: TextStyle(color: Colors.white, fontSize: 12)),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('DETECTED MATERIAL', style: TextStyle(fontSize: 10, letterSpacing: 1.2, color: Colors.grey[600])),
                            const SizedBox(height: 4),
                            const Text('PET Bottle', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: primaryGreen)),
                          ],
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(color: const Color(0xFFE8F5E9), borderRadius: BorderRadius.circular(8)),
                          child: const Text('#01 PETE', style: TextStyle(color: primaryGreen, fontWeight: FontWeight.w600, fontSize: 12)),
                        ),
                      ],
                    ),
                  )
                ],
              ),
            ),
            const SizedBox(height: 16),

            // --- Circularity Score ---
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white, 
                borderRadius: BorderRadius.circular(16), 
                border: Border.all(color: Colors.grey.withOpacity(0.2))
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Circularity Score', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: primaryGreen)),
                      const SizedBox(height: 4),
                      Text('High recycling potential', style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                    ],
                  ),
                  Stack(
                    alignment: Alignment.center,
                    children: [
                      SizedBox(
                        width: 50, 
                        height: 50, 
                        child: CircularProgressIndicator(
                          value: 0.84, 
                          backgroundColor: Colors.grey[200], 
                          valueColor: const AlwaysStoppedAnimation<Color>(primaryGreen), 
                          strokeWidth: 4
                        )
                      ),
                      const Text('84', style: TextStyle(fontWeight: FontWeight.bold, color: primaryGreen, fontSize: 16)),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // --- Best Action ---
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: const Color(0xFFF0FDF4), 
                borderRadius: BorderRadius.circular(16), 
                border: const Border(left: BorderSide(color: accentGreen, width: 4))
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.recycling, color: accentGreen, size: 28),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('BEST ACTION: RECYCLE', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.2, color: primaryGreen)),
                        const SizedBox(height: 8),
                        Text(
                          'High-density PET plastic is optimal for mechanical recycling. Ensure it is empty and crushed before disposal.', 
                          style: TextStyle(fontSize: 14, color: Colors.grey[800], height: 1.5)
                        ),
                      ],
                    ),
                  )
                ],
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white, 
          border: Border(top: BorderSide(color: Colors.grey.withOpacity(0.2)))
        ),
        child: Row(
          children: [
            Expanded(
              flex: 1,
              child: OutlinedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.bookmark_border, color: primaryGreen),
                label: const Text('Save', style: TextStyle(color: primaryGreen)),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16), 
                  side: const BorderSide(color: primaryGreen), 
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              flex: 2,
              child: ElevatedButton.icon(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.document_scanner_outlined, color: Colors.white),
                label: const Text('Scan Another', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: primaryGreen, 
                  padding: const EdgeInsets.symmetric(vertical: 16), 
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}