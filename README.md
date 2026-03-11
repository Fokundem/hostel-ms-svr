# HostelMS Backend

FastAPI backend server for the HostelMS management system with JWT authentication, PostgreSQL database, and Prisma ORM.

## Features

- ✅ JWT Authentication (Login/Register)
- ✅ Role-based Access Control (ADMIN, HOSTEL_MANAGER, STUDENT, EMPLOYEE)
- ✅ PostgreSQL Database with Prisma ORM
- ✅ Swagger/OpenAPI Documentation
- ✅ Security: Password hashing, JWT tokens, CORS
- ✅ WebSocket support (ready for chat)
- ✅ RESTful API design

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: Prisma
- **Authentication**: JWT + Passlib
- **Server**: Uvicorn
- **Real-time**: WebSockets

## Prerequisites

- Python 3.10+
- PostgreSQL 12+
- pip or conda
- Docker (optional, for PostgreSQL)

## Setup Instructions

### 1. Clone and Navigate

```bash
cd hostel_ms_sev
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Database

#### Option A: Using Docker (Recommended)

```bash
docker-compose up -d
```

This will start PostgreSQL on `localhost:5432` with:
- User: `hostel_user`
- Password: `hostel_password`
- Database: `hostel_ms_db`
- PgAdmin: http://localhost:5050

#### Option B: Manual PostgreSQL Setup

Create a PostgreSQL database and update `.env` with your connection string:

```
DATABASE_URL=postgresql://username:password@localhost:5432/hostel_ms_db
```

### 5. Initialize Prisma

```bash
# Install Prisma CLI globally (one time)
npm install -g @prisma/cli

# Or use npx directly
npx prisma migrate dev --name init
```

This will:
- Create tables in PostgreSQL
- Generate Prisma client

### 6. Update Environment Variables

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

Update the `SECRET_KEY` with a strong secret:

```
SECRET_KEY=your-strong-secret-key-here
```

### 7. Run the Server

```bash
# Development (with auto-reload)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main script
python app/main.py
```

The server will start at: **http://localhost:8000**

## API Documentation

Once the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication

```
POST   /api/v1/auth/register       # Register new user
POST   /api/v1/auth/login          # Login (returns JWT token)
POST   /api/v1/auth/logout         # Logout
GET    /api/v1/auth/me             # Get current user
PUT    /api/v1/auth/me             # Update user profile
```

### Usage Example

#### Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "password123",
    "name": "John Doe",
    "role": "STUDENT",
    "matricule": "MAT001",
    "department": "Computer Science",
    "level": "200"
  }'
```

#### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "password123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_id",
    "email": "student@example.com",
    "name": "John Doe",
    "role": "STUDENT",
    "status": "ACTIVE"
  }
}
```

#### Get Current User

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Project Structure

```
app/
├── main.py              # Entry point
├── settings.py          # Configuration
├── database.py          # Database connection
├── api/
│   └── v1/
│       ├── auth.py      # Authentication routes
│       ├── rooms.py     # Room management (coming soon)
│       ├── allocations.py # Room allocation flow (coming soon)
│       └── ...
├── services/
│   ├── auth.py         # Auth business logic
│   ├── room.py         # Room service (coming soon)
│   └── ...
├── schemas/
│   └── auth.py         # Request/response models
├── utils/
│   ├── security.py     # JWT & password hashing
│   ├── dependencies.py # FastAPI dependencies
│   └── exceptions.py   # Custom exceptions
└── websockets/         # WebSocket handlers (coming soon)

prisma/
└── schema.prisma       # Database schema

docker-compose.yml      # PostgreSQL + PgAdmin
requirements.txt        # Python dependencies
.env                    # Environment variables
```

## Development

### Run Tests (when available)

```bash
pytest
```

### Format Code

```bash
black app/
```

### Lint Code

```bash
flake8 app/
```

## Next Steps (Planned)

1. ✅ Authentication System (JWT)
2. 🔄 Room Management & Allocation Flow
3. 🔄 Payments System
4. 🔄 Complaints System
5. 🔄 Chat System (Group + Private)
6. 🔄 Notifications System
7. 🔄 Visitor Management
8. 🔄 Admin Dashboard

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection string |
| `SECRET_KEY` | - | JWT secret key |
| `ALGORITHM` | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | JWT token expiration |
| `DEBUG` | True | Debug mode |
| `ALLOWED_ORIGINS` | localhost:5173,3000 | CORS allowed origins |

## Troubleshooting

### Database Connection Error

1. Check PostgreSQL is running
2. Verify DATABASE_URL in `.env`
3. Run `docker-compose ps` to see container status

### Migration Error

```bash
# Reset Prisma
npx prisma generate

# Re-run migrations
npx prisma migrate dev
```

### Port Already in Use

Change the port in the run command:

```bash
python -m uvicorn app.main:app --reload --port 8001
```

## Contributing

1. Create feature branches
2. Follow PEP 8 style guide
3. Add tests for new features
4. Submit pull requests

## License

MIT
