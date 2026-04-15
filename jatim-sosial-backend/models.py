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
    kode_provinsi = Column(String(2))
    nama_provinsi = Column(String(100))
    kode_kabupaten = Column(String(4))
    nama_kabupaten = Column(String(100))
    kode_kecamatan = Column(String(7))
    nama_kecamatan = Column(String(100))
    kode_kelurahan_desa = Column(String(10))
    nama_kelurahan_desa = Column(String(100))
    alamat_domisili = Column(String(500))
    no_kk = Column(String(16), unique=True, index=True)
    nama_kepala_keluarga = Column(String(500))
    jumlah_anggota_keluarga = Column(Integer)
    desil_kesejahteraan_nasional = Column(Integer)
    penerima_bantuan_iuran_nasional = Column(Boolean)
    penerima_bantuan_iuran_pemda = Column(Boolean)
    id_pln = Column(String(20), nullable=True)
    status_kepemilikan_rumah = Column(SmallInteger)
    jenis_lantai = Column(SmallInteger)
    luas_lantai = Column(Integer)
    jenis_dinding = Column(SmallInteger)
    jenis_atap = Column(SmallInteger)
    sumber_air_minum = Column(SmallInteger)
    sumber_penerangan = Column(SmallInteger)
    daya_listrik = Column(SmallInteger)
    bahan_bakar_memasak = Column(SmallInteger)
    fasilitas_bab = Column(SmallInteger)
    jenis_kloset = Column(SmallInteger)
    jenis_pembuangan_akhir = Column(SmallInteger)
    flag_kepemilikan_aset = Column(Boolean)
    kepemilikan_aset_tabung_gas = Column(Boolean)
    kepemilikan_aset_kulkas = Column(Boolean)
    kepemilikan_aset_ac = Column(Boolean)
    kepemilikan_aset_water_heater = Column(Boolean)
    kepemilikan_aset_telepon_rumah = Column(Boolean)
    kepemilikan_aset_televisi_datar = Column(Boolean)
    kepemilikan_aset_perhiasan_emas = Column(Boolean)
    kepemilikan_aset_komputer_laptop_tablet = Column(Boolean)
    kepemilikan_aset_kendaraan_sepeda_motor = Column(Boolean)
    kepemilikan_aset_kendaraan_sepeda = Column(Boolean)
    kepemilikan_aset_kendaraan_mobil = Column(Boolean)
    kepemilikan_aset_kendaraan_perahu = Column(Boolean)
    kepemilikan_aset_kendaraan_kapal = Column(Boolean)
    kepemilikan_aset_smartphone = Column(Boolean)
    kepemilikan_aset_tanah = Column(Boolean)
    kepemilikan_aset_rumah = Column(Boolean)
    jumlah_kepemilikan_ternak_sapi = Column(Integer)
    jumlah_kepemilikan_ternak_kerbau = Column(Integer)
    jumlah_kepemilikan_ternak_kuda = Column(Integer)
    jumlah_kepemilikan_ternak_babi = Column(Integer)
    jumlah_kepemilikan_ternak_kambing_domba = Column(Integer)

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