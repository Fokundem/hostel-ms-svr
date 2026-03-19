import asyncio
from database import get_db, connect_db
from db import get_db_session
from services.allocation import AllocationService

async def main():
    await connect_db()
    for session in get_db_session():
        service = AllocationService(session)
        allocs = service.get_all_allocations()
        if allocs:
            print("FIRST ALLOC:")
            import json
            print(json.dumps(allocs[0], default=str, indent=2))
        else:
            print("NO ALLOCS")
        break

asyncio.run(main())
