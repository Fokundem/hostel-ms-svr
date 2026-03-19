from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc
from datetime import datetime, timedelta

from models import Student, Room, Payment, Complaint, User, PaymentStatusEnum, ComplaintStatusEnum


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> dict:
        total_students = len(self.db.execute(select(Student)).scalars().all())
        rooms = self.db.execute(select(Room)).scalars().all()
        total_rooms = len(rooms)
        total_capacity = sum(r.capacity for r in rooms)
        total_occupied = sum(r.occupied or 0 for r in rooms)
        occupancy_rate = (total_occupied / total_capacity * 100) if total_capacity > 0 else 0

        now = datetime.now()
        this_month, this_year = now.month, now.year
        payments = self.db.execute(
            select(Payment).where(
                Payment.status == PaymentStatusEnum.PAID,
                Payment.month == this_month,
                Payment.year == this_year,
            )
        ).scalars().all()
        monthly_revenue = sum(p.amount for p in payments)

        recent_students = (
            self.db.execute(
                select(Student)
                .options(joinedload(Student.user))
                .order_by(desc(Student.createdAt))
                .limit(5)
            )
            .unique()
            .scalars()
            .all()
        )
        recent_payments = (
            self.db.execute(
                select(Payment)
                .options(joinedload(Payment.student).joinedload(Student.user))
                .order_by(desc(Payment.createdAt))
                .limit(5)
            )
            .unique()
            .scalars()
            .all()
        )
        pending_complaints = (
            self.db.execute(
                select(Complaint)
                .where(Complaint.status == ComplaintStatusEnum.PENDING)
                .options(joinedload(Complaint.student).joinedload(Student.user))
                .order_by(desc(Complaint.createdAt))
                .limit(5)
            )
            .unique()
            .scalars()
            .all()
        )

        revenue_data = []
        for i in range(5, -1, -1):
            date = now - timedelta(days=i * 30)
            m, y = date.month, date.year
            month_name = date.strftime("%b")
            m_payments = self.db.execute(
                select(Payment).where(
                    Payment.status == PaymentStatusEnum.PAID,
                    Payment.month == m,
                    Payment.year == y,
                )
            ).scalars().all()
            total = sum(p.amount for p in m_payments)
            revenue_data.append({"month": month_name, "revenue": total})

        def status_lower(obj):
            s = getattr(obj, "status", None) or getattr(obj, "user", None) and getattr(obj.user, "status", None)
            return (s.value if hasattr(s, "value") else str(s)).lower() if s else ""

        return {
            "totalStudents": total_students,
            "totalRooms": total_rooms,
            "occupiedRooms": total_occupied,
            "occupancyRate": round(occupancy_rate, 1),
            "monthlyRevenue": monthly_revenue,
            "recentStudents": [
                {
                    "id": s.id,
                    "name": s.user.name,
                    "matricule": s.matricule,
                    "status": status_lower(s),
                }
                for s in recent_students
            ],
            "recentPayments": [
                {
                    "id": p.id,
                    "studentName": p.student.user.name if p.student and p.student.user else "",
                    "amount": p.amount,
                    "month": datetime(2000, p.month, 1).strftime("%B"),
                    "year": p.year,
                    "status": (p.status.value if hasattr(p.status, "value") else str(p.status)).lower(),
                }
                for p in recent_payments
            ],
            "pendingComplaints": [
                {
                    "id": c.id,
                    "title": c.title,
                    "studentName": c.student.user.name if c.student and c.student.user else "",
                    "priority": (c.priority.value if hasattr(c.priority, "value") else str(c.priority)).lower(),
                }
                for c in pending_complaints
            ],
            "revenueData": revenue_data,
            "roomOccupancyData": [
                {"name": "Occupied", "value": total_occupied, "color": "#1a56db"},
                {"name": "Available", "value": total_capacity - total_occupied, "color": "#e5e7eb"},
            ],
        }
