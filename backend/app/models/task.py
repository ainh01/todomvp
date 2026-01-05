from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="Task title")
    description: str = Field(default="", max_length=5000, description="Task description")


class CreateTaskRequest(TaskBase):
    parent_id: str = Field(default="0", description="Parent task ID, '0' for root tasks")
    
    @validator('parent_id')
    def validate_parent_id(cls, v):
        if v != "0" and not v.isdigit():
            raise ValueError("parent_id must be '0' or a numeric string")
        return v


class UpdateTaskRequest(BaseModel):
    task_id: str = Field(..., description="ID of task to update")
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    completed: Optional[bool] = Field(None, description="Toggle completion status")
    
    @validator('task_id')
    def validate_task_id(cls, v):
        if not v.isdigit():
            raise ValueError("task_id must be a numeric string")
        return v


class DeleteTasksRequest(BaseModel):
    task_ids: List[str] = Field(..., min_items=1, description="List of task IDs to delete")
    
    @validator('task_ids')
    def validate_task_ids(cls, v):
        """Ensure all task IDs are numeric."""
        for task_id in v:
            if not task_id.isdigit():
                raise ValueError(f"Invalid task_id: {task_id}")
        return v


class Task(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    parent_id: str
    created_at: str  # ISO 8601 timestamp
    completed_at: str  # Empty string if not completed
    deleted_at: str  # Empty string if not deleted
    updated_at: str  # ISO 8601 timestamp
    subtasks: List['Task'] = Field(default_factory=list, description="Nested subtasks")
    
    @property
    def is_completed(self) -> bool:
        return bool(self.completed_at)
    
    @property
    def is_deleted(self) -> bool:
        return bool(self.deleted_at)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123",
                "user_id": "user_456",
                "title": "Complete project documentation",
                "description": "Write comprehensive README and API docs",
                "parent_id": "0",
                "created_at": "2024-01-15T10:30:00Z",
                "completed_at": "",
                "deleted_at": "",
                "updated_at": "2024-01-15T10:30:00Z",
                "subtasks": []
            }
        }


Task.model_rebuild()


class TaskResponse(BaseModel):
    success: bool = True
    task: Task


class TaskListResponse(BaseModel):
    success: bool = True
    tasks: List[Task]
    count: int


class DeleteResponse(BaseModel):
    success: bool = True
    deleted_count: int
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
