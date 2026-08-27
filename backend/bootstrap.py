import os
from sqlalchemy import create_engine
from app.models.models import Base  # Mengambil cetak biru tabel Anda

# Mengambil konfigurasi dari fail .env yang disuntikkan oleh Docker
DB_USER = os.getenv("DATABASE_USER", "pilahin")
DB_PASS = os.getenv("DATABASE_PASSWORD", "pilahin12354") 
DB_HOST = os.getenv("DATABASE_HOST", "postgres")
DB_NAME = os.getenv("DATABASE_NAME", "pilahin")

# Merakit URL Koneksi (otomatis menggunakan sandi dari .env)
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

print(f"Menghubungkan ke database {DB_NAME}...")
engine = create_engine(SQLALCHEMY_DATABASE_URL)

print("Mengeksekusi pembuatan tabel...")
Base.metadata.create_all(bind=engine)
print("Selesai! Silakan muat ulang (refresh) Database Client Anda.")