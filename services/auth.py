from prisma import Prisma
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.exceptions import InvalidCredentialsException, UserAlreadyExistsException
from app.schemas.auth import RegisterRequest, LoginRequest
from datetime import timedelta
from app.settings import settings


class AuthService:
    def __init__(self, db: Prisma):
        self.db = db

    async def register(self, user_data: RegisterRequest) -> dict:
        """Register a new user"""
        # Check if user already exists
        existing_user = await self.db.user.find_unique(where={"email": user_data.email})
        if existing_user:
            raise UserAlreadyExistsException()

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user
        new_user = await self.db.user.create(
            data={
                "email": user_data.email,
                "password": hashed_password,
                "name": user_data.name,
                "phone": user_data.phone,
                "role": user_data.role,
            }
        )

        # If registering as student, create student profile
        if user_data.role == "STUDENT":
            if not user_data.matricule or not user_data.department or not user_data.level:
                # Clean up user if student data is incomplete
                await self.db.user.delete(where={"id": new_user.id})
                raise ValueError("Student must provide matricule, department, and level")

            await self.db.student.create(
                data={
                    "userId": new_user.id,
                    "matricule": user_data.matricule,
                    "department": user_data.department,
                    "level": user_data.level,
                    "guardianContact": user_data.guardianContact,
                }
            )

        return {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "role": new_user.role,
            "status": new_user.status,
        }

    async def login(self, credentials: LoginRequest) -> dict:
        """Login user and return JWT token"""
        # Find user by email
        user = await self.db.user.find_unique(where={"email": credentials.email})
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
                "role": user.role,
                "phone": user.phone,
                "avatar": user.avatar,
                "status": user.status,
            },
        }

    async def get_user(self, user_id: str) -> dict:
        """Get user details"""
        user = await self.db.user.find_unique(where={"id": user_id})
        if not user:
            raise ValueError("User not found")

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "phone": user.phone,
            "avatar": user.avatar,
            "status": user.status,
            "createdAt": user.createdAt.isoformat(),
        }

    async def update_user(self, user_id: str, update_data: dict) -> dict:
        """Update user details"""
        user = await self.db.user.update(
            where={"id": user_id},
            data={k: v for k, v in update_data.items() if v is not None},
        )

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "phone": user.phone,
            "avatar": user.avatar,
            "status": user.status,
        }
