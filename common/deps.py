from fastapi import Header, HTTPException, status
from common.security import verify_token, TokenError

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = verify_token(token)
        return payload  # contains sub (email) and role
    except TokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

def require_role(*roles: str):
    async def checker(user=awaitable_dependency(get_current_user)):
        # Placeholder to make FastAPI happy, actual wrapper provided below
        return user
    # Proper dependency factory for FastAPI
    from fastapi import Depends
    async def dep(user: dict = Depends(get_current_user)):
        if user.get("role") not in roles:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user
    return dep
