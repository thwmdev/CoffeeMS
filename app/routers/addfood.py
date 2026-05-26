from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.schemas.mon import MonCreate
from app.models.mon import Mon

from app.database import SessionLocal

router = APIRouter()

# dependency database
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.post("/them-mon")
def them_mon(
    mon: MonCreate,
    db: Session = Depends(get_db)
):

    mon_moi = Mon(

        TenMon = mon.ten_mon,
        GiaBan = mon.gia,
        MoTa = mon.mo_ta,
        MaDM = mon.ma_dm
    )

    db.add(mon_moi)

    db.commit()

    db.refresh(mon_moi)

    return {
        "message": "Thêm món thành công",
        "data": {
            "MaMon": mon_moi.MaMon,
            "TenMon": mon_moi.TenMon
        }
    }