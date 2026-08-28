import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

// Sesuaikan path import dengan lokasi sebenarnya di proyek Anda
import '../../../features/auth/server_config_screen.dart';
import '../../features/auth/presentation/login.dart';
import '../../features/auth/presentation/register.dart';
import '../../features/main/main_scaffold.dart';
import '../../features/home/home_dashboard.dart';
import '../../features/scan/scan_screen.dart';
// import '../../features/result/result_screen.dart'; // Buka komentar jika sudah digunakan

// --- Dummy Screens ---
class MapScreen extends StatelessWidget {
  const MapScreen({super.key});
  @override
  Widget build(BuildContext context) => const Scaffold(body: Center(child: Text('Map Screen')));
}

class ActivityScreen extends StatelessWidget {
  const ActivityScreen({super.key});
  @override
  Widget build(BuildContext context) => const Scaffold(body: Center(child: Text('Activity Screen')));
}

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});
  @override
  Widget build(BuildContext context) => const Scaffold(body: Center(child: Text('Profile Screen')));
}

class AdminScreen extends StatelessWidget {
  const AdminScreen({super.key});
  @override
  Widget build(BuildContext context) => const Scaffold(body: Center(child: Text('Admin Screen')));
}

final appRouter = GoRouter(
  initialLocation: '/setup', // Memaksa aplikasi membuka konfigurasi server terlebih dahulu
  routes: [
    // 1. Rute Publik (Tanpa Bottom Navigation Bar)
    GoRoute(
      path: '/setup',
      builder: (context, state) => const ServerConfigScreen(),
    ),
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),
    GoRoute(
      path: '/register',
      builder: (context, state) => const RegisterScreen(),
    ),

    // 2. Rute Terproteksi (Dilengkapi Bottom Navigation Bar)
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) {
        return MainScaffold(navigationShell: navigationShell);
      },
      branches: [
        StatefulShellBranch(routes: [GoRoute(path: '/home', builder: (c, s) => const HomeDashboard())]),
        StatefulShellBranch(routes: [GoRoute(path: '/map', builder: (c, s) => const MapScreen())]),
        StatefulShellBranch(routes: [GoRoute(path: '/scan', builder: (c, s) => const ScanScreen())]),
        StatefulShellBranch(routes: [GoRoute(path: '/activity', builder: (c, s) => const ActivityScreen())]),
        StatefulShellBranch(routes: [GoRoute(path: '/profile', builder: (c, s) => const ProfileScreen())]),
        StatefulShellBranch(routes: [GoRoute(path: '/admin', builder: (c, s) => const AdminScreen())]),
      ],
    ),
  ],
);