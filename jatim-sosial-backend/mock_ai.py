import uvicorn
from fastapi import FastAPI, UploadFile, File, Body

app = FastAPI(title="Pusat Mock API Tim AI (1, 2, 3)", version="1.0")

# 1. MOCK API TIM 1 (KLASIFIKASI DESIL)
@app.post("/api/ai/tim1-klasifikasi", tags=["Tim 1 - LLM"])
async def klasifikasi_tim1(data: dict = Body(...)):

    aset_motor = data.get("kepemilikan_aset_kendaraan_sepeda_motor", False)
    aset_kulkas = data.get("kepemilikan_aset_kulkas", False)
    
    if not aset_motor and not aset_kulkas:
        desil = 1
        kategori = "Sangat Miskin (Desil 1)"
    else:
        desil = 4
        kategori = "Rentan Miskin (Desil 4)"

    return {
        "status": "success",
        "desil": desil,
        "kategori_kesejahteraan": kategori,
        "reasoning": f"Analisis Mock Model: Berdasarkan input ketiadaan aset motor={aset_motor} dan kulkas={aset_kulkas}, diputuskan masuk ke Desil {desil}."
    }

# 2. MOCK API TIM 2 (ANALISIS VISUAL RUMAH)
@app.post("/api/ai/tim2-visual", tags=["Tim 2 - VisualLM"])
async def visual_tim2(file: UploadFile = File(...)):

    nama_file = file.filename
    
    return {
        "status": "success",
        "nama_file_dianalisis": nama_file,
        "prediksi_material": {
            "jenis_atap": 3,      
            "jenis_dinding": 4,   
            "jenis_lantai": 5    
        },
        "layak_huni": False,
        "reasoning_visual": "Model mendeteksi tekstur kayu lapuk pada dinding (91% confidence) dan lantai tanpa semen (88% confidence)."
    }

# 3. MOCK API TIM 3 (REKOMENDASI BANTUAN)
@app.post("/api/ai/tim3-rekomendasi", tags=["Tim 3 - RAG"])
async def rekomendasi_tim3(data: dict = Body(...)):

    desil = data.get("desil", 0)
    
    if desil <= 2:
        bantuan = ["PKH", "BPNT (Sembako)", "Bantuan Bedah Rumah (RST)"]
        alasan = f"Keluarga berada di Desil {desil}. Prioritas utama untuk intervensi multi-sektor termasuk perbaikan fasilitas fisik rumah."
    else:
        bantuan = ["PBI-JK (BPJS Gratis)"]
        alasan = f"Keluarga berada di Desil {desil}. Disarankan fokus pada jaring pengaman kesehatan."

    return {
        "status": "success",
        "rekomendasi_bantuan": bantuan,
        "reasoning_rekomendasi": alasan
    }

if __name__ == "__main__":
    print("Menjalankan Mock Server AI di Port 8001...")
    uvicorn.run(app, host="127.0.0.1", port=8001)