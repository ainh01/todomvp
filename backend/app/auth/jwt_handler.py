from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import get_settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


class JWTHandler:
    def __init__(self):
        self.settings = get_settings()
        self.secret_key = self.settings.jwt_secret_key
        self.algorithm = self.settings.jwt_algorithm
    
    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def extract_user_id(self, payload: dict) -> str:
        user_id: Optional[str] = payload.get("user_id") or payload.get("sub")
        
        if user_id is None:
            logger.error("JWT payload missing user_id claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user_id claim"
            )
        
        return str(user_id)


jwt_handler = JWTHandler()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    token = credentials.credentials
    payload = jwt_handler.verify_token(token)
    user_id = jwt_handler.extract_user_id(payload)
    
    logger.debug(f"Authenticated user: {user_id}")
    return user_id


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def get_current_user_sse(
    token: Optional[str] = Query(None, description="JWT token for SSE authentication")
) -> str:
    if not token:
        logger.warning("SSE connection attempted without token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token. Use ?token=YOUR_JWT_TOKEN",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = jwt_handler.verify_token(token)
    user_id = jwt_handler.extract_user_id(payload)
    
    logger.info(f"SSE connection authenticated for user: {user_id}")
    return user_id