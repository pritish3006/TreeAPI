# First-Time User Setup Guide

This guide walks through every step required to set up and run the Tree Management API as a first-time user.

## Prerequisites Verification

Before starting, ensure you have:

1. **Python 3.12 or higher**
   ```bash
   python --version
   # Should show Python 3.12.x or higher
   ```

2. **SQLite3**
   ```bash
   sqlite3 --version
   # Should show the SQLite version
   ```

3. **Optional: UV package manager**
   ```bash
   uv --version
   # If not installed, you can use pip instead
   ```

## Step 1: Clone the Repository

```bash
git clone [repository-url]
cd TreeAPI
```

## Step 2: Set Up Python Environment (CRITICAL)

A virtual environment with Python 3.12+ is **absolutely required** - the application will not work properly without it.

### Option A: Using UV (recommended)

```bash
# Install UV if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# IMPORTANT: You MUST see (.venv) at the beginning of your prompt
# Example: (.venv) user@machine:~/TreeAPI$

# Install dependencies
uv pip install -r requirements.txt
```

### Option B: Using standard pip

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# IMPORTANT: You MUST see (venv) at the beginning of your prompt
# Example: (venv) user@machine:~/TreeAPI$

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file if needed
# Default values work for local development
```

## Step 4: Database Setup

**CRITICAL**: Your virtual environment MUST be activated.

```bash
# Run database migrations to create the database schema
alembic upgrade head

# Verify the database was created
ls -la tree_api.db*
# You should see tree_api.db and associated WAL files
```

## Step 5: Start the Development Server

**CRITICAL**: Your virtual environment MUST be activated.

```bash
# Start the server with auto-reload for development
uvicorn app.main:app --reload
```

You should see output similar to:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [28967]
INFO:     Started server process [28969]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 6: Verify Server is Running

### Check Health Endpoint

```bash
curl http://localhost:8000/healthz
```

Expected response:
```json
{"status":"healthy"}
```

### Create Your First Node

```bash
curl -X POST \
  http://localhost:8000/api/tree \
  -H "Content-Type: application/json" \
  -d '{"label": "My First Root Node"}'
```

Expected response (ID may vary):
```json
{"id":1,"label":"My First Root Node"}
```

### Create a Child Node

```bash
# Replace 1 with the actual ID from the previous response
curl -X POST \
  http://localhost:8000/api/tree \
  -H "Content-Type: application/json" \
  -d '{"label": "My First Child Node", "parentId": 1}'
```

Expected response (ID may vary):
```json
{"id":2,"label":"My First Child Node"}
```

### Retrieve the Tree

```bash
curl http://localhost:8000/api/tree
```

Expected response (formatted for readability):
```json
[
  {
    "id": 1,
    "label": "My First Root Node",
    "parentId": null,
    "children": [
      {
        "id": 2,
        "label": "My First Child Node",
        "parentId": 1,
        "children": []
      }
    ]
  }
]
```

## Step 7: Access API Documentation

Open your browser and navigate to:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Step 8: Run Tests (Optional)

**CRITICAL**: Your virtual environment MUST be activated.

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app tests/
```

## Step 9: Production Deployment

**CRITICAL**: Your virtual environment MUST be activated before starting the production server.

```bash
# REQUIRED: Activate your virtual environment
source .venv/bin/activate  # or source venv/bin/activate

# Start the server in production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Common Issues and Solutions

### Virtual Environment Not Activated

If you see import errors or missing dependencies:
```bash
# Check if you see (.venv) or (venv) in your prompt
# If not, activate it:
source .venv/bin/activate  # or source venv/bin/activate
```

### Database Errors

If you see database connection errors:
- Ensure SQLite is installed
- Check that the database file path in .env is correct
- Verify file permissions on the database directory

### Port Already in Use

If port 8000 is already in use:
```bash
# Use a different port
uvicorn app.main:app --reload --port 8001
```

### Module Not Found Errors

If you see "module not found" errors:
- Ensure your virtual environment is activated
- Verify all dependencies are installed
- Check that you're running the command from the project root 