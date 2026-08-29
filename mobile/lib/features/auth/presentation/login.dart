import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/auth_provider.dart';
import '../data/auth_repository.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;
  bool _isLoading = false;
  final Color _primaryGreen = const Color(0xFF1E3F28);

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (_emailController.text.isEmpty || _passwordController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Email dan sandi tidak boleh kosong')));
      return;
    }

    setState(() => _isLoading = true);
    try {
      final response = await ref
          .read(authRepositoryProvider)
          .login(_emailController.text.trim(), _passwordController.text);
      await ref.read(authSessionProvider.notifier).authenticate(response);
      if (mounted) context.go('/home');
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
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 32.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                CircleAvatar(
                  radius: 32,
                  backgroundColor: _primaryGreen,
                  child: const Icon(Icons.eco, color: Colors.white, size: 36),
                ),
                const SizedBox(height: 16),
                Text('pilah.in', textAlign: TextAlign.center, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: _primaryGreen)),
                const SizedBox(height: 8),
                const Text('Selamat Datang Kembali!', textAlign: TextAlign.center, style: TextStyle(fontSize: 16, color: Colors.black87)),
                const SizedBox(height: 32),
                
                const Text('Email', style: TextStyle(fontWeight: FontWeight.w600)),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _emailController,
                  decoration: InputDecoration(hintText: 'nama@email.com', prefixIcon: const Icon(Icons.mail_outline), border: OutlineInputBorder(borderRadius: BorderRadius.circular(8))),
                ),
                const SizedBox(height: 16),
                
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Password', style: TextStyle(fontWeight: FontWeight.w600)),
                    TextButton(
                      onPressed: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Fitur reset password belum tersedia.')),
                        );
                      },
                      style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: Size.zero),
                      child: Text('Lupa Password?', style: TextStyle(color: _primaryGreen, fontSize: 13)),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  decoration: InputDecoration(
                    hintText: '••••••••',
                    prefixIcon: const Icon(Icons.lock_outline),
                    suffixIcon: IconButton(icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility), onPressed: () => setState(() => _obscurePassword = !_obscurePassword)),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                ),
                const SizedBox(height: 24),
                
                ElevatedButton(
                  onPressed: _isLoading ? null : _handleLogin,
                  style: ElevatedButton.styleFrom(backgroundColor: _primaryGreen, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 16)),
                  child: _isLoading 
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Row(mainAxisAlignment: MainAxisAlignment.center, children: [Text('Masuk', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)), SizedBox(width: 8), Icon(Icons.login, size: 20)]),
                ),
                const SizedBox(height: 32),
                
                Row(
                  children: [
                    const Expanded(child: Divider()),
                    Padding(padding: const EdgeInsets.symmetric(horizontal: 16), child: Text('atau masuk dengan', style: TextStyle(color: Colors.grey.shade600, fontSize: 12))),
                    const Expanded(child: Divider()),
                  ],
                ),
                const SizedBox(height: 24),
                
                OutlinedButton.icon(
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Login dengan Google belum tersedia.')),
                    );
                  },
                  icon: const Icon(Icons.g_mobiledata, size: 28, color: Colors.black87),
                  label: const Text('Google', style: TextStyle(color: Colors.black87)),
                  style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Login dengan Apple belum tersedia.')),
                    );
                  },
                  icon: const Icon(Icons.apple, size: 24, color: Colors.black87),
                  label: const Text('Apple', style: TextStyle(color: Colors.black87)),
                  style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
                ),
                const SizedBox(height: 32),
                
                Center(
                  child: InkWell(
                    onTap: () => context.push('/register'),
                    child: RichText(text: TextSpan(text: 'Belum punya akun? ', style: const TextStyle(color: Colors.black87), children: [TextSpan(text: 'Daftar sekarang', style: TextStyle(color: _primaryGreen, fontWeight: FontWeight.bold))])),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
