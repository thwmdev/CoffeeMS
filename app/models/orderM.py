from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database import Base

class Mon(Base):

    __tablename__ = "MON"

    MaMon = Column(Integer, primary_key=True, index=True)

    TenMon = Column(String(100), nullable=False)

    GiaBan = Column(Float, nullable=False)

    MoTa = Column(String(255))

    MaDM = Column(Integer, ForeignKey("DANHMUC.MaDM"))