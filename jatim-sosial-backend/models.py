from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

# 1. Tabel User (Petugas/Analis Dinas)
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="petugas")
    
    perhitungan_divalidasi = relationship("Perhitungan", back_populates="petugas")

# 2. Tabel Keluarga (Data Demografi & Input)
class Keluarga(Base):
    __tablename__ = "keluarga"

    id = Column(Integer, primary_key=True, index=True)
    no_kk = Column(String, unique=True, index=True, nullable=False)
    nama_kepala_keluarga = Column(String, nullable=False)
    alamat = Column(Text, nullable=False)
    foto_rumah_url = Column(String, nullable=True) # Disimpan sebagai URL object storage
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    analisis = relationship("Perhitungan", back_populates="keluarga", uselist=False)

# 3. Tabel Perhitungan (Hasil Integrasi Model 1, 2, dan 3)
class Perhitungan(Base):
    __tablename__ = "perhitungan"

    id = Column(Integer, primary_key=True, index=True)
    keluarga_id = Column(Integer, ForeignKey("keluarga.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    
    # Output dari Model AI
    desil_kemiskinan = Column(String, nullable=True)     # Hasil Model 1 (Teks)
    kondisi_rumah = Column(String, nullable=True)        # Hasil Model 2 (VLM)
    rekomendasi_bantuan = Column(Text, nullable=True)    # Hasil Model 3 (RAG)
    
    # Status Human-in-the-loop
    status_validasi = Column(String, default="Menunggu")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relasi balik (Back-populates) agar ORM bisa saling membaca
    keluarga = relationship("Keluarga", back_populates="analisis")
    petugas = relationship("User", back_populates="perhitungan_divalidasi")