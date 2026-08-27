FROM python:3.10-slim

WORKDIR /app

# Perbarui pip ke versi terbaru untuk resolusi dependensi yang lebih stabil
RUN pip install --no-cache-dir --upgrade pip

# Instal PyTorch CPU menggunakan --extra-index-url (bukan --index-url)
RUN pip install --no-cache-dir torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu

# Salin dan instal seluruh dependensi dari requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]