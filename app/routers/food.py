from fastapi import APIRouter
from fastapi import Depends

from app.schemas.food import MonCreate
from app.security.roles import role_required

router = APIRouter(
    prefix="/food",
    tags=["Food"]
)

@router.post("/them-mon")
def them_mon(
    mon: MonCreate,
    user = Depends(role_required("admin"))
):

    return {
        "message": "Thêm món thành công",
        "data": mon
    }