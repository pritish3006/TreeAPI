# Tree Management API Server

![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688.svg)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.27-red.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg)
![Alembic](https://img.shields.io/badge/Alembic-1.13.1-lightgrey.svg)
![Tests](https://img.shields.io/badge/Tests-Pytest-green.svg)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

A production-ready FastAPI server for managing hierarchical tree data structures. This API provides a robust solution for creating and querying tree-based data with persistent storage.

## Features

- **Tree Management API**: Create and retrieve hierarchical tree structures
- **Persistent Storage**: SQLite database with SQLAlchemy ORM
- **Production-Ready**: Comprehensive error handling, validation, and performance optimizations
- **Fully Tested**: Extensive test suite with pytest
- **API Documentation**: Interactive Swagger UI and ReDoc 
- **Database Migrations**: Managed through Alembic

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

## Installation

### Prerequisites
- Python 3.12 or higher (REQUIRED)
- SQLite3
- uv or pip

### Quick Setup

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd TreeAPI
   ```

2. Install uv (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   uv pip install -r requirements.txt  # With UV
   # OR
   pip install -r requirements.txt     # With standard pip
   ```

5. Create an environment file:
   ```bash
   cp .env.example .env
   # Edit the .env file with your preferred settings
   ```

6. Run database migrations:
   ```bash
   alembic upgrade head
   ```

7. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Usage

The API exposes the following endpoints:

### GET /healthz

Health check endpoint to verify the API is running properly.

**Example Request:**
```bash
curl -X GET http://localhost:8000/healthz
```

**Example Response:**
```json
{
  "status": "healthy"
}
```

### GET /api/tree

Retrieves all trees in the database as a nested structure.

**Example Request:**
```bash
curl -X GET http://localhost:8000/api/tree
```

**Example Response:**
```json
[
  {
    "id": 1,
    "label": "Root Node",
    "parentId": null,
    "children": [
      {
        "id": 2,
        "label": "Child Node 1",
        "parentId": 1,
        "children": []
      },
      {
        "id": 3,
        "label": "Child Node 2",
        "parentId": 1,
        "children": []
      }
    ]
  }
]
```

### POST /api/tree

Creates a new node in the tree.

**Example Request (Creating a Root Node):**
```bash
curl -X POST http://localhost:8000/api/tree \
     -H "Content-Type: application/json" \
     -d '{"label": "New Root Node"}'
```

**Example Request (Creating a Child Node):**
```bash
curl -X POST http://localhost:8000/api/tree \
     -H "Content-Type: application/json" \
     -d '{"label": "New Child Node", "parentId": 1}'
```

**Example Response:**
```json
{
  "id": 4,
  "label": "New Child Node",
  "parentId": 1
}
```

## Testing

This project has a comprehensive test suite using pytest. The tests cover CRUD operations, API endpoints, edge cases, and performance considerations.

### Running Tests

To run the entire test suite:
```bash
pytest
```

To run tests with coverage report:
```bash
pytest --cov=app tests/
```

To run a specific test file:
```bash
pytest tests/test_api/test_endpoints.py
```

To run tests with verbose output:
```bash
pytest -v
```

### Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interaction between components
- **API Tests**: Test the API endpoints using FastAPI TestClient
- **Performance Tests**: Test the performance of the API under load
- **Edge Case Tests**: Test unusual inputs and boundary conditions

## Deployment

### Development Deployment

For local development and testing, the built-in Uvicorn server with reload is ideal:
```bash
uvicorn app.main:app --reload
```

### Production Deployment

For production deployment, use Uvicorn with multiple workers:
```bash
# IMPORTANT: Always activate your virtual environment first
source .venv/bin/activate  # or source venv/bin/activate

uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

This configuration offers:
- Multiple worker processes for better performance
- No auto-reload (more stable in production)
- Binding to all network interfaces
- Proper parallelism for multi-core systems

### Cloud Deployment Options

This API can be deployed to various cloud platforms:
- **AWS**: Deploy on EC2, Elastic Beanstalk, or Lambda (with API Gateway)
- **GCP**: Deploy on Compute Engine, App Engine, or Cloud Run
- **Azure**: Deploy on Azure App Service or Azure Container Instances

### Environment Variables

Configure the application using environment variables in the `.env` file. See `.env.example` for available options.

## Documentation

When the server is running, the API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

This project is licensed under the MIT License - see the LICENSE file for details. 