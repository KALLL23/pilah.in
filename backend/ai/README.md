# AI workspace

Folder ini memusatkan tiga komponen AI pilah.in:

```text
backend/ai/
├── llm/                    # grounded recommendation integration
├── yolo_classification/    # Scan Waste training pipeline
├── yolo_detection/         # Report Waste training pipeline
└── raw_data/               # dataset lokal, diabaikan Git
```

Jalankan pipeline dari root repository agar semua path konfigurasi tetap konsisten.

Classification:

```powershell
python -m backend.ai.yolo_classification.src.pipeline --config backend/ai/yolo_classification/configs/pilah_cls_v0.1.yaml
```

Object detection:

```powershell
python -m backend.ai.yolo_detection.src.pipeline --config backend/ai/yolo_detection/configs/pilah_det_v0.1.yaml
```

Detail setup, opsi safe re-run, mapping kelas, dan output ada di README masing-masing pipeline.
