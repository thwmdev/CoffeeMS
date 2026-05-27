from functools import wraps
from flask import request, jsonify
import jwt

SECRET_KEY = "secret-key-demo"


def decode_token(token):
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])


def role_required(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            auth_header = request.headers.get("Authorization")

            if not auth_header:
                return jsonify({"message": "UNAUTHORIZED"}), 401

            try:
                token = auth_header.split(" ")[1]
                payload = decode_token(token)
                user_role = payload.get("role")
            except:
                return jsonify({"message": "INVALID TOKEN"}), 401

            if user_role not in allowed_roles:
                return jsonify({"message": "KHONG CO QUYEN"}), 403

            return func(*args, **kwargs)

        return wrapper
    return decorator