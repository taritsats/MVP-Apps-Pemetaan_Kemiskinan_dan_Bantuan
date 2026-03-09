import os
import httpx
import chromadb # Import ChromaDB yang baru saja diinstal
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

# --- 1. SETUP SUPABASE ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Pastikan file .env sudah diisi dengan SUPABASE_URL dan SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. SETUP CHROMADB ---
# Membuat folder 'chroma_data' di komputer/server Anda untuk menyimpan vektor
chroma_client = chromadb.PersistentClient(path="./chroma_data")
# Membuat 'tabel' (collection) khusus untuk data warga
warga_collection = chroma_client.get_or_create_collection(name="vektor_warga")

app = FastAPI(title="Asisten Jatim Sosial API", version="1.0")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# --- 3. ROOT & SCHEMA ---
@app.get("/", tags=["General"])
async def root():
    return {"pesan": "Sistem Backend Berjalan Normal. Akses /docs untuk dokumentasi API."}

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

# --- 5. ORKESTRASI ASESMEN (SIMPAN KE SQL & VEKTOR) ---
@app.post("/api/v1/asesmen/sosial", tags=["Asesmen"])
async def asesmen_sosial(data: DataWarga, current_user = Depends(get_current_user)):
    URL_TIM_1 = "http://127.0.0.1:8001/api/ai/tim1-klasifikasi"
    URL_TIM_3 = "http://127.0.0.1:8001/api/ai/tim3-rekomendasi"
    
    try:
        # A. Simpan ke Supabase (Tabel warga)
        res_warga = supabase.table("warga").insert(data.model_dump()).execute()
        warga_id = res_warga.data[0]["id"]
        
        async with httpx.AsyncClient() as client:
            # B. Panggil API Tim 1
            res_tim1 = await client.post(URL_TIM_1, json=data.model_dump(), timeout=10.0)
            res_tim1.raise_for_status()
            hasil_tim1 = res_tim1.json()
            desil_warga = hasil_tim1["desil"]
            
            # C. Panggil API Tim 3
            payload_tim3 = data.model_dump()
            payload_tim3["desil"] = desil_warga 
            res_tim3 = await client.post(URL_TIM_3, json=payload_tim3, timeout=10.0)
            res_tim3.raise_for_status()
            hasil_tim3 = res_tim3.json()
            rekomendasi_teks = str(hasil_tim3["rekomendasi"])
            
            # D. Simpan ke Supabase (Tabel hasil_asesmen)
            supabase.table("hasil_asesmen").insert({
                "warga_id": warga_id,
                "petugas_email": current_user.email,
                "desil": desil_warga,
                "kategori_kesejahteraan": hasil_tim1["kategori"],
                "rekomendasi_program": rekomendasi_teks
            }).execute()

            # ==========================================
            # E. SIMPAN KE CHROMADB (VECTOR DATABASE)
            # ==========================================
            teks_dokumen = f"Warga bernama {data.nama} (NIK: {data.nik}) memiliki pendidikan {data.pendidikan} dengan pendapatan Rp{data.pendapatan} dan {data.jumlah_tanggungan} tanggungan. Masuk dalam desil {desil_warga} ({hasil_tim1['kategori']}). Rekomendasi program: {rekomendasi_teks}."
            
            warga_collection.add(
                documents=[teks_dokumen],
                metadatas=[{"warga_id": warga_id, "desil": desil_warga}], 
                ids=[warga_id]
            )
            
            return {
                "status": "Sukses",
                "warga_id": warga_id, 
                "klasifikasi_tim1": hasil_tim1,
                "rekomendasi_tim3": hasil_tim3
            }
            
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Server Tim AI tidak merespon. Pastikan port 8001 menyala.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses orkestrasi: {str(e)}")

# --- 6. ENDPOINT ASESMEN VISUAL (Tim 2) ---
@app.post("/api/v1/asesmen/visual/{warga_id}", tags=["Asesmen"])
async def asesmen_visual(warga_id: str, file: UploadFile = File(...), current_user = Depends(get_current_user)):
    URL_TIM_2 = "http://127.0.0.1:8001/api/ai/tim2-visual"
    try:
        async with httpx.AsyncClient() as client:
            files = {"file": (file.filename, file.file, file.content_type)}
            res_ai = await client.post(URL_TIM_2, files=files, timeout=15.0)
            hasil_visual = res_ai.json()
            
            supabase.table("hasil_asesmen").update({
                "kondisi_rumah": hasil_visual["kondisi"]
            }).eq("warga_id", warga_id).execute()
            
            return hasil_visual
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Server API Visual (Tim 2) tidak merespon")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses visual: {str(e)}")