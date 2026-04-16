import uuid
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from database import Base

# --- TABEL 1: USER (UNTUK LOGIN) ---
class User(Base):
    __tablename__ = "user"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)

# --- TABEL 2: KELUARGA (DATA ASESMEN SOSIAL) ---
class Keluarga(Base):
    __tablename__ = "keluarga"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    kode_provinsi = Column(String(10))
    provinsi = Column(String(100))
    kode_kabupaten_kota = Column(String(15))
    kabupaten_kota = Column(String(100))
    kode_kecamatan = Column(String(20))
    kecamatan = Column(String(100))
    kode_kelurahan_desa = Column(String(25))
    kelurahan_desa = Column(String(100))
    alamat = Column(String(500))
    nomor_kartu_keluarga = Column(String(16), unique=True, index=True)
    jumlah_anggota_keluarga = Column(Integer)
    nama_anggota_keluarga = Column(String(500))
    pbi_nas = Column(Boolean)
    pbi_pemda = Column(Boolean)
    id_pelanggan_pln = Column(String(20), nullable=True)
    status_kepemilikan_rumah = Column(SmallInteger)
    jenis_lantai_terluas = Column(SmallInteger)
    luas_lantai = Column(Integer)
    jenis_dinding_terluas = Column(SmallInteger)
    jenis_atap_terluas = Column(SmallInteger)
    sumber_air_minum_utama = Column(SmallInteger)
    sumber_penerangan_utama = Column(SmallInteger)
    daya_terpasang = Column(SmallInteger)
    bahan_bakar_utama_memasak = Column(SmallInteger)
    fasilitas_bab = Column(SmallInteger)
    jenis_kloset = Column(SmallInteger)
    pembuangan_akhir_tinja = Column(SmallInteger)
    kepemilikan_aset = Column(Boolean)
    aset_bergerak_tabung_gas = Column(Boolean)
    aset_bergerak_lemari_es = Column(Boolean)
    aset_bergerak_ac = Column(Boolean)
    aset_bergerak_pemanas_air = Column(Boolean)
    aset_bergerak_telepon_rumah = Column(Boolean)
    aset_bergerak_tv_datar = Column(Boolean)
    aset_bergerak_emas_perhiasan = Column(Boolean)
    aset_bergerak_komputer_laptop_tablet = Column(Boolean)
    aset_bergerak_sepeda_motor = Column(Boolean)
    aset_bergerak_sepeda = Column(Boolean)
    aset_bergerak_mobil = Column(Boolean)
    aset_bergerak_perahu = Column(Boolean)
    aset_bergerak_kapal_perahu_motor = Column(Boolean)
    aset_bergerak_smartphone = Column(Boolean)
    aset_tidak_bergerak_lahan_lainnya = Column(Boolean)
    aset_tidak_bergerak_rumah_lainnya = Column(Boolean)
    jumlah_ternak_sapi = Column(Integer)
    jumlah_ternak_kerbau = Column(Integer)
    jumlah_ternak_kuda = Column(Integer)
    jumlah_ternak_babi = Column(Integer)
    jumlah_ternak_kambing_domba = Column(Integer)
    skor = Column(Integer, nullable=True)
    desil_nasional = Column(Integer, nullable=True)

# --- TABEL 3: PERHITUNGAN (HASIL AI) ---
class Perhitungan(Base):
    __tablename__ = "perhitungan"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keluarga_id = Column(UUID(as_uuid=True), ForeignKey("keluarga.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    
    desil_kemiskinan = Column(String)
    rekomendasi_bantuan = Column(String)
    kondisi_rumah = Column(String, nullable=True)
    foto_url = Column(String, nullable=True)
    status_validasi = Column(String, default="Menunggu")