import os
import httpx
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File # Tambahkan UploadFile & File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

# --- 1. SETUP ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Pastikan file .env sudah diisi dengan SUPABASE_URL dan SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI(title="Asisten Jatim Sosial API", version="1.0")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# --- 2. ROOT ENDPOINT ---
@app.get("/", tags=["General"])
async def root():
    return {"pesan": "Akses /docs untuk dokumentasi API."}

# --- 3. SCHEMA DATA ---
class DataWarga(BaseModel):
    nik: str
    nama: str
    pendapatan: float
    jumlah_tanggungan: int
    pendidikan: str

# --- 4. SISTEM LOGIN ---
@app.post("/auth/login", tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": form_data.username, 
            "password": form_data.password
        })
        return {"access_token": res.session.access_token, "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=401, detail="Email atau kata sandi salah")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        user_res = supabase.auth.get_user(token)
        if not user_res.user:
            raise HTTPException(status_code=401, detail="Sesi berakhir")
        return user_res.user
    except Exception:
        raise HTTPException(status_code=401, detail="Sesi tidak valid")

# --- 5. ORKESTRASI ASESMEN ---

# Jalur Teks (Tim 1 + 3)
@app.post("/api/v1/asesmen/sosial", tags=["Asesmen"])
async def asesmen_sosial(data: DataWarga, current_user = Depends(get_current_user)):
    URL_AI_TEXT = "http://127.0.0.1:8001/api/ai/text-analysis"
    
    try:
        # 1. Simpan data warga ke Supabase
        res_warga = supabase.table("warga").insert(data.model_dump()).execute()
        warga_id = res_warga.data[0]["id"]
        
        async with httpx.AsyncClient() as client:
            # 2. Panggil API Tim 1+3
            res_ai = await client.post(URL_AI_TEXT, json=data.model_dump(), timeout=10.0)
            hasil_ai = res_ai.json()
            
            # 3. Simpan hasil ke tabel hasil_asesmen
            supabase.table("hasil_asesmen").insert({
                "warga_id": warga_id,
                "petugas_email": current_user.email,
                "desil": hasil_ai["klasifikasi"]["desil"],
                "rekomendasi_program": str(hasil_ai["rekomendasi"])
            }).execute()
            
            return {"warga_id": warga_id, "hasil_sosial": hasil_ai}
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Server AI (Port 8001) tidak merespon")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses data: {str(e)}")

# Jalur Visual (Tim 2)
@app.post("/api/v1/asesmen/visual/{warga_id}", tags=["Asesmen"])
async def asesmen_visual(warga_id: str, file: UploadFile = File(...), current_user = Depends(get_current_user)):
    URL_AI_VISUAL = "http://127.0.0.1:8001/api/ai/visual-analysis"
    
    try:
        async with httpx.AsyncClient() as client:
            # Kirim file ke API Dummy Tim 2
            files = {"file": (file.filename, file.file, file.content_type)}
            res_ai = await client.post(URL_AI_VISUAL, files=files, timeout=15.0)
            hasil_visual = res_ai.json()
            
            # Update data hasil_asesmen di Supabase
            supabase.table("hasil_asesmen").update({
                "kondisi_rumah": hasil_visual["kondisi"]
            }).eq("warga_id", warga_id).execute()
            
            return hasil_visual
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Server AI Visual tidak merespon")