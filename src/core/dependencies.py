from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from src.db.session import get_db
from src.core.config import settings
from src.db.models import User
from src import schemas

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    Validate JWT token and return current user.
    Raises 401 if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Check token expiration
        exp = payload.get("exp")
        if not exp or datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract and validate email
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
            
        # Fetch and validate user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise credentials_exception
            
        # Return a plain dict because downstream routes expect subscriptable access
        return {
            "id": user.id,
            "email": user.email,
            "github_username": user.github_username,
        }
        
    except JWTError:
        raise credentials_exception