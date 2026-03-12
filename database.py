from prisma import Prisma
from typing import Optional

prisma: Optional[Prisma] = None


async def connect_db():
    """Connect to the database on startup"""
    global prisma
    prisma = Prisma()
    await prisma.connect()
    print("✓ Database connected successfully")


async def disconnect_db():
    """Disconnect from the database on shutdown"""
    global prisma
    if prisma:
        await prisma.disconnect()
        print("✓ Database disconnected")


def get_db() -> Prisma:
    """Get the database connection"""
    if prisma is None:
        raise RuntimeError("Database not initialized")
    return prisma
