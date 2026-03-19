from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from database import get_db
from utils.dependencies import get_current_admin
from schemas.students import StudentResponse, StudentCreate, StudentUpdate
from services.student import StudentService
from services.notification import NotificationService
from models import Student


router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=list[StudentResponse])
def list_students(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    service = StudentService(db)
    return service.list_students()


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    try:
        service = StudentService(db)
        student = service.create_student(payload.model_dump())
        return {"message": "Student created successfully", "student": student}
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error creating student")


@router.put("/{student_id}", response_model=dict)
def update_student(
    student_id: str,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    try:
        service = StudentService(db)
        student = service.update_student(student_id, payload.model_dump(exclude_unset=True))
        return {"message": "Student updated successfully", "student": student}
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error updating student")


@router.delete("/{student_id}", response_model=dict)
def delete_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    try:
        student = db.execute(
            select(Student)
            .where(Student.id == student_id)
            .options(joinedload(Student.user))
        ).unique().scalar_one_or_none()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        student_name = student.user.name if student.user else "Student"
        service = StudentService(db)
        service.delete_student(student_id)
        NotificationService(db).create_for_roles(
            roles=["ADMIN", "HOSTEL_MANAGER"],
            title="Student removed",
            message=f"{student_name} was removed from the system by {current_user.name}.",
            type_value="SYSTEM",
            data={"link": "/admin/students"},
        )
        return {"message": "Student deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
