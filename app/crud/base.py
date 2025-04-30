"""base crud class with common operations."""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    base crud class with default methods to create, read, update, delete (crud).
    
    attributes:
        model: a sqlalchemy model class
    """

    def __init__(self, model: Type[ModelType]):
        """initialize crud base with model type."""
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """get a record by id.
        
        args:
            db: database session
            id: id of the record to get
            
        returns:
            optional model instance if found
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        get multiple records with pagination.
        
        args:
            db: database session
            skip: number of records to skip
            limit: maximum number of records to return
            
        returns:
            list of model instances
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        create new record.
        
        args:
            db: database session
            obj_in: pydantic schema with create data
            
        returns:
            created model instance
        """
        # Convert to dict with snake_case field names
        obj_in_data = obj_in.model_dump(
            by_alias=False,  # use Python field names (snake_case)
            exclude_unset=True  # only include set values
        )
        
        # Create model instance with validated data
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        
        try:
            db.commit()
            db.refresh(db_obj)
        except Exception as e:
            db.rollback()
            raise e
        
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        update existing record.
        
        args:
            db: database session
            db_obj: existing database object
            obj_in: update data (schema or dict)
            
        returns:
            updated model instance
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(
                by_alias=False,
                exclude_unset=True
            )
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        try:
            db.commit()
            db.refresh(db_obj)
        except Exception as e:
            db.rollback()
            raise e
        
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        """
        remove a record.
        
        args:
            db: database session
            id: id of record to remove
            
        returns:
            removed model instance
        """
        obj = db.query(self.model).get(id)
        if obj is None:
            return None
            
        try:
            db.delete(obj)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        
        return obj 