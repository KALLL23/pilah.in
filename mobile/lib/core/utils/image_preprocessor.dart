import 'dart:io';
import 'package:flutter_image_compress/flutter_image_compress.dart';
import 'package:path_provider/path_provider.dart';

class ImagePreprocessor {
  static Future<File?> processImage(File rawImage) async {
    final dir = await getTemporaryDirectory();
    final targetPath = '${dir.absolute.path}/temp_${DateTime.now().millisecondsSinceEpoch}.jpg';

    // Menerapkan kompresi JPEG 85, batas maksimal 1280px, dan menghapus metadata EXIF[cite: 1]
    final XFile? compressedImage = await FlutterImageCompress.compressAndGetFile(
      rawImage.absolute.path,
      targetPath,
      quality: 85, 
      minWidth: 1280, 
      minHeight: 1280, 
      format: CompressFormat.jpeg, 
      keepExif: false, 
    );

    if (compressedImage == null) return null;

    final processedFile = File(compressedImage.path);
    
    // Validasi pencegahan ukuran file agar tidak melebihi 8 MB[cite: 1]
    final fileSizeInBytes = await processedFile.length();
    if (fileSizeInBytes > 8 * 1024 * 1024) {
      throw Exception('Ukuran file melebihi batas 8 MB setelah kompresi.');
    }

    return processedFile;
  }
}