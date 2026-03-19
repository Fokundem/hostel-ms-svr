from prisma import Prisma
from typing import List


class HostelService:
    def __init__(self, db: Prisma):
        self.db = db

    async def list_hostels(self) -> List[dict]:
        hostels = await self.db.hostel.find_many(order={"createdAt": "asc"})
        return hostels

    async def create_hostel(self, data: dict) -> dict:
        hostel = await self.db.hostel.create(
            data={
                "name": data["name"],
                "code": data["code"],
                "totalRooms": data["totalRooms"],
            }
        )
        return hostel

