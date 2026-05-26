from fastapi import HTTPException, Depends

def role_required(role: str):

    def checker():

        # demo giả lập user
        current_user = {
            "username": "admin",
            "role": "admin"
        }

        if current_user["role"] != role:
            raise HTTPException(
                status_code=403,
                detail="Không đủ quyền"
            )

        return current_user

    return checker