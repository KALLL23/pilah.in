# PILAH-DET Training Pipeline

Pipeline ini memvalidasi dan memetakan SynWasteNet ke taxonomy delapan kelas pilah.in, membuat split baru yang bebas overlap, melatih `yolo26n.pt`, mengevaluasi test set, lalu menerbitkan `models/waste_det.pt`.

## Setup

Dari root repository:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/ai/yolo_detection/requirements.txt
```

Dataset lokal harus berada di:

```text
backend/ai/raw_data/SynWasteNet/
├── images/       # 6.000 gambar canonical
└── labels/       # anotasi YOLO yang berpasangan berdasarkan stem
```

Folder `split/` bawaan dataset sengaja tidak dipakai karena train dan val tumpang tindih 730 gambar dan tidak menyediakan test set. Raw data selalu read-only. Pipeline membuat split 70/15/15 baru dari `images/` dan `labels/`.

## Satu command

```powershell
python -m backend.ai.yolo_detection.src.pipeline --config backend/ai/yolo_detection/configs/pilah_det_v0.1.yaml
```

Saat pertama dijalankan, Ultralytics akan mengunduh weight resmi `yolo26n.pt` bila belum ada. Pipeline tidak mengganti model dengan varian lain secara diam-diam.

Command aman untuk memvalidasi seluruh data dan membangun dataset tanpa training GPU:

```powershell
python -m backend.ai.yolo_detection.src.pipeline --config backend/ai/yolo_detection/configs/pilah_det_v0.1.yaml --skip-training
```

Gunakan `--force` untuk membangun ulang output generated. Opsi ini hanya menghapus `data/processed/detection` dan run dengan versi model yang sama; raw dataset tidak pernah dihapus.

## Mempercepat training lokal

- Pastikan log Ultralytics menampilkan CUDA dan pantau GPU dengan `nvidia-smi -l 2`. GPU usage yang terus rendah biasanya berarti data loader terhambat storage.
- Hindari melatih langsung dari folder cloud-sync. Pindahkan `dataset.processed_root` dan `output.runs_dir` di config ke SSD lokal non-OneDrive, atau pastikan seluruh file tersedia offline.
- Untuk eksperimen cepat, gunakan `imgsz: 512`, `deterministic: false`, dan tambahkan `fraction: 0.25` di bawah `model.train`. Kembalikan `fraction: 1.0` dan `imgsz: 640` untuk final training.
- Dengan VRAM 4 GB, mulai dari `batch: 8`. Jika stabil dan VRAM masih longgar, coba 12 atau 16; jika out-of-memory, turunkan ke 4.
- `epochs` tidak mengubah durasi satu epoch. Gunakan early stopping melalui `patience` dan lakukan smoke run dengan 1–3 epoch sebelum final run.

## Mapping kelas

| SynWasteNet | Model pilah.in |
|---|---|
| plastic | plastic |
| paper, cardboard | paper_cardboard |
| glass | glass |
| metal | metal |
| organic | organic |
| cloth | textile |
| battery, e_waste | electronic_special |
| other_waste | residual_mixed |

Nama keluaran tersebut langsung kompatibel dengan adapter detection backend.

## Output

```text
data/processed/detection/
├── metadata.csv
├── dataset/{train,val,test}/{images,labels}/
├── dataset/data.yaml
└── reports/{dataset_report.json,dataset_report.md}

runs/detection/PILAH-DET-v0.1.0/
├── config_snapshot.yaml
├── ultralytics/
├── evaluation/
└── reports/{training_report.json,training_report.md}

models/waste_det.pt
models/archive/PILAH-DET-v0.1.0.pt
```

## Tests

```powershell
python -m pytest backend/ai/yolo_detection/tests -q
```
