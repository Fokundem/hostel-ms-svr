from fastapi import APIRouter, Depends, HTTPException, status
from prisma import Prisma

from database import get_db
from utils.dependencies import get_current_admin
from schemas.students import StudentResponse, StudentCreate, StudentUpdate
from services.student import StudentService


router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=list[StudentResponse])
async def list_students(
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    service = StudentService(db)
    return await service.list_students()


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: StudentCreate,
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    try:
        service = StudentService(db)
        student = await service.create_student(payload.model_dump())
        return {"message": "Student created successfully", "student": student}
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error creating student")


@router.put("/{student_id}", response_model=dict)
async def update_student(
    student_id: str,
    payload: StudentUpdate,
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    try:
        service = StudentService(db)
        student = await service.update_student(student_id, payload.model_dump(exclude_unset=True))
        return {"message": "Student updated successfully", "student": student}
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error updating student")


@router.delete("/{student_id}", response_model=dict)
async def delete_student(
    student_id: str,
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    try:
        service = StudentService(db)
        await service.delete_student(student_id)
        return {"message": "Student deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error deleting student")

