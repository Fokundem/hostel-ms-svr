from prisma import Prisma
from datetime import datetime, timedelta

class DashboardService:
    def __init__(self, db: Prisma):
        self.db = db

    async def get_stats(self):
        """Aggregate statistics for the admin dashboard"""
        
        # 1. Total Students
        total_students = await self.db.student.count()
        
        # 2. Room Occupancy
        total_rooms = await self.db.room.count()
        occupied_rooms = await self.db.room.count(where={"status": "FULL"})
        # Partically occupied rooms count towards occupancy but status might be AVAILABLE if not full
        # Let's calculate based on capacity vs occupied
        # Actually prisma-client-py aggregate might be better but let's do simple counts for now
        
        rooms = await self.db.room.find_many()
        total_capacity = sum(r.capacity for r in rooms)
        total_occupied = sum(r.occupied for r in rooms)
        occupancy_rate = (total_occupied / total_capacity * 100) if total_capacity > 0 else 0
        
        # 3. Monthly Revenue
        now = datetime.now()
        this_month = now.month
        this_year = now.year
        
        payments = await self.db.payment.find_many(
            where={
                "status": "PAID",
                "month": this_month,
                "year": this_year
            }
        )
        monthly_revenue = sum(p.amount for p in payments)
        
        # 4. Recent Activity
        recent_students = await self.db.student.find_many(
            take=5,
            order={"createdAt": "desc"},
            include={"user": True}
        )
        
        recent_payments = await self.db.payment.find_many(
            take=5,
            order={"createdAt": "desc"},
            include={"student": {"include": {"user": True}}}
        )
        
        pending_complaints = await self.db.complaint.find_many(
            where={"status": "PENDING"},
            take=5,
            order={"createdAt": "desc"},
            include={"student": {"include": {"user": True}}}
        )
        
        # 5. Monthly Revenue Data (for chart - last 6 months)
        revenue_data = []
        for i in range(5, -1, -1):
            date = now - timedelta(days=i*30)
            m = date.month
            y = date.year
            month_name = date.strftime("%b")
            
            m_payments = await self.db.payment.find_many(
                where={
                    "status": "PAID",
                    "month": m,
                    "year": y
                }
            )
            total = sum(p.amount for p in m_payments)
            revenue_data.append({"month": month_name, "revenue": total})

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
                    "status": s.user.status.lower()
                } for s in recent_students
            ],
            "recentPayments": [
                {
                    "id": p.id,
                    "studentName": p.student.user.name,
                    "amount": p.amount,
                    "month": datetime(2000, p.month, 1).strftime("%B"),
                    "year": p.year,
                    "status": p.status.lower()
                } for p in recent_payments
            ],
            "pendingComplaints": [
                {
                    "id": c.id,
                    "title": c.title,
                    "studentName": c.student.user.name,
                    "priority": c.priority.lower()
                } for c in pending_complaints
            ],
            "revenueData": revenue_data,
            "roomOccupancyData": [
                {"name": "Occupied", "value": total_occupied, "color": "#1a56db"},
                {"name": "Available", "value": total_capacity - total_occupied, "color": "#e5e7eb"}
            ]
        }
