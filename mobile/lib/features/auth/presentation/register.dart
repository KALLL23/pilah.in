import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/auth_provider.dart';
import '../data/auth_repository.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isAccepted = false;
  bool _isLoading = false;
  final Color _primaryGreen = const Color(0xFF1E3F28);

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    if (_nameController.text.isEmpty || _emailController.text.isEmpty || _passwordController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Harap isi seluruh formulir')));
      return;
    }

    setState(() => _isLoading = true);
    try {
      final response = await ref.read(authRepositoryProvider).register(
        _nameController.text.trim(),
        _emailController.text.trim(),
        _passwordController.text,
      );
      await ref.read(authSessionProvider.notifier).authenticate(response);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Pendaftaran berhasil!')),
      );
      context.go('/home');
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(backgroundColor: Colors.white, elevation: 0, leading: IconButton(icon: const Icon(Icons.arrow_back, color: Colors.black87), onPressed: () => context.go('/login'))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(height: 4, color: _primaryGreen, margin: const EdgeInsets.only(bottom: 24)),
            Text('pilah.in', textAlign: TextAlign.center, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: _primaryGreen)),
            const SizedBox(height: 8),
            const Text('Bergabunglah untuk Masa Depan Hijau', textAlign: TextAlign.center, style: TextStyle(fontSize: 16, color: Colors.black87)),
            const SizedBox(height: 32),
            
            TextFormField(controller: _nameController, decoration: InputDecoration(hintText: 'Nama Lengkap', prefixIcon: const Icon(Icons.person_outline), border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)))),
            const SizedBox(height: 16),
            TextFormField(controller: _emailController, decoration: InputDecoration(hintText: 'Email', prefixIcon: const Icon(Icons.mail_outline), border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)))),
            const SizedBox(height: 16),
            TextFormField(controller: _passwordController, obscureText: true, decoration: InputDecoration(hintText: 'Password', prefixIcon: const Icon(Icons.lock_outline), border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)))),
            const SizedBox(height: 16),
            
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  height: 24,
                  width: 24,
                  child: Checkbox(value: _isAccepted, activeColor: _primaryGreen, onChanged: (val) => setState(() => _isAccepted = val ?? false)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: RichText(
                    text: TextSpan(
                      text: 'Saya menyetujui ',
                      style: const TextStyle(color: Colors.black87, fontSize: 13),
                      children: [
                        TextSpan(text: 'Syarat dan Ketentuan ', style: TextStyle(color: _primaryGreen)),
                        const TextSpan(text: 'serta Kebijakan Privasi.'),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            
            ElevatedButton(
              onPressed: (_isAccepted && !_isLoading) ? _handleRegister : null, 
              style: ElevatedButton.styleFrom(backgroundColor: _primaryGreen, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 16)),
              child: _isLoading 
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                  : const Row(mainAxisAlignment: MainAxisAlignment.center, children: [Text('Daftar', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)), SizedBox(width: 8), Icon(Icons.arrow_forward, size: 20)]),
            ),
            const SizedBox(height: 32),
            
            Row(
              children: [
                const Expanded(child: Divider()),
                Padding(padding: const EdgeInsets.symmetric(horizontal: 16), child: Text('ATAU DAFTAR DENGAN', style: TextStyle(color: Colors.grey.shade600, fontSize: 10, letterSpacing: 1.2))),
                const Expanded(child: Divider()),
              ],
            ),
            const SizedBox(height: 24),
            
            Row(
              children: [
                Expanded(child: OutlinedButton(onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Daftar dengan Google belum tersedia.')),
                  );
                }, style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))), child: const Icon(Icons.g_mobiledata, size: 28, color: Colors.black87))),
                const SizedBox(width: 16),
                Expanded(child: OutlinedButton(onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Daftar dengan Apple belum tersedia.')),
                  );
                }, style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))), child: const Icon(Icons.apple, size: 24, color: Colors.black87))),
              ],
            ),
            const SizedBox(height: 32),
            
            Center(
              child: InkWell(
                onTap: () => context.go('/login'), // Memaksa kembali ke halaman login melalui teks interaktif
                child: RichText(text: TextSpan(text: 'Sudah memiliki akun? ', style: const TextStyle(color: Colors.black87), children: [TextSpan(text: 'Masuk', style: TextStyle(color: _primaryGreen, fontWeight: FontWeight.bold))])),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}
