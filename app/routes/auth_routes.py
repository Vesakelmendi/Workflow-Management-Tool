from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional

from ..services.auth_service import AuthService
from ..models.user import UserCreate, UserResponse

router = APIRouter(prefix="/api", tags=["authentication"])


class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

class LoginResponse(BaseModel):
    success: bool = True
    user: UserResponse
    message: str = "Authentication successful"

class RegisterResponse(BaseModel):
    success: bool = True
    user: UserResponse
    message: str = "User created successfully"

# Routes
@router.post("/authenticate", response_model=LoginResponse)
async def authenticate(login_data: LoginRequest):
    """
    Authenticates a user with their username/email and password.
    """
    user = None

    if login_data.username:
        user = AuthService.authenticate_user(login_data.username, login_data.password)
    elif login_data.email:
        u = AuthService.get_user_by_email(login_data.email)
        if u and AuthService.verify_password(login_data.password, u.password):
            user = UserResponse(
                id=u.id,
                email=u.email,
                username=u.username,
                roles=u.roles
            )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    return LoginResponse(user=user)

@router.post("/register", response_model=RegisterResponse)
async def register(user_data: UserCreate):
    """
    Registers a new user with default 'user' role.
    """
    try:
        new_user = AuthService.create_user(user_data)
        return RegisterResponse(user=new_user)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
