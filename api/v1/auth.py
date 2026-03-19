from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db
from services.auth import AuthService
from schemas.auth import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    UserResponse,
    UserUpdateRequest,
)
from utils.dependencies import get_current_user
from utils.exceptions import InvalidCredentialsException, UserAlreadyExistsException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user (Student, Admin, or Manager)"""
    try:
        service = AuthService(db)
        result = service.register(user_data)
        return {"message": "User registered successfully", "user": result}
    except UserAlreadyExistsException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login user and return JWT token"""
    try:
        service = AuthService(db)
        result = service.login(credentials)
        return result
    except InvalidCredentialsException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_current_user_details(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current authenticated user details"""
    try:
        service = AuthService(db)
        user_data = service.get_user(current_user.id)
        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user details"
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdateRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    try:
        service = AuthService(db)
        updated_user = service.update_user(
            current_user.id,
            update_data.dict(exclude_unset=True)
        )
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user profile"
        )


@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """Logout user (client should discard token)"""
    return {"message": "Logged out successfully"}
