import os
import httpx
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from uuid import UUID
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import models
import schemas
from database import engine, get_db
import csv
import io

# BAGIAN 1: SETUP AWAL
load_dotenv()
models.Base.metadata.create_all(bind=engine)

# BAGIAN 2: KONFIGURASI MINIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin_minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = "foto-rumah-warga"

s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

def ensure_bucket_exists():
    try:
        s3_client.head_bucket(Bucket=MINIO_BUCKET)
    except ClientError:
        s3_client.create_bucket(Bucket=MINIO_BUCKET)
        print(f"[MinIO] Bucket '{MINIO_BUCKET}' berhasil dibuat.")

try:
    ensure_bucket_exists()
except Exception as e:
    print(f"[MinIO] Peringatan: Tidak bisa terhubung ke MinIO → {e}")

# BAGIAN 3: KONFIGURASI KEAMANAN JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# BAGIAN 4: INISIALISASI APLIKASI FASTAPI
app = FastAPI(
    title="API Pemetaan Kemiskinan Jatim",
    version="2.1",
    description="Backend MVP Tim 4 — Mengorkestrasi alur data dari Tim 1, 2, dan 3."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AI_BASE_URL = os.getenv("AI_BASE_URL", "http://127.0.0.1:8001")

# BAGIAN 5: DEPENDENCY — PENJAGA PINTU AUTENTIKASI
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token tidak memiliki identitas pengguna.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid atau sudah kadaluarsa.")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Pengguna tidak ditemukan.")
    return user

# BAGIAN 6: ENDPOINT AUTENTIKASI
@app.post("/auth/buat-admin", tags=["Auth"], summary="Buat akun admin default (sekali pakai)")
def buat_admin(db: Session = Depends(get_db)):

    if db.query(models.User).filter(models.User.username == "admin_jatim").first():
        return {"pesan": "Akun admin sudah ada, tidak perlu dibuat ulang."}
    
    db.add(models.User(
        username="admin_jatim",
        email="admin@dinsos.go.id",
        password_hash=get_password_hash("ADMIN_PASSWORD")
    ))
    db.commit()
    return {"pesan": "Akun admin berhasil dibuat."}


@app.post("/auth/login", tags=["Auth"], summary="Login dan dapatkan token JWT")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Username atau password salah.")
    
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# BAGIAN 7: IMPORT CSV (MASTER DATA)
@app.post(
    "/api/v1/import-csv",
    tags=["1. Import Master Data"],
    summary="Sinkronisasi data warga dari file CSV"
)
async def import_csv(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):

    contents = await file.read()
    reader = csv.DictReader(io.StringIO(contents.decode("utf-8")))

    kolom_sah = [c.name for c in models.Keluarga.__table__.columns]
    kk_existing = {k[0] for k in db.query(models.Keluarga.nomor_kartu_keluarga).all()}
    
    sukses = 0
    di_skip = 0
    objek_baru = []

    for row in reader:
        try:
            no_kk_row = row.get("nomor_kartu_keluarga")

            # Skip baris tanpa nomor KK atau yang sudah ada di database
            if not no_kk_row or no_kk_row in kk_existing:
                di_skip += 1
                continue

            data_bersih = {}
            for k, v in row.items():
                if not k or k not in kolom_sah:
                    continue

                val_str = str(v).strip().upper() if v else ""

                if k.startswith("kode_"):
                    data_bersih[k] = val_str.replace(".", "")

                elif k.startswith("aset_") or k.startswith("pbi_") or k == "kepemilikan_aset":
                    data_bersih[k] = val_str in ["YA", "1", "TRUE"]

                elif k in ["skor", "desil_nasional"]:
                    try:
                        data_bersih[k] = int(float(v)) if v else None
                    except ValueError:
                        data_bersih[k] = None

                elif k.startswith("jumlah_") or k in [
                    "luas_lantai", "daya_terpasang",
                    "status_kepemilikan_rumah", "jenis_lantai_terluas",
                    "jenis_dinding_terluas", "jenis_atap_terluas",
                    "sumber_air_minum_utama", "sumber_penerangan_utama",
                    "bahan_bakar_utama_memasak", "fasilitas_bab",
                    "jenis_kloset", "pembuangan_akhir_tinja"
                ]:
                    try:
                        data_bersih[k] = int(float(v)) if v else 0
                    except ValueError:
                        data_bersih[k] = 0

                else:
                    data_bersih[k] = v

            objek_baru.append(models.Keluarga(**data_bersih))
            kk_existing.add(no_kk_row)
            sukses += 1

        except Exception:
            di_skip += 1
            continue

    if objek_baru:
        db.add_all(objek_baru)
        db.commit()

    return {
        "status": "Sukses",
        "pesan": f"{sukses} data berhasil diimpor, {di_skip} baris di-skip (duplikat/error)."
    }

