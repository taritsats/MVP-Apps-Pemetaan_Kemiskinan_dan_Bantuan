import os
import httpx
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
import models
from database import engine, get_db

# --- 1. SETUP DATABASE POSTGRESQL ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Pemetaan Kemiskinan dan Bantuan", version="1.0")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# --- 2. ROOT & SCHEMA (PYDANTIC) ---
@app.get("/", tags=["General"])
async def root():
    return {"pesan": "Backend FastAPI + PostgreSQL Berjalan Normal!"}

class DataWarga(BaseModel):
    no_kk: str
    nama_kepala_keluarga: str
    alamat: str

# --- 3. SISTEM LOGIN (MOCK / DUMMY UNTUK SEMENTARA) ---
async def get_current_user(db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    if not user:
        user = models.User(username="admin_jatim", email="admin@dinsos.go.id", password_hash="dummy_hash")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# --- 4. ORKESTRASI ASESMEN (SIMPAN KE POSTGRESQL) ---
@app.post("/api/v1/asesmen/sosial", tags=["Asesmen"])
async def asesmen_sosial(
    data: DataWarga, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db) # <--- Inject koneksi database
):
    URL_TIM_1 = "http://127.0.0.1:8001/api/ai/tim1-klasifikasi"
    URL_TIM_3 = "http://127.0.0.1:8001/api/ai/tim3-rekomendasi"
    
    try:
        # A. Simpan Input Warga ke PostgreSQL (Tabel Keluarga)
        keluarga_baru = models.Keluarga(
            no_kk=data.no_kk,
            nama_kepala_keluarga=data.nama_kepala_keluarga,
            alamat=data.alamat
        )
        db.add(keluarga_baru)
        db.commit()
        db.refresh(keluarga_baru)
        warga_id = keluarga_baru.id
        
        async with httpx.AsyncClient() as client:
            # B. Panggil API Tim 1
            res_tim1 = await client.post(URL_TIM_1, json=data.model_dump(), timeout=10.0)
            res_tim1.raise_for_status()
            hasil_tim1 = res_tim1.json()
            desil_warga = hasil_tim1.get("desil", "Tidak diketahui")
            
            # C. Panggil API Tim 3
            payload_tim3 = data.model_dump()
            payload_tim3["desil"] = desil_warga 
            res_tim3 = await client.post(URL_TIM_3, json=payload_tim3, timeout=10.0)
            res_tim3.raise_for_status()
            hasil_tim3 = res_tim3.json()
            rekomendasi_teks = str(hasil_tim3.get("rekomendasi", "Tidak ada rekomendasi"))
            
            # D. Simpan Hasil ke PostgreSQL (Tabel Perhitungan)
            perhitungan_baru = models.Perhitungan(
                keluarga_id=warga_id,
                user_id=current_user.id,
                desil_kemiskinan=str(desil_warga),
                rekomendasi_bantuan=rekomendasi_teks,
                status_validasi="Menunggu"
            )
            db.add(perhitungan_baru)
            db.commit()
            
            return {
                "status": "Sukses",
                "warga_id": warga_id, 
                "klasifikasi_tim1": hasil_tim1,
                "rekomendasi_tim3": hasil_tim3
            }
            
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Server Tim AI tidak merespon. Pastikan port 8001 menyala.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal memproses orkestrasi: {str(e)}")


# --- 5. ENDPOINT ASESMEN VISUAL (Tim 2) ---
@app.post("/api/v1/asesmen/visual/{warga_id}", tags=["Asesmen"])
async def asesmen_visual(
    warga_id: int, 
    file: UploadFile = File(...), 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    URL_TIM_2 = "http://127.0.0.1:8001/api/ai/tim2-visual"
    try:
        async with httpx.AsyncClient() as client:
            files = {"file": (file.filename, file.file, file.content_type)}
            res_ai = await client.post(URL_TIM_2, files=files, timeout=15.0)
            hasil_visual = res_ai.json()
            kondisi_didapat = hasil_visual.get("kondisi", "Tidak terdeteksi")
            
            perhitungan = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == warga_id).first()
            
            if not perhitungan:
                raise HTTPException(status_code=404, detail="Data asesmen untuk warga ini belum ada. Jalankan asesmen sosial dulu.")
            
            perhitungan.kondisi_rumah = kondisi_didapat
            db.commit()
            
            return hasil_visual
            
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Server API Visual (Tim 2) tidak merespon")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal memproses visual: {str(e)}")