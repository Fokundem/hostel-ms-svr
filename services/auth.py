from utils.security import hash_password, verify_password, create_access_token
from utils.exceptions import InvalidCredentialsException, UserAlreadyExistsException
from schemas.auth import RegisterRequest, LoginRequest
from datetime import timedelta
from settings import settings
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import User, Student, RoleEnum, UserStatusEnum


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, user_data: RegisterRequest) -> dict:
        """Register a new user"""
        # Check if user already exists
        existing_user = self.db.execute(select(User).where(User.email == user_data.email)).scalar_one_or_none()
        if existing_user:
            raise UserAlreadyExistsException()

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Ensure role is uppercase to match Prisma Enum
        role = user_data.role.upper()
        role_enum = RoleEnum(role)

        # Create user
        new_user = User(
            email=user_data.email,
            password=hashed_password,
            name=user_data.name,
            phone=user_data.phone,
            role=role_enum,
            status=UserStatusEnum.ACTIVE,
        )
        self.db.add(new_user)
        self.db.flush()

        # If registering as student, create student profile
        if role == "STUDENT":
            if not user_data.matricule or not user_data.department or not user_data.level:
                # Clean up user if student data is incomplete
                self.db.rollback()
                raise ValueError("Student must provide matricule, department, and level")

            # Check if matricule already exists
            existing_student = self.db.execute(
                select(Student).where(Student.matricule == user_data.matricule)
            ).scalar_one_or_none()
            if existing_student:
                # Clean up user
                self.db.rollback()
                raise ValueError(f"Student with matricule {user_data.matricule} already exists")

            self.db.add(
                Student(
                    userId=new_user.id,
                    matricule=user_data.matricule,
                    department=user_data.department,
                    level=user_data.level,
                    guardianContact=user_data.guardianContact,
                )
            )

        self.db.commit()

        return {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "role": new_user.role.value,
            "status": new_user.status.value,
        }

    def login(self, credentials: LoginRequest) -> dict:
        """Login user and return JWT token"""
        # Find user by email
        user = self.db.execute(select(User).where(User.email == credentials.email)).scalar_one_or_none()
        if not user:
            raise InvalidCredentialsException()

        # Verify password
        if not verify_password(credentials.password, user.password):
            raise InvalidCredentialsException()

        # Check user status
        if user.status != "ACTIVE":
            raise InvalidCredentialsException(f"User account is {user.status}")

        # Create JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role},
            expires_delta=access_token_expires,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
                "phone": user.phone,
                "avatar": user.avatar,
                "status": user.status.value,
            },
        }

    def get_user(self, user_id: str) -> dict:
        """Get user details"""
        user = self.db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "phone": user.phone,
            "avatar": user.avatar,
            "status": user.status.value,
            "createdAt": user.createdAt.isoformat(),
        }

    def update_user(self, user_id: str, update_data: dict) -> dict:
        """Update user details"""
        user = self.db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        for k, v in update_data.items():
            if v is None:
                continue
            setattr(user, k, v)
        self.db.commit()

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "phone": user.phone,
            "avatar": user.avatar,
            "status": user.status.value,
        }
