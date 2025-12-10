from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime, date

from app.models.task import PriorityEnum, StatusEnum


class TaskCreateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None)  
    priority: str = PriorityEnum.LOW.value
    start_date: Optional[str] = None
    due_date: str = Field(..., description="Due date is required (YYYY-MM-DD)")
    images: Optional[List[str]] = []

    @validator('priority')
    def validate_priority(cls, value):
        if value not in [p.value for p in PriorityEnum]:
            raise ValueError(f'Priority must be one of: {[p.value for p in PriorityEnum]}')
        return value

    @validator('due_date')
    def validate_due_date(cls, value):
        """Validate due date format and ensure it's not in the past"""
        if not value:
            raise ValueError('Due date is required. Please select a date.')
        
        # Parse "YYYY-MM-DD" string
        try:
            parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError('Due date must be in YYYY-MM-DD format.')
        
        # Compare dates directly (no timezone issues)
        today = date.today()
        
        # Allow today's date OR future dates
        if parsed_date < today:
            raise ValueError('Due date cannot be in the past. Please select today or a future date.')
        
        # Return the date string as-is for the database
        return value


class TaskUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=1000)  # Added min_length
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    images: Optional[List[str]] = []

    @validator('status')
    def validate_status(cls, v):
        if v and v not in [s.value for s in StatusEnum]:
            raise ValueError(f'Status must be one of: {[s.value for s in StatusEnum]}')
        return v

    @validator('priority')
    def validate_priority(cls, v):
        if v and v not in [p.value for p in PriorityEnum]:
            raise ValueError(f'Priority must be one of: {[p.value for p in PriorityEnum]}')
        return v

    @validator('due_date')
    def validate_due_date(cls, value):
        """Validate due date format and ensure it's not in the past"""
        if not value:
            return None
        
        try:
            parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError('Due date must be in YYYY-MM-DD format.')
        
        # Compare dates directly
        today = date.today()
        
        # Allow today's date OR future dates
        if parsed_date < today:
            raise ValueError('Due date cannot be in the past. Please select today or a future date.')
        
        return value


class TaskReadSchema(BaseModel):
    task_id: int
    title: str
    description: Optional[str]
    start_date: datetime
    due_date: datetime
    status: str = StatusEnum.PENDING.value
    priority: str = PriorityEnum.LOW.value
    user_id: int
    images: List[str] = []