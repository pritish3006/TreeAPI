# Tree Management API Server

A FastAPI API Server for managing hierarchical tree structures.

## Requirements
- Python 3.12+
- SQLite
- UV (for dependency management)

## Project Structure
```
TreeAPI/
├── app/                    # Main application package
│   ├── api/               # API endpoints
│   ├── core/              # Core configurations
│   ├── crud/              # Database CRUD operations
│   ├── db/                # Database setup and sessions
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic models
│   └── main.py           # FastAPI application creation
├── alembic/               # Database migrations
├── tests/                 # Test suite
│   ├── test_api/         # API integration tests
│   └── test_crud/        # CRUD unit tests
├── .env                   # Environment variables (create from template)
├── alembic.ini           # Alembic configuration
├── requirements.txt       # Project dependencies
└── README.md             # This file
```

## Setup
1. Install UV:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

3. Create .env file from template and configure as needed

4. Run migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

## Testing
Run tests with:
```bash
pytest
```

## API Documentation
Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 