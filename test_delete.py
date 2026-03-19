import asyncio
import traceback
from database import get_db, connect_db
from db import get_db_session
from services.student import StudentService
from sqlalchemy import select
from models import Student

async def main():
    await connect_db()
    for session in get_db_session():
        # Get any student
        student = session.execute(select(Student)).scalars().first()
        if not student:
            print("No students found.")
            return
            
        print(f"Attempting to delete student {student.id}")
        service = StudentService(session)
        try:
            service.delete_student(student.id)
            print("Success")
        except Exception as e:
            print("ERROR:")
            traceback.print_exc()
        break

asyncio.run(main())
