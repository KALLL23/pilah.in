import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:image_picker/image_picker.dart';
import 'analyzing_screen.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  CameraController? _cameraController;
  List<CameraDescription>? _cameras;
  bool _isCameraInitialized = false;
  bool _isFlashOn = false;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      _cameras = await availableCameras();
      if (_cameras != null && _cameras!.isNotEmpty) {
        _cameraController = CameraController(
          _cameras![0], // Menggunakan kamera belakang
          ResolutionPreset.high,
          enableAudio: false,
        );

        await _cameraController!.initialize();
        if (mounted) {
          setState(() {
            _isCameraInitialized = true;
          });
        }
      }
    } catch (e) {
      debugPrint("Error initializing camera: $e");
    }
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }

  Future<void> _takePicture() async {
    if (!_cameraController!.value.isInitialized) return;
    try {
      final XFile image = await _cameraController!.takePicture();
      _processImage(image.path);
    } catch (e) {
      debugPrint("Error taking picture: $e");
    }
  }

  Future<void> _pickFromGallery() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      _processImage(image.path);
    }
  }

  void _processImage(String imagePath) {
  // Pindah ke layar Analyzing dengan membawa parameter gambar
  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (context) => AnalyzingScreen(imagePath: imagePath),
    ),
  );
  }

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);
    const accentGreen = Color(0xFF00BFA5);

    if (!_isCameraInitialized) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: CircularProgressIndicator(color: accentGreen)),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // 1. Tampilan Kamera (Full Screen)
          CameraPreview(_cameraController!),

          // 2. Overlay Hitam Transparan
          Container(
            color: Colors.black.withOpacity(0.3),
          ),

          // 3. Area Pembidik (Bounding Box)
          Center(
            child: Container(
              width: MediaQuery.of(context).size.width * 0.75,
              height: MediaQuery.of(context).size.height * 0.5,
              decoration: BoxDecoration(
                border: Border.all(color: accentGreen.withOpacity(0.5), width: 2),
                borderRadius: BorderRadius.circular(16),
              ),
              // Membuat kotak area ini sepenuhnya transparan (menembus overlay)
              child: const SizedBox(), 
            ),
          ),

          // 4. Teks Instruksi di atas pembidik
          Positioned(
            top: MediaQuery.of(context).size.height * 0.15,
            left: 0,
            right: 0,
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.6),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text(
                  'Align item within the frame',
                  style: TextStyle(color: Colors.white, fontSize: 14),
                ),
              ),
            ),
          ),

          // 5. Tombol Top Bar (Back, Flash, Help)
          Positioned(
            top: 50,
            left: 20,
            right: 20,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildIconButton(
                  icon: Icons.arrow_back,
                  onTap: () => Navigator.pop(context),
                ),
                Row(
                  children: [
                    _buildIconButton(
                      icon: _isFlashOn ? Icons.flash_on : Icons.flash_off,
                      onTap: () {
                        setState(() {
                          _isFlashOn = !_isFlashOn;
                          _cameraController?.setFlashMode(
                            _isFlashOn ? FlashMode.torch : FlashMode.off,
                          );
                        });
                      },
                    ),
                    const SizedBox(width: 12),
                    _buildIconButton(
                      icon: Icons.help_outline,
                      onTap: () {},
                    ),
                  ],
                ),
              ],
            ),
          ),

          // 6. Bagian Bawah (Opsi Mode & Tombol Capture)
          Positioned(
            bottom: 40,
            left: 0,
            right: 0,
            child: Column(
              children: [
                // Tabs (Auto-detect, dll)
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _buildModeChip('AUTO-DETECT', true, primaryGreen),
                    const SizedBox(width: 8),
                    _buildModeChip('BARCODE', false, primaryGreen),
                    const SizedBox(width: 8),
                    _buildModeChip('TEXT', false, primaryGreen),
                  ],
                ),
                const SizedBox(height: 24),
                
                // Area Tombol Shutter dan Galeri
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 40),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      // Tombol Galeri
                      IconButton(
                        icon: const Icon(Icons.photo_library, color: Colors.white, size: 32),
                        onPressed: _pickFromGallery,
                      ),
                      
                      // Tombol Shutter Utama
                      GestureDetector(
                        onTap: _takePicture,
                        child: Container(
                          height: 70,
                          width: 70,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(color: Colors.white, width: 3),
                            color: Colors.transparent,
                          ),
                          child: Center(
                            child: Container(
                              height: 56,
                              width: 56,
                              decoration: const BoxDecoration(
                                shape: BoxShape.circle,
                                color: primaryGreen,
                              ),
                              child: const Icon(Icons.camera_alt, color: Colors.white, size: 28),
                            ),
                          ),
                        ),
                      ),
                      
                      // Placeholder agar posisi shutter tetap di tengah
                      const SizedBox(width: 48), 
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  'AI PROCESSING READY',
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 10,
                    letterSpacing: 2,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // Komponen pembantu untuk ikon bundar transparan
  Widget _buildIconButton({required IconData icon, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.4),
          shape: BoxShape.circle,
        ),
        child: Icon(icon, color: Colors.white, size: 24),
      ),
    );
  }

  // Komponen pembantu untuk label mode
  Widget _buildModeChip(String label, bool isSelected, Color activeColor) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: isSelected ? activeColor : Colors.white.withOpacity(0.3),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: Colors.white,
          fontSize: 12,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        ),
      ),
    );
  }
}