import 'package:pilahin/features/scan/scan_screen.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// Sesuaikan path import ini dengan lokasi Anda menyimpan file home_dashboard.dart
import 'features/home/home_dashboard.dart'; 

void main() {
  runApp(const PilahInApp());
}

class PilahInApp extends StatelessWidget {
  const PilahInApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'pilah.in',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1E3F28), // Warna hijau gelap utama
          background: const Color(0xFFF8F9FA), // Warna latar belakang putih keabu-abuan
        ),
        textTheme: GoogleFonts.interTextTheme(Theme.of(context).textTheme),
        useMaterial3: true,
      ),
      home: const MainNavigationScreen(),
    );
  }
}

// --- Layar Navigasi Utama ---
class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;

  // Daftar halaman yang akan ditampilkan saat tab ditekan
  final List<Widget> _pages = [
    const HomeDashboard(), // Mengambil dari home_dashboard.dart
    const ScanScreen(), // Mengambil dari scan_screen.dart
    const ProfileDummyScreen(), // Layar dummy agar tidak error
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.background,
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      
      // Tombol Kamera/Scan Utama
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => const ScanScreen()),
          );
        },
        backgroundColor: const Color(0xFF1E3F28),
        shape: const CircleBorder(),
        elevation: 4,
        child: const Icon(Icons.camera_alt, color: Colors.white, size: 28),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
      
      // Bottom Navigation Bar
      bottomNavigationBar: BottomAppBar(
        shape: const CircularNotchedRectangle(),
        notchMargin: 8.0,
        color: Colors.white,
        elevation: 10,
        child: SizedBox(
          height: 60,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNavItem(icon: Icons.home_rounded, label: 'Home', index: 0),
              _buildNavItem(icon: Icons.history_rounded, label: 'History', index: 1),
              const SizedBox(width: 40), // Ruang kosong untuk tombol kamera di tengah
              _buildNavItem(icon: Icons.camera_alt, label: 'Scan', index: -1, isPlaceholder: true), // Placeholder teks
              _buildNavItem(icon: Icons.person_outline_rounded, label: 'Profile', index: 2),
            ],
          ),
        ),
      ),
    );
  }

  // Fungsi pembantu untuk merender ikon navigasi
  Widget _buildNavItem({
    required IconData icon, 
    required String label, 
    required int index,
    bool isPlaceholder = false,
  }) {
    final isSelected = _currentIndex == index;
    final color = isSelected ? const Color(0xFF1E3F28) : Colors.grey;

    if (isPlaceholder) {
      return Column(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          const SizedBox(height: 24), // Spacer pengganti ikon
          Text(
            label,
            style: const TextStyle(color: Colors.grey, fontSize: 12),
          ),
        ],
      );
    }

    return InkWell(
      onTap: () => setState(() => _currentIndex = index),
      highlightColor: Colors.transparent,
      splashColor: Colors.transparent,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: color),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              color: color, 
              fontSize: 12, 
              fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal
            ),
          ),
        ],
      ),
    );
  }
}

// --- Dummy Screens ---
// Dibuat sementara agar Anda bisa menekan tab History dan Profile tanpa menyebabkan error

class HistoryDummyScreen extends StatelessWidget {
  const HistoryDummyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Text(
          'History Screen\n(Dalam Pengembangan)',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 16, color: Colors.grey),
        ),
      ),
    );
  }
}

class ProfileDummyScreen extends StatelessWidget {
  const ProfileDummyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Text(
          'Profile Screen\n(Dalam Pengembangan)',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 16, color: Colors.grey),
        ),
      ),
    );
  }
}
