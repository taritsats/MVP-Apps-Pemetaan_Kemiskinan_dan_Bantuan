import os
import httpx
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import boto3
from dotenv import load_dotenv

import models
from database import engine, get_db

# 1. SETUP AWAL & LOAD ENV
load_dotenv()
models.Base.metadata.create_all(bind=engine)

# 2. KONFIGURASI MINIO
MINIO_ENDPOINT = "127.0.0.1:9000"
MINIO_ACCESS_KEY = "admin_minio"
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "supersecretpassword")
MINIO_BUCKET = "foto-rumah-warga"

s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)   

# 3. KONFIGURASI KEAMANAN JWT
# Perbaikan: Tambahkan fallback string jika .env gagal terbaca
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "rahasia_super_aman_pemetaan_jatim") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 4. METADATA SWAGGER UI
app = FastAPI(
    title="API Pemetaan Kemiskinan Jatim",
    description="Sistem Backend Pemetaan Kemiskinan",
    version="1.0.0",
)

# 5. SCHEMAS (PYDANTIC)
class DataWarga(BaseModel):
    # 1. Identitas & Lokasi
    kode_provinsi: str = Field(..., max_length=2, example="35")
    nama_provinsi: str = Field(..., max_length=100, example="Jawa Timur")
    kode_kabupaten: str = Field(..., max_length=4, example="3573")
    nama_kabupaten: str = Field(..., max_length=100, example="Kota Malang")
    kode_kecamatan: str = Field(..., max_length=7, example="3573010")
    nama_kecamatan: str = Field(..., max_length=100, example="Lowokwaru")
    kode_kelurahan_desa: str = Field(..., max_length=10, example="3573010001")
    nama_kelurahan_desa: str = Field(..., max_length=100, example="Ketawanggede")
    alamat_domisili: str = Field(..., max_length=500, example="Jl. Veteran, Malang")
    no_kk: str = Field(..., max_length=16, example="3573012345678901")
    nama_kepala_keluarga: str = Field(..., max_length=500, example="Bapak Budi")
    jumlah_anggota_keluarga: int = Field(..., example=4)
    
    # 2. Indikator Kesejahteraan & PLN
    desil_kesejahteraan_nasional: int = Field(..., example=1)
    penerima_bantuan_iuran_nasional: bool = Field(..., example=True)
    penerima_bantuan_iuran_pemda: bool = Field(..., example=False)
    id_pln: Optional[str] = Field(default=None, max_length=20, example="123456789012")
    
    # 3. Kondisi Rumah (Angka kode kategori)
    status_kepemilikan_rumah: int = Field(..., example=2)
    jenis_lantai: int = Field(..., example=5)
    luas_lantai: int = Field(..., example=24)
    jenis_dinding: int = Field(..., example=4)
    jenis_atap: int = Field(..., example=3)
    sumber_air_minum: int = Field(..., example=4)
    sumber_penerangan: int = Field(..., example=2)
    daya_listrik: int = Field(..., example=450)
    bahan_bakar_memasak: int = Field(..., example=3)
    fasilitas_bab: int = Field(..., example=2)
    jenis_kloset: int = Field(..., example=2)
    jenis_pembuangan_akhir: int = Field(..., example=2)
    
    # 4. Kepemilikan Aset (Boolean)
    flag_kepemilikan_aset: bool = Field(..., example=True)
    kepemilikan_aset_tabung_gas: bool = Field(..., example=False)
    kepemilikan_aset_kulkas: bool = Field(..., example=False)
    kepemilikan_aset_ac: bool = Field(..., example=False)
    kepemilikan_aset_water_heater: bool = Field(..., example=False)
    kepemilikan_aset_telepon_rumah: bool = Field(..., example=False)
    kepemilikan_aset_televisi_datar: bool = Field(..., example=False)
    kepemilikan_aset_perhiasan_emas: bool = Field(..., example=False)
    kepemilikan_aset_komputer_laptop_tablet: bool = Field(..., example=False)
    kepemilikan_aset_kendaraan_sepeda_motor: bool = Field(..., example=True)
    kepemilikan_aset_kendaraan_sepeda: bool = Field(..., example=False)
    kepemilikan_aset_kendaraan_mobil: bool = Field(..., example=False)
    kepemilikan_aset_kendaraan_perahu: bool = Field(..., example=False)
    kepemilikan_aset_kendaraan_kapal: bool = Field(..., example=False)
    kepemilikan_aset_smartphone: bool = Field(..., example=True)
    kepemilikan_aset_tanah: bool = Field(..., example=False)
    kepemilikan_aset_rumah: bool = Field(..., example=False)
    
    # 5. Kepemilikan Ternak
    jumlah_kepemilikan_ternak_sapi: int = Field(..., example=0)
    jumlah_kepemilikan_ternak_kerbau: int = Field(..., example=0)
    jumlah_kepemilikan_ternak_kuda: int = Field(..., example=0)
    jumlah_kepemilikan_ternak_babi: int = Field(..., example=0)
    jumlah_kepemilikan_ternak_kambing_domba: int = Field(..., example=0)

