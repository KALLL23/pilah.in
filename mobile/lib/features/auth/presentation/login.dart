import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/config/app_config.dart';
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
  bool _demoMode = false;
  final Color _primaryGreen = const Color(0xFF1E3F28);

  @override
  void initState() {
    super.initState();
    _fetchDemoMode();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _fetchDemoMode() async {
    final dio = ref.read(dioProvider);
    final authSession = ref.read(authSessionProvider).value;
    if (authSession == null || !authSession.hasServer) return;
    try {
      final response = await dio.get('${authSession.serverUrl}/api/v1/admin/demo-mode');
      if (mounted) {
        setState(() => _demoMode = response.data['demo_mode'] == true);
      }
    } catch (_) {}
  }

  Future<void> _toggleDemoMode() async {
    final dio = ref.read(dioProvider);
    final authSession = ref.read(authSessionProvider).value;
    if (authSession == null || !authSession.hasServer) return;
    try {
      final response = await dio.post('${authSession.serverUrl}/api/v1/admin/demo-mode');
      if (mounted) {
        final newMode = response.data['demo_mode'] == true;
        setState(() => _demoMode = newMode);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(newMode ? 'Demo Mode: ON — Lokasi bisa di mana saja' : 'Demo Mode: OFF — Hanya Semarang'),
            backgroundColor: newMode ? const Color(0xFF00BFA5) : Colors.orange,
          ),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Gagal mengubah Demo Mode'), backgroundColor: Colors.red),
        );
      }
    }
  }

  String? _normalizeServerUrl(String value) {
    final normalized = value.trim().replaceFirst(RegExp(r'/+$'), '');
    final uri = Uri.tryParse(normalized);
    if (uri == null ||
        !{'http', 'https'}.contains(uri.scheme) ||
        uri.host.isEmpty) {
      return null;
    }
    return normalized;
  }

  void _showServerConfig() {
    final urlController = TextEditingController(
      text: AppConfig.defaultServerUrl,
    );
    bool isLoading = false;
    String statusMessage = '';

    showDialog(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            Future<void> testConnection() async {
              setDialogState(() {
                isLoading = true;
                statusMessage = 'Menghubungkan...';
              });

              final dio = ref.read(dioProvider);
              final serverUrl = _normalizeServerUrl(urlController.text);
              if (serverUrl == null) {
                setDialogState(() {
                  isLoading = false;
                  statusMessage = 'URL tidak valid.';
                });
                return;
              }

              try {
                final response = await dio.get('$serverUrl/api/health');
                if (response.statusCode == 200) {
                  await ref
                      .read(authSessionProvider.notifier)
                      .configureServer(serverUrl);
                  if (!context.mounted) return;
                  setDialogState(() {
                    statusMessage = 'Koneksi berhasil!';
                    isLoading = false;
                  });
                }
              } catch (_) {
                if (!context.mounted) return;
                setDialogState(() {
                  statusMessage =
                      'Gagal terhubung. Pastikan backend berjalan dan HP di jaringan yang sama.';
                  isLoading = false;
                });
              }
            }

            return AlertDialog(
              title: const Text('Konfigurasi Server'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: urlController,
                    decoration: const InputDecoration(
                      labelText: 'Server URL',
                      border: OutlineInputBorder(),
                      hintText: 'http://192.168.1.9:8000',
                    ),
                    keyboardType: TextInputType.url,
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: isLoading ? null : testConnection,
                      child: isLoading
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child:
                                  CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text('Test Connection'),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    statusMessage,
                    style: TextStyle(
                      color: statusMessage.contains('berhasil')
                          ? Colors.green
                          : Colors.red,
                      fontSize: 13,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(dialogContext).pop(),
                  child: const Text('Tutup'),
                ),
              ],
            );
          },
        );
      },
    );
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
        child: Stack(
          children: [
            Center(
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
        Positioned(
          top: 8,
          right: 8,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              GestureDetector(
                onTap: _toggleDemoMode,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _demoMode ? const Color(0xFFE8F5E9) : Colors.grey.shade200,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: _demoMode ? const Color(0xFF00BFA5) : Colors.grey.shade400,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.science,
                        size: 14,
                        color: _demoMode ? const Color(0xFF00BFA5) : Colors.grey,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        'Demo',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: _demoMode ? const Color(0xFF00BFA5) : Colors.grey,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 4),
              IconButton(
                icon: Icon(Icons.settings, color: Colors.grey.shade600),
                onPressed: _showServerConfig,
                tooltip: 'Konfigurasi Server',
              ),
            ],
          ),
        ),
        ],
      ),
    ),
  );
}
}
