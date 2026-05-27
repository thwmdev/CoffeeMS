import jwt
import datetime

SECRET_KEY = "your_secret"

payload = {
    "user_id": 1,
    "role": "manager",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}

token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

print(token)