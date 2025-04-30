"""pytest configuration and fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.tree import Node

# Use in-memory SQLite for tests
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def engine():
    """create a new database engine for each test."""
    engine = create_engine(
        TEST_SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(engine):
    """create a new database session for each test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def empty_db(db: Session):
    """provide an empty database."""
    yield db

@pytest.fixture(scope="function")
def sample_tree(db: Session):
    """create a sample tree structure for testing.
    
    creates:
        root1                    root2
        ├── child1              └── child3
        │   ├── grandchild1
        │   └── grandchild2
        └── child2
    """
    # Create roots
    root1 = Node(label="root1")
    root2 = Node(label="root2")
    db.add_all([root1, root2])
    db.commit()
    
    # Create children for root1
    child1 = Node(label="child1", parent=root1)
    child2 = Node(label="child2", parent=root1)
    db.add_all([child1, child2])
    
    # Create child for root2
    child3 = Node(label="child3", parent=root2)
    db.add(child3)
    
    # Create grandchildren for child1
    grandchild1 = Node(label="grandchild1", parent=child1)
    grandchild2 = Node(label="grandchild2", parent=child1)
    db.add_all([grandchild1, grandchild2])
    
    db.commit()
    db.refresh(root1)
    db.refresh(root2)
    
    return [root1, root2, child1, child2, child3, grandchild1, grandchild2]

@pytest.fixture(scope="function")
def override_db(db: Session):
    """override the database dependency in FastAPI app."""
    from app.main import app
    from app.db.session import get_db
    
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield db
    app.dependency_overrides = {} 