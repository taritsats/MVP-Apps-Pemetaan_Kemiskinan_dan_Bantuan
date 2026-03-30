from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI(title="Mock Service API AI (Tim 1, 2, 3)")

# --- MOCK TIM 1 (Klasifikasi) ---
@app.post("/api/ai/tim1-klasifikasi")
async def mock_tim1(data: dict):
    return {
        "desil": 1,
        "kategori": "Sangat Miskin",
        "reasoning": "Pendapatan sangat rendah dan tanggungan banyak (Mocked)"
    }

# --- MOCK TIM 2 (Visual Rutilahu) ---
@app.post("/api/ai/tim2-visual")
async def mock_tim2(file: UploadFile = File(...)):
    return {
        "kondisi": "Rusak Berat",
        "confidence": 0.92,
        "catatan": "Atap bocor, dinding retak (Mocked)"
    }

# --- MOCK TIM 3 (Rekomendasi RAG) ---
@app.post("/api/ai/tim3-rekomendasi")
async def mock_tim3(data: dict):
    return {
        "rekomendasi": "Prioritas 1: Program Bantuan Bedah Rumah (Rutilahu) dan PKH Kesehatan.",
        "sumber_aturan": "Pergub Jatim No. 12 Tahun 2023 (Mocked)"
    }