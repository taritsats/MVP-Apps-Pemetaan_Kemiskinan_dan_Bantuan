import uvicorn
import schemas
from fastapi import FastAPI, UploadFile, File, Body

app = FastAPI(title="Pusat Mock API Tim AI (1, 2, 3)", version="1.0")

# 1. MOCK API TIM 1 (KLASIFIKASI DESIL)
@app.post("/api/ai/tim1-klasifikasi", tags=["Tim 1 - LLM"])
async def klasifikasi_tim1(data: schemas.KeluargaResponse):

    id = data.id
    kode_provinsi = data.kode_provinsi
    provinsi = data.provinsi
    kode_kabupaten_kota = data.kode_kabupaten_kota
    kabupaten_kota = data.kabupaten_kota
    kode_kecamatan = data.kode_kecamatan
    kecamatan = data.kecamatan
    kode_kelurahan_desa = data.kode_kelurahan_desa
    kelurahan_desa = data.kelurahan_desa
    alamat = data.alamat
    nomor_kartu_keluarga = data.nomor_kartu_keluarga
    jumlah_anggota_keluarga = data.jumlah_anggota_keluarga
    nama_anggota_keluarga = data.nama_anggota_keluarga
    pbi_nas = data.pbi_nas
    pbi_pemda = data.pbi_pemda
    id_pelanggan_pln = data.id_pelanggan_pln
    status_kepemilikan_rumah = data.status_kepemilikan_rumah
    jenis_lantai_terluas = data.jenis_lantai_terluas
    luas_lantai = data.luas_lantai
    jenis_dinding_terluas = data.jenis_dinding_terluas
    jenis_atap_terluas = data.jenis_atap_terluas
    sumber_air_minum_utama = data.sumber_air_minum_utama
    sumber_penerangan_utama = data.sumber_penerangan_utama
    daya_terpasang = data.daya_terpasang
    bahan_bakar_utama_memasak = data.bahan_bakar_utama_memasak
    fasilitas_bab = data.fasilitas_bab
    jenis_kloset = data.jenis_kloset
    pembuangan_akhir_tinja = data.pembuangan_akhir_tinja
    kepemilikan_aset = data.kepemilikan_aset
    aset_bergerak_tabung_gas = data.aset_bergerak_tabung_gas
    aset_bergerak_lemari_es = data.aset_bergerak_lemari_es
    aset_bergerak_ac = data.aset_bergerak_ac
    aset_bergerak_pemanas_air = data.aset_bergerak_pemanas_air
    aset_bergerak_telepon_rumah = data.aset_bergerak_telepon_rumah
    aset_bergerak_tv_datar = data.aset_bergerak_tv_datar
    aset_bergerak_emas_perhiasan = data.aset_bergerak_emas_perhiasan
    aset_bergerak_komputer_laptop_tablet = data.aset_bergerak_komputer_laptop_tablet
    aset_bergerak_sepeda_motor = data.aset_bergerak_sepeda_motor
    aset_bergerak_sepeda = data.aset_bergerak_sepeda
    aset_bergerak_mobil = data.aset_bergerak_mobil
    aset_bergerak_perahu = data.aset_bergerak_perahu
    aset_bergerak_kapal_perahu_motor = data.aset_bergerak_kapal_perahu_motor
    aset_bergerak_smartphone = data.aset_bergerak_smartphone
    aset_tidak_bergerak_lahan_lainnya = data.aset_tidak_bergerak_lahan_lainnya
    aset_tidak_bergerak_rumah_lainnya = data.aset_tidak_bergerak_rumah_lainnya
    jumlah_ternak_sapi = data.jumlah_ternak_sapi
    jumlah_ternak_kerbau = data.jumlah_ternak_kerbau
    jumlah_ternak_kuda = data.jumlah_ternak_kuda
    jumlah_ternak_babi = data.jumlah_ternak_babi
    jumlah_ternak_kambing_domba = data.jumlah_ternak_kambing_domba
    skor = data.skor
    desil_nasional = data.desil_nasional
    
    if not aset_bergerak_sepeda_motor and not aset_bergerak_lemari_es:
        desil = 1
        kategori = "Sangat Miskin (Desil 1)"
    else:
        desil = 4
        kategori = "Rentan Miskin (Desil 4)"

    return {
        "status": "success",
        "desil": desil,
        "kategori_kesejahteraan": kategori,
        "id_keluarga": str(id),
        "reasoning": f"Analisis Mock Model: Berdasarkan input ketiadaan aset motor={aset_bergerak_sepeda_motor} dan kulkas={aset_bergerak_lemari_es}, diputuskan masuk ke Desil {desil}."
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

    reasoning = data.get("reasoning", None)
    
    if reasoning:
        bantuan = ["Bantuan Renovasi Rumah", "Bantuan Perbaikan Sanitasi"]
        alasan = "Rekomendasi berdasarkan hasil klasifikasi desil 1 dan analisis visual yang menunjukkan kondisi rumah tidak layak huni."
        return {
            "status": "success",
            "rekomendasi_bantuan": bantuan,
            "reasoning_rekomendasi": alasan
        }
    else:
        return {
            "status": "error",
            "message": "Reasoning dari model klasifikasi dan visual diperlukan untuk memberikan rekomendasi yang tepat."
        }

if __name__ == "__main__":
    print("Menjalankan Mock Server AI di Port 8001...")
    uvicorn.run(app, host="127.0.0.1", port=8001)