# 6. ENDPOINT AUTHENTICATION
@app.post("/auth/buat-admin", tags=["Authentication"], summary="Buat Akun Admin Pertama")
def buat_admin(db: Session = Depends(get_db)):
    admin = db.query(models.User).filter(models.User.username == "admin_jatim").first()
    if admin:
        return {"pesan": "Akun admin_jatim sudah ada di database!"}
    
    raw_password = os.getenv("ADMIN_PASSWORD", "taritsa123")
    hashed_pw = get_password_hash(raw_password)
    
    new_admin = models.User(username="admin_jatim", email="admin@dinsos.go.id", password_hash=hashed_pw)
    db.add(new_admin)
    db.commit()
    return {"pesan": "Berhasil! Akun admin_jatim telah dibuat dengan aman."}

@app.post("/auth/login", tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Username atau password salah")
    
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Token tidak valid atau sudah kadaluarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.username == username).first()
    # Perbaikan: Jika user tidak ada di database, tolak aksesnya
    if user is None:
        raise credentials_exception
    return user

# 7. ENDPOINT ASESMEN
@app.post("/api/v1/asesmen/sosial", tags=["Asesmen"])
async def asesmen_sosial(data: DataWarga, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    URL_TIM_1 = "http://127.0.0.1:8001/api/ai/tim1-klasifikasi"
    URL_TIM_3 = "http://127.0.0.1:8001/api/ai/tim3-rekomendasi"
    
    try:
        keluarga_baru = models.Keluarga(**data.model_dump())
        db.add(keluarga_baru)
        db.commit()
        db.refresh(keluarga_baru)
        
        async with httpx.AsyncClient() as client:
            res_tim1 = await client.post(URL_TIM_1, json=data.model_dump(), timeout=10.0)
            desil_warga = res_tim1.json().get("desil", "Tidak diketahui")
            
            payload_tim3 = data.model_dump()
            payload_tim3["desil"] = desil_warga 
            res_tim3 = await client.post(URL_TIM_3, json=payload_tim3, timeout=10.0)
            rekomendasi_teks = str(res_tim3.json().get("rekomendasi", "Tidak ada rekomendasi"))
            
            perhitungan_baru = models.Perhitungan(
                keluarga_id=keluarga_baru.id, user_id=current_user.id,
                desil_kemiskinan=str(desil_warga), rekomendasi_bantuan=rekomendasi_teks
            )
            db.add(perhitungan_baru)
            db.commit()
            
            return {"status": "Sukses", "warga_id": str(keluarga_baru.id), "klasifikasi_tim1": res_tim1.json(), "rekomendasi_tim3": res_tim3.json()}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal memproses orkestrasi: {str(e)}")

@app.post("/api/v1/asesmen/visual/{warga_id}", tags=["Asesmen"])
async def asesmen_visual(warga_id: str, file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    URL_TIM_2 = "http://127.0.0.1:8001/api/ai/tim2-visual"
    
    try:
        file_content = await file.read()
        nama_file_unik = f"{warga_id}_{file.filename}"
        s3_client.put_object(Bucket=MINIO_BUCKET, Key=nama_file_unik, Body=file_content, ContentType=file.content_type)
        foto_url = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{nama_file_unik}"

        await file.seek(0)
        async with httpx.AsyncClient() as client:
            files = {"file": (file.filename, file.file, file.content_type)}
            res_ai = await client.post(URL_TIM_2, files=files, timeout=15.0)
            kondisi_didapat = str(res_ai.json().get("prediksi_material", "Tidak terdeteksi"))

            perhitungan = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == warga_id).first()
            if not perhitungan:
                raise HTTPException(status_code=404, detail="Data warga tidak ditemukan.")

            perhitungan.kondisi_rumah = kondisi_didapat
            perhitungan.foto_url = foto_url 
            db.commit()
            
            return {"status": "Sukses", "url_foto": foto_url, "analisis_ai": res_ai.json()}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal: {str(e)}")