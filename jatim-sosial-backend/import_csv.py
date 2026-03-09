import csv
import httpx
import asyncio
import random

# --- KONFIGURASI ---
CSV_FILE = "data_tim1.csv"
BASE_URL = "http://127.0.0.1:8000"
EMAIL_PETUGAS = "admin@jatim.go.id"
PASSWORD_PETUGAS = "sandi123"

async def main():
    async with httpx.AsyncClient() as client:
        print("1. Melakukan Login...")
        res_login = await client.post(f"{BASE_URL}/auth/login", data={"username": EMAIL_PETUGAS, "password": PASSWORD_PETUGAS})
        
        if res_login.status_code != 200:
            print("Gagal Login. Cek email/password Supabase Anda.")
            return
            
        headers = {"Authorization": f"Bearer {res_login.json()['access_token']}"}
        print("Login Berhasil! Memulai import dataset Tim 1...\n")

        try:
            with open(CSV_FILE, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                sukses = 0
                gagal = 0
                
                for idx, row in enumerate(reader, start=1):
                    if idx > 10: 
                        break

                    # 2. MEMBUAT DATA YANG COCOK DENGAN API KITA
                    nik_dummy = f"3573{random.randint(100000000000, 999999999999)}"
                    nama_dummy = f"Warga Uji Coba {idx}"
                    
                    data_warga = {
                        "nik": nik_dummy,
                        "nama": nama_dummy,
                        # Mengambil dari CSV Tim 1
                        "pendapatan": float(row["pendapatan"]),
                        "jumlah_tanggungan": int(row["jumlah_anggota"]), 
                        "pendidikan": row["pendidikan"]
                    }
                    
                    print(f"Mengirim Data ke-{idx}: {nama_dummy} (Pendapatan: Rp{data_warga['pendapatan']})...")
                    
                    # 3. KIRIM KE API ORKESTRASI ANDA
                    res_api = await client.post(
                        f"{BASE_URL}/api/v1/asesmen/sosial", 
                        json=data_warga, 
                        headers=headers,
                        timeout=None
                    )
                    
                    if res_api.status_code == 200:
                        hasil = res_api.json()
                        print(f"  -> SUKSES! Model menjawab: Desil {hasil['klasifikasi_tim1']['desil']} -> {hasil['rekomendasi_tim3']['rekomendasi'][0]['program']}")
                        sukses += 1
                    else:
                        print(f"  -> GAGAL: {res_api.text}")
                        gagal += 1
                        
                print(f"\n--- SELESAI ---")
                print(f"Berhasil masuk ke Supabase: {sukses} data")
                
        except FileNotFoundError:
            print(f"File {CSV_FILE} tidak ditemukan. Pastikan letaknya di folder yang sama.")
        except KeyError as e:
            print(f"Error: Kolom {e} tidak ditemukan di CSV. Pastikan nama kolom di baris pertama CSV persis sama.")

if __name__ == "__main__":
    asyncio.run(main())