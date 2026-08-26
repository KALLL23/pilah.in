from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import random
import time

# Inisialisasi Aplikasi
app = FastAPI(
    title="pilah.in API",
    description="Backend API untuk layanan pilah.in.",
    version="1.0.0"
)

# Konfigurasi CORS agar aplikasi (atau web) bisa mengakses API tanpa diblokir
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint 1: Pengecekan Status Server
@app.get("/api/health")
def health_check():
    return {"status": "success", "message": "pilah.in API is running."}

# Endpoint 2: Analisis Gambar (Fitur Utama)
@app.post("/api/scan/analyze")
async def analyze_waste(image: UploadFile = File(...)):
    # Validasi format file
    if not image.filename.endswith(('.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Format gambar tidak didukung. Gunakan JPG atau PNG.")

    try:
        # Di sinilah nantinya Anda membaca file dan memasukkannya ke model YOLO
        # image_bytes = await image.read()
        # ai_result = yolo_model.predict(image_bytes)
        
        # [MOCK ENGINE] Simulasi proses komputasi AI (1.5 detik)
        time.sleep(1.5)

        # [MOCK DATA] Basis data sementara untuk hasil AI
        mock_database = [
            {
                "detected_class": "PET Bottle",
                "material_code": "#01 PETE",
                "confidence": 94.5,
                "circularity_score": 84,
                "score_status": "High recycling potential",
                "best_action": "RECYCLE",
                "action_reason": "High-density PET plastic is optimal for mechanical recycling. Ensure it is empty and crushed before disposal.",
                "est_value_rp": 450,
                "impact_co2e_grams": -120
            },
            {
                "detected_class": "Cardboard Box",
                "material_code": "PAP 20",
                "confidence": 98.2,
                "circularity_score": 92,
                "score_status": "Excellent upcycle potential",
                "best_action": "UPCYCLE",
                "action_reason": "Clean cardboard is perfect for repurposing. Keep it dry to maintain its structural integrity and value.",
                "est_value_rp": 300,
                "impact_co2e_grams": -85
            }
        ]

        # Pilih hasil secara acak untuk mensimulasikan berbagai skenario pemindaian
        ai_decision = random.choice(mock_database)

        return {
            "status": "success",
            "filename": image.filename,
            "data": ai_decision
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan pada server: {str(e)}")

# Menjalankan server secara otomatis jika file dieksekusi langsung
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
