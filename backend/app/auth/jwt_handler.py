"""
JWT token verification and user authentication.
Extracts user_id from JWT claims for request authorization.
"""

from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import get_settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer()


class JWTHandler:
    """
    Handles JWT token verification and user extraction.
    Validates token signature and expiration.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.secret_key = self.settings.jwt_secret_key
        self.algorithm = self.settings.jwt_algorithm
    
    def verify_token(self, token: str) -> dict:
        """
        Verify JWT token and extract payload.
        
        Args:
            token: JWT token string
            
        Returns:
            dict: Token payload containing user claims
            
        Raises:
            HTTPException: If token is invalid or expired
        """
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
        """
        Extract user_id from JWT payload.
        
        Args:
            payload: Decoded JWT payload
            
        Returns:
            str: User ID
            
        Raises:
            HTTPException: If user_id claim is missing
        """
        user_id: Optional[str] = payload.get("user_id") or payload.get("sub")
        
        if user_id is None:
            logger.error("JWT payload missing user_id claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user_id claim"
            )
        
        return str(user_id)


# Global JWT handler instance
jwt_handler = JWTHandler()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    FastAPI dependency for extracting authenticated user ID.
    
    Usage in route:
        @app.get("/protected")
        async def protected_route(user_id: str = Depends(get_current_user)):
            ...
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        str: Authenticated user ID
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = jwt_handler.verify_token(token)
    user_id = jwt_handler.extract_user_id(payload)
    
    logger.debug(f"Authenticated user: {user_id}")
    return user_id


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """
    Optional authentication dependency.
    Returns None if no token provided instead of raising error.
    
    Returns:
        Optional[str]: User ID if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def get_current_user_sse(
    token: Optional[str] = Query(None, description="JWT token for SSE authentication")
) -> str:
    """
    FastAPI dependency for SSE endpoints that accept token via query parameter.
    
    EventSource API doesn't support custom headers, so token must be passed in URL.
    This is a necessary compromise for browser-based SSE connections.
    
    Usage in route:
        @app.get("/stream")
        async def sse_stream(user_id: str = Depends(get_current_user_sse)):
            ...
    
    Args:
        token: JWT token from query parameter
        
    Returns:
        str: Authenticated user ID
        
    Raises:
        HTTPException: If authentication fails or token is missing
        
    Security Note:
        Always use HTTPS in production as token is visible in URL.
        Consider implementing token rotation or short-lived SSE tokens.
    """
    if not token:
        logger.warning("SSE connection attempted without token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token. Use ?token=YOUR_JWT_TOKEN",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Reuse existing token verification logic
    payload = jwt_handler.verify_token(token)
    user_id = jwt_handler.extract_user_id(payload)
    
    logger.info(f"SSE connection authenticated for user: {user_id}")
    return user_id
