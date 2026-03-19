from __future__ import annotations
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Enum as SAEnum,
    Integer,
    Float,
    Boolean,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from db import Base

def _id() -> str:
    return uuid.uuid4().hex


class RoleEnum(str, PyEnum):
    ADMIN = "ADMIN"
    HOSTEL_MANAGER = "HOSTEL_MANAGER"
    STUDENT = "STUDENT"
    EMPLOYEE = "EMPLOYEE"


class UserStatusEnum(str, PyEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class User(Base):
    __tablename__ = "User"

    id = Column(String, primary_key=True, default=_id)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(SAEnum(RoleEnum), nullable=False, default=RoleEnum.STUDENT)
    avatar = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    status = Column(SAEnum(UserStatusEnum), nullable=False, default=UserStatusEnum.ACTIVE)
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="user", uselist=False)


class Student(Base):
    __tablename__ = "Student"

    id = Column(String, primary_key=True, default=_id)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    user = relationship("User", back_populates="student")

    matricule = Column(String, unique=True, nullable=False)
    department = Column(String, nullable=False)
    level = Column(String, nullable=False)
    guardianContact = Column(String, nullable=True)

    roomId = Column(String, ForeignKey("Room.id"), nullable=True)
    room = relationship("Room", back_populates="students")

    payments = relationship("Payment", back_populates="student")
    complaints = relationship("Complaint", back_populates="student")
    visitors = relationship("Visitor", back_populates="student")
    roomAllocations = relationship("RoomAllocation", back_populates="student")

    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Hostel(Base):
    __tablename__ = "Hostel"

    id = Column(String, primary_key=True, default=_id)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    totalRooms = Column(Integer, nullable=False)
    rooms = relationship("Room", back_populates="hostel")
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class RoomStatusEnum(str, PyEnum):
    AVAILABLE = "AVAILABLE"
    FULL = "FULL"
    MAINTENANCE = "MAINTENANCE"


class Room(Base):
    __tablename__ = "Room"

    id = Column(String, primary_key=True, default=_id)
    roomNumber = Column(String, nullable=False)
    floor = Column(String, nullable=False)
    block = Column(String, nullable=False)
    hostelId = Column(String, ForeignKey("Hostel.id", ondelete="CASCADE"), nullable=False)
    hostel = relationship("Hostel", back_populates="rooms")
    capacity = Column(Integer, nullable=False)
    occupied = Column(Integer, nullable=False, default=0)
    status = Column(SAEnum(RoomStatusEnum), nullable=False, default=RoomStatusEnum.AVAILABLE)
    amenities = Column(JSON, nullable=False, default=list)
    price = Column(Float, nullable=False)
    students = relationship("Student", back_populates="room")
    allocations = relationship("RoomAllocation", back_populates="room")
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AllocationStatusEnum(str, PyEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RoomAllocation(Base):
    __tablename__ = "RoomAllocation"

    id = Column(String, primary_key=True, default=_id)
    studentId = Column(String, ForeignKey("Student.id", ondelete="CASCADE"), nullable=False)
    roomId = Column(String, ForeignKey("Room.id", ondelete="CASCADE"), nullable=False)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)

    student = relationship("Student", back_populates="roomAllocations")
    room = relationship("Room", back_populates="allocations")
    user = relationship("User")

    status = Column(SAEnum(AllocationStatusEnum), nullable=False, default=AllocationStatusEnum.PENDING)
    requestedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    approvedAt = Column(DateTime, nullable=True)
    approvedBy = Column(String, nullable=True)
    rejectionReason = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PaymentStatusEnum(str, PyEnum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PAID = "PAID"
    REJECTED = "REJECTED"
    OVERDUE = "OVERDUE"


class PaymentTypeEnum(str, PyEnum):
    HOSTEL_FEE = "HOSTEL_FEE"
    MAINTENANCE = "MAINTENANCE"
    OTHER = "OTHER"


class Payment(Base):
    __tablename__ = "Payment"

    id = Column(String, primary_key=True, default=_id)
    studentId = Column(String, ForeignKey("Student.id", ondelete="CASCADE"), nullable=False)
    student = relationship("Student", back_populates="payments")
    amount = Column(Float, nullable=False)
    type = Column(SAEnum(PaymentTypeEnum), nullable=False, default=PaymentTypeEnum.HOSTEL_FEE)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(SAEnum(PaymentStatusEnum), nullable=False, default=PaymentStatusEnum.PENDING)
    method = Column(String, nullable=True)
    proofImageUrl = Column(String, nullable=True)
    rejectionReason = Column(String, nullable=True)
    reviewedAt = Column(DateTime, nullable=True)
    reviewedBy = Column(String, nullable=True)
    paidAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ComplaintStatusEnum(str, PyEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class ComplaintPriorityEnum(str, PyEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ComplaintCategoryEnum(str, PyEnum):
    MAINTENANCE = "MAINTENANCE"
    SECURITY = "SECURITY"
    CLEANLINESS = "CLEANLINESS"
    NOISE = "NOISE"
    OTHER = "OTHER"


class Complaint(Base):
    __tablename__ = "Complaint"

    id = Column(String, primary_key=True, default=_id)
    studentId = Column(String, ForeignKey("Student.id", ondelete="CASCADE"), nullable=False)
    student = relationship("Student", back_populates="complaints")
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(SAEnum(ComplaintCategoryEnum), nullable=False, default=ComplaintCategoryEnum.OTHER)
    priority = Column(SAEnum(ComplaintPriorityEnum), nullable=False, default=ComplaintPriorityEnum.MEDIUM)
    status = Column(SAEnum(ComplaintStatusEnum), nullable=False, default=ComplaintStatusEnum.PENDING)
    adminResponse = Column(String, nullable=True)
    resolvedAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class VisitorStatusEnum(str, PyEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Visitor(Base):
    __tablename__ = "Visitor"

    id = Column(String, primary_key=True, default=_id)
    student = relationship("Student", back_populates="visitors")
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    purpose = Column(String, nullable=False)
    studentId = Column(String, ForeignKey("Student.id", ondelete="CASCADE"), nullable=False)
    roomNumber = Column(String, nullable=False)
    status = Column(SAEnum(VisitorStatusEnum), nullable=False, default=VisitorStatusEnum.PENDING)
    requestedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    approvedAt = Column(DateTime, nullable=True)
    approvedBy = Column(String, nullable=True)
    rejectionReason = Column(String, nullable=True)
    entryTime = Column(DateTime, nullable=True)
    exitTime = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NotificationTypeEnum(str, PyEnum):
    ROOM_APPROVED = "ROOM_APPROVED"
    ROOM_REJECTED = "ROOM_REJECTED"
    PAYMENT_DUE = "PAYMENT_DUE"
    COMPLAINT_UPDATE = "COMPLAINT_UPDATE"
    MESSAGE = "MESSAGE"
    SYSTEM = "SYSTEM"


class Notification(Base):
    __tablename__ = "Notification"

    id = Column(String, primary_key=True, default=_id)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User")
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(SAEnum(NotificationTypeEnum), nullable=False, default=NotificationTypeEnum.SYSTEM)
    read = Column(Boolean, default=False, nullable=False)
    data = Column(JSON, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

