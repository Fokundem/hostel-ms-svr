import asyncio
import traceback
from database import connect_db
from db import get_db_session
from services.student import StudentService
from services.allocation import AllocationService
from models import Student, Room, RoleEnum
from schemas.auth import RegisterRequest
from services.auth import AuthService

async def main():
    await connect_db()
    for session in get_db_session():
        try:
            auth_service = AuthService(session)
            student_data = auth_service.register(RegisterRequest(
                email="test_cascade@example.com",
                password="password123",
                name="Cascade Test",
                phone="123456789",
                role="STUDENT",
                matricule="MAT_CASCADE_1",
                department="CS",
                level="200"
            ))
            student_user_id = student_data["id"]
            
            student = session.execute(
                "SELECT id FROM \"Student\" WHERE \"matricule\" = 'MAT_CASCADE_1'"
            ).scalar_one()
            
            room = session.execute("SELECT id FROM \"Room\" LIMIT 1").scalar_one()
            
            alloc_service = AllocationService(session)
            alloc_service.request_room(student, student_user_id, room)
            
            print("Created student and allocation. Now attempting delete...")
            
            student_service = StudentService(session)
            student_service.delete_student(student)
            print("Successfully deleted student with relations!")
        except Exception as e:
            print("DELETION FAILED:")
            traceback.print_exc()
        finally:
            # clean up
            session.rollback()
            session.execute("DELETE FROM \"User\" WHERE email = 'test_cascade@example.com'")
            session.commit()
        break

asyncio.run(main())