# BAGIAN 8: ASESMEN SOSIAL — TIM 1 & TIM 3
@app.post(
    "/api/v1/asesmen/sosial",
    tags=["2. Asesmen Tim 1 & 3"],
    summary="Jalankan analisis LLM + RAG untuk satu keluarga"
)
async def asesmen_sosial(
    payload: schemas.TriggerAsesmenRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Step 1: Ambil data keluarga
    keluarga = db.query(models.Keluarga).filter(
        models.Keluarga.id == payload.keluarga_id
    ).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Data keluarga tidak ditemukan.")

    try:
        # Step 2: Siapkan data sebagai dictionary untuk dikirim ke AI
        data_untuk_ai = {
            c.name: getattr(keluarga, c.name)
            for c in models.Keluarga.__table__.columns
        }
        data_untuk_ai.pop("id", None)  # ID internal tidak perlu dikirim ke AI

        async with httpx.AsyncClient() as client:

            # Step 3a: Panggil Tim 1 — LLM Klasifikasi Desil
            try:
                res_tim1 = await client.post(
                    f"{AI_BASE_URL}/api/ai/tim1-klasifikasi",
                    json=data_untuk_ai,
                    timeout=15.0
                )
                res_tim1.raise_for_status()
                hasil_tim1 = res_tim1.json()
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Tim 1 tidak dapat dihubungi: {e}")
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=502, detail=f"Tim 1 mengembalikan error: {e}")

            desil_baru = str(hasil_tim1.get("desil", 0))
            skor_baru = int(hasil_tim1.get("skor_prioritas", 0))

            # Step 3b: Panggil Tim 3 — RAG Rekomendasi Bantuan
            data_untuk_ai["desil"] = desil_baru
            try:
                res_tim3 = await client.post(
                    f"{AI_BASE_URL}/api/ai/tim3-rekomendasi",
                    json=data_untuk_ai,
                    timeout=15.0
                )
                res_tim3.raise_for_status()
                hasil_tim3 = res_tim3.json()
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Tim 3 tidak dapat dihubungi: {e}")
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=502, detail=f"Tim 3 mengembalikan error: {e}")

            rekomendasi_baru = hasil_tim3.get("rekomendasi_bantuan", [])

        # Step 4: Ambil atau buat record Perhitungan
        hitung = db.query(models.Perhitungan).filter(
            models.Perhitungan.keluarga_id == keluarga.id
        ).first()

        desil_lama = None
        bantuan_lama = None

        if not hitung:
            # Pertama kali diasesmen → buat record baru
            hitung = models.Perhitungan(
                keluarga_id=keluarga.id,
                user_id=current_user.id,
            )
            db.add(hitung)
        else:
            # Sudah pernah diasesmen → simpan nilai lama untuk log
            desil_lama = hitung.desil_kemiskinan
            bantuan_lama = hitung.rekomendasi_bantuan

        # Step 5: Update tabel Perhitungan dengan hasil baru
        hitung.desil_kemiskinan = desil_baru
        hitung.skor_prioritas = skor_baru
        hitung.rekomendasi_bantuan = rekomendasi_baru

        # Step 6: Tulis audit trail ke LogHistori
        log = models.LogHistori(
            keluarga_id=keluarga.id,
            user_id=current_user.id,
            desil_lama=desil_lama,
            desil_baru=desil_baru,
            bantuan_lama=bantuan_lama,
            bantuan_baru=rekomendasi_baru
        )
        db.add(log)
        db.commit()

        return {
            "status": "Sukses",
            "nomor_kk": keluarga.nomor_kartu_keluarga,
            "hasil_ai": {
                "desil": desil_baru,
                "skor_prioritas": skor_baru,
                "rekomendasi_bantuan": rekomendasi_baru
            }
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Kesalahan internal: {str(e)}")

# BAGIAN 9: ASESMEN VISUAL — TIM 2
@app.post(
    "/api/v1/asesmen/visual/{id_keluarga}",
    tags=["3. Asesmen Tim 2"],
    summary="Upload foto rumah dan jalankan analisis visual AI"
)
async def asesmen_visual(
    id_keluarga: UUID,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Step 1: Validasi keluarga ada
    keluarga = db.query(models.Keluarga).filter(
        models.Keluarga.id == id_keluarga
    ).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Data keluarga tidak ditemukan.")

    try:
        # Step 2: Baca isi file dan upload ke MinIO
        content = await file.read()
        nama_unik = f"{id_keluarga}_{file.filename}"
        s3_client.put_object(
            Bucket=MINIO_BUCKET,
            Key=nama_unik,
            Body=content,
            ContentType=file.content_type
        )
        url_foto = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{nama_unik}"

        # Step 3: Reset pointer file lalu kirim ke Tim 2
        await file.seek(0)
        try:
            async with httpx.AsyncClient() as client:
                files_payload = {"file": (file.filename, file.file, file.content_type)}
                res_ai = await client.post(
                    f"{AI_BASE_URL}/api/ai/tim2-visual",
                    files=files_payload,
                    timeout=30.0  # visual model butuh lebih lama
                )
                res_ai.raise_for_status()
                hasil_ai = res_ai.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Tim 2 tidak dapat dihubungi: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Tim 2 mengembalikan error: {e}")

        kondisi_teks = hasil_ai.get("reasoning_visual") or str(hasil_ai)

        # Step 4: Simpan ke tabel Perhitungan
        hitung = db.query(models.Perhitungan).filter(
            models.Perhitungan.keluarga_id == keluarga.id
        ).first()
        if not hitung:
            hitung = models.Perhitungan(
                keluarga_id=keluarga.id,
                user_id=current_user.id
            )
            db.add(hitung)

        hitung.kondisi_rumah = kondisi_teks
        hitung.foto_url = url_foto
        db.commit()

        return {
            "status": "Sukses",
            "url_foto": url_foto,
            "analisis_ai": hasil_ai
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Kesalahan internal: {str(e)}")

# BAGIAN 10: ENDPOINT READ DATA (GET)
@app.get(
    "/api/v1/keluarga",
    tags=["4. Read Data"],
    summary="Ambil daftar semua keluarga (dengan pagination)"
)
async def list_keluarga(
    skip: int = 0,
    limit: int = 20,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    total = db.query(models.Keluarga).count()
    data = db.query(models.Keluarga).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [schemas.KeluargaResponse.from_orm(k) for k in data]
    }

@app.get(
    "/api/v1/keluarga/{keluarga_id}",
    tags=["4. Read Data"],
    summary="Ambil detail satu keluarga berdasarkan ID"
)
async def get_keluarga(
    keluarga_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mengembalikan detail lengkap data keluarga beserta hasil asesmen AI jika sudah ada."""
    keluarga = db.query(models.Keluarga).filter(
        models.Keluarga.id == keluarga_id
    ).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Data keluarga tidak ditemukan.")


    return {
        "keluarga": schemas.KeluargaResponse.from_orm(keluarga),
    }

@app.get(
    "/api/v1/keluarga/{keluarga_id}/histori",
    tags=["4. Read Data"],
    summary="Lihat riwayat perubahan asesmen satu keluarga"
)
async def get_histori(
    keluarga_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    logs = db.query(models.LogHistori).filter(
        models.LogHistori.keluarga_id == keluarga_id
    ).order_by(models.LogHistori.timestamp.desc()).all()

    return {
        "keluarga_id": str(keluarga_id),
        "jumlah_riwayat": len(logs),
        "riwayat": [
            {
                "timestamp": log.timestamp,
                "desil_lama": log.desil_lama,
                "desil_baru": log.desil_baru,
                "bantuan_lama": log.bantuan_lama,
                "bantuan_baru": log.bantuan_baru,
            }
            for log in logs
        ]
    }

