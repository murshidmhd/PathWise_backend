from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from core.config import settings

bearer_scheme = HTTPBearer()
print("that bearer schema is here ", bearer_scheme)

from fastapi import Request


from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError
from core.config import settings

def verify_token(request: Request) -> dict:
    # 1. Get the header manually to avoid the 'quiet' 401 errors
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    # 2. Extract the token
    token = auth_header.split(" ")[1]

    try:
        # 3. Decode using the Django Secret Key
        payload = jwt.decode(
            token,
            settings.DJANGO_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload 

    except JWTError as e:
        print(f"JWT DECODE ERROR: {str(e)}") # This will show in Docker logs
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired or is invalid",
        )