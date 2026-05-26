from fastapi import APIRouter

router = APIRouter()

menu = []

@router.post("/them-mon")
def them_mon(
    ten_mon: str,
    gia: float
):

    mon = {
        "ten_mon": ten_mon,
        "gia": gia
    }

    menu.append(mon)

    return {
        "message": "Thêm món thành công",
        "data": mon
    }