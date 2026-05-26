from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database import get_db

from app.models.accounts import TaiKhoan

from app.schemas.auth import LoginRequest

from app.security.hash import verify_password

from app.security.jwt_handler import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    user = db.query(TaiKhoan).filter(
        TaiKhoan.TenDangNhap == request.username
    ).first()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Sai tài khoản"
        )

    if not verify_password(
        request.password,
        user.MatKhau
    ):

        raise HTTPException(
            status_code=401,
            detail="Sai mật khẩu"
        )

    token = create_access_token({
        "sub": user.TenDangNhap,
        "role": user.VaiTro
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.VaiTro
    }