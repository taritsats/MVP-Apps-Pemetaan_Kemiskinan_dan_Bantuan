import asyncio
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI(title="Server AI Terpisah (Tim 1+3 & Tim 2)", version="2.0")

class TextAIRequest(BaseModel):
    pendapatan: float
    jumlah_tanggungan: int
    pendidikan: str

# --- API 1: Tim 1 + 3 (Analisis Sosial & Kebijakan) ---
@app.post("/api/ai/text-analysis")
async def text_analysis_api(data: TextAIRequest):
    await asyncio.sleep(1.5)
    desil = 1 if data.pendapatan < 1500000 else 3
    return {
        "klasifikasi": {"desil": desil, "kategori": "Sangat Rentan" if desil == 1 else "Rentan"},
        "rekomendasi": [{"program": "PKH", "dasar_hukum": "Permensos 2023"}] if desil == 1 else []
    }

# --- API 2: Tim 2 (Analisis Visual) ---
@app.post("/api/ai/visual-analysis")
async def visual_analysis_api(file: UploadFile = File(...)):
    await asyncio.sleep(2)
    return {
        "kondisi": "Tidak Layak Huni",
        "temuan": f"Analisis visual {file.filename}: Struktur bangunan rapuh.",
        "confidence": 0.89
    }