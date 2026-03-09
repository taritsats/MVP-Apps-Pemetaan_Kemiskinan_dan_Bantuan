import asyncio
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI(title="API dummy (Tim 1, 2, 3)", version="3.0")

class ProfilWargaRequest(BaseModel):
    pendapatan: float
    jumlah_tanggungan: int
    pendidikan: str

class RekomendasiRequest(ProfilWargaRequest):
    desil: int # Tim 3 butuh tahu desil warga dari Tim 1

# --- API 1: Tim 1 (Klasifikasi Sosial / Penentuan Desil) ---
@app.post("/api/ai/tim1-klasifikasi")
async def api_tim_1(data: ProfilWargaRequest):
    await asyncio.sleep(1)
    desil = 1 if data.pendapatan < 1500000 else 3
    kategori = "Sangat Rentan" if desil == 1 else "Rentan"
    return {"desil": desil, "kategori": kategori}

# --- API 2: Tim 3 (Rekomendasi Program Bantuan) ---
@app.post("/api/ai/tim3-rekomendasi")
async def api_tim_3(data: RekomendasiRequest):
    await asyncio.sleep(1)
    rekomendasi = []
    # Logika: Jika desil 1 (Sangat Rentan), berikan PKH
    if data.desil == 1:
        rekomendasi.append({"program": "Program Keluarga Harapan (PKH)", "dasar": "Permensos"})
    else:
        rekomendasi.append({"program": "Bantuan Pangan Non Tunai (BPNT)", "dasar": "Permensos"})
    return {"rekomendasi": rekomendasi}

# --- API 3: Tim 2 (Analisis Visual / Kondisi Rumah) ---
@app.post("/api/ai/tim2-visual")
async def api_tim_2(file: UploadFile = File(...)):
    await asyncio.sleep(2)
    return {"kondisi": "Tidak Layak Huni", "confidence": 0.89}