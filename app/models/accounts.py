from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from app.database import Base

class TaiKhoan(Base):

    __tablename__ = "TAIKHOAN"

    MaTK = Column(
        Integer,
        primary_key=True,
        index=True
    )

    TenDangNhap = Column(
        String(50),
        unique=True,
        nullable=False
    )

    MatKhau = Column(
        String(255),
        nullable=False
    )

    VaiTro = Column(
        String(20),
        nullable=False
    )

    TrangThai = Column(
        String(20),
        nullable=False
    )