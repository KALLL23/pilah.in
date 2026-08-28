import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'core/router/app_router.dart';

void main() {
  // Wajib membungkus aplikasi dengan ProviderScope untuk mengaktifkan Riverpod
  runApp(const ProviderScope(child: PilahInApp()));
}

class PilahInApp extends StatelessWidget {
  const PilahInApp({super.key});

  @override
  Widget build(BuildContext context) {
    // Gunakan MaterialApp.router agar go_router dapat mengambil alih navigasi
    return MaterialApp.router(
      title: 'pilah.in',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1E3F28), 
          surface: const Color(0xFFF8F9FA), 
        ),
        textTheme: GoogleFonts.interTextTheme(Theme.of(context).textTheme),
        useMaterial3: true,
      ),
      routerConfig: appRouter, 
    );
  }
}