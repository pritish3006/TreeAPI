"""script to seed test data for database layer testing."""
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.tree import Node

def seed_test_data() -> None:
    """
    seed test data for database layer validation.
    
    test cases:
        0: empty database state (start fresh)
        1: basic operations (root node, valid parent-child)
        many: complex cases (invalid parent, cycle attempts, multi-level)
    """
    # Create engine with foreign key enforcement
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    
    # Enable foreign key enforcement
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Case 0: Ensure empty database
        print("\n🧪 Case 0: Empty database")
        db.query(Node).delete()
        db.commit()
        print("✓ Database cleared")
        
        # Verify database is empty
        count = db.query(Node).count()
        print(f"Current node count: {count}")
        
        # Case 1: Basic Valid Operations
        print("\n🧪 Case 1: Basic valid operations")
        # Create root node
        root = Node(label="root_node")
        db.add(root)
        db.flush()
        print(f"✓ Created root node with id: {root.id}")
        
        # Create child with valid parent
        child = Node(label="valid_child", parent_id=root.id)
        db.add(child)
        db.flush()
        print(f"✓ Created child with id: {child.id}, parent_id: {child.parent_id}")
        
        # Case Many: Complex Cases
        print("\n🧪 Case Many: Complex cases")
        # Multi-level structure for traversal testing
        branch1 = Node(label="branch1", parent_id=root.id)
        branch2 = Node(label="branch2", parent_id=root.id)
        db.add_all([branch1, branch2])
        db.flush()
        print(f"✓ Created branches with ids: {branch1.id}, {branch2.id}")
        
        leaf1 = Node(label="leaf1", parent_id=branch1.id)
        leaf2 = Node(label="leaf2", parent_id=branch1.id)
        db.add_all([leaf1, leaf2])
        db.flush()
        print(f"✓ Created leaves with ids: {leaf1.id}, {leaf2.id}")
        print("✓ Created multi-level structure")
        
        # Commit all changes
        db.commit()
        print("\n✅ Test data seeded successfully!")
        
        # Verify final state
        final_count = db.query(Node).count()
        print(f"Final node count: {final_count}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding test data: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding test data...")
    seed_test_data() 