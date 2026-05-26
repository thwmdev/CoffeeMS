from app.schemas.auth import LoginRequest

class LoginRequest(BaseModel):
    username: str
    password: str