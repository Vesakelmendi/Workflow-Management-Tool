from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from ..services.auth_service import AuthService
from ..models.user import UserResponse


router = APIRouter(prefix="/api", tags=["authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    user: UserResponse
    message: str


@router.post("/authenticate", response_model=LoginResponse)
async def authenticate(login_data: LoginRequest):
    """Authenticate user with username and password"""
    try:
        user = AuthService.authenticate_user(login_data.username, login_data.password)
        
        if user:
            return LoginResponse(
                success=True,
                user=user,
                message="Authentication successful"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )
