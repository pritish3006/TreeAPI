1. Introduction

This document defines the functional and non‑functional requirements, user stories, and technical specifications for the Tree Management API. The API provides endpoints to create and retrieve hierarchical tree data structures with persistent storage and comprehensive testing.

2. Product Overview

Goal: Expose a simple, production‑grade HTTP API to manage node‑based trees.Audience: Backend developers integrating tree data into applications (e.g., org charts, file trees, taxonomies).

Key Features:

- GET /api/tree: retrieve full forest
- POST /api/tree: create nodes under a specified parent
- Persistent storage across restarts
- Automated testing (pytest + TestClient)
- Swagger/OpenAPI docs

3. User Stories

- As a developer, I want to fetch all trees so that I can display them in my UI.
- As a developer, I want to add a node under an existing parent so that I can expand the tree dynamically.
- As a developer, I want error feedback when I reference a non‑existent parent so I catch mistakes early.
- As a system administrator, I want the data to persist across server restarts so nothing is lost.
- As a CI engineer, I want automated tests covering endpoints and error cases so builds fail on regressions.

4. Functional Requirements

4.1 Endpoints & Logic

GET /api/tree
Description: Return the entire forest as nested JSON.
Response: 200 OK, body: array of root nodes { id, label, children: [...] }.
Errors: N/A (always returns empty array at worst).

POST /api/tree
Description: Create a new node and attach to parentId (nullable for root).
Request Body (JSON):

```
{"label": "string", "parentId": integer | null}
```
Validation:
- label required, max 255 chars, non‑empty.
- parentId if not null must reference existing node.
- Prevent cycles (parent cannot be descendant of new node).

Responses:
- 201 Created, body: node created { id, label, parentId }.
- 400 Bad Request on validation failure.
- 404 Not Found if parentId not found.

4.2 Error Handling
Standard JSON error format:
- {"detail": "Error message here."}
- Use HTTP status codes.
- Server errors return 500 Internal Server Error with generic message.

4.3 Application Logic

Cycle Prevention: Walk parent chain to root to detect loops.
- Timestamp Management: Auto‑update updated_at on changes.
- Database Transactions: Wrap create operations in transactions to ensure atomicity.

5. Database Layer

Schema: Adjacency List (nodes table with parent_id).
Indexes: index on parent_id for fast child lookups.
Migrations: Alembic scripts to create table and index.
Constraints: Foreign key with ON DELETE CASCADE.
ORM: SQLAlchemy models with relationship for children.

6. Pydantic Schemas

```
from pydantic import BaseModel, Field
from typing import Optional, List

class NodeBase(BaseModel):
    label: str = Field(..., max_length=255)
    parentId: Optional[int] = Field(None, alias="parentId")

class NodeCreate(NodeBase):
    pass

class NodeResponse(BaseModel):
    id: int
    label: str
    parentId: Optional[int]
    children: List['NodeResponse'] = []
    class Config:
        orm_mode = True
```

7. Data Flow & Requirements

Request ➔ API layer (FastAPI) ➔ validate via Pydantic schema.
Business Logic ➔ CRUD module (SQLAlchemy + sessions).
Cycle Check (on POST) ➔ DB lookup loop.
Persistence ➔ commit to SQLite.
Response ➔ Build JSON tree for GET, return created node for POST.

8. Middleware Requirements

DB Session Middleware: create/teardown SQLAlchemy session per request.

Error Handling Middleware: catch unhandled exceptions, translate to JSON errors.

Logging Middleware: structured request/response logging (method, path, status, duration).

9. Testing Requirements & Procedures

9.1 Unit Tests (pytest)

crud.get_all_nodes returns correct list.

crud.create_node inserts valid node.

cycle detection rejects loops.

9.2 Integration Tests (TestClient)

GET /api/tree on empty DB returns [].

POST to create a root, then GET includes it.

POST with invalid parentId returns 404.

POST that would cause cycle returns 400.

DELETE parent cascades children (optional future test).

9.3 CI Pipeline

Lint (flake8, mypy)

Run pytest suite

Fail build on any error

10. Deployment Specifications

Containerization: Dockerfile for FastAPI app.

Compose: docker-compose.yml with app + postgres.

Environment Variables:

DATABASE_URL, PORT=8000, LOG_LEVEL.

Cloud Deploy: support AWS ECS/Fargate or GCP Cloud Run.

Health Check: GET /healthz returns 200 OK.

CI/CD: on push to main, build Docker image, run tests, deploy.

End of Document.

