"""
FastAPI routes for todo application.
Implements all CRUD endpoints with authentication and SSE support.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.models.task import (
    CreateTaskRequest,
    UpdateTaskRequest,
    DeleteTasksRequest,
    TaskResponse,
    TaskListResponse,
    DeleteResponse,
    ErrorResponse
)
from app.services.task_service import TaskService
from app.services.sse_service import sse_manager
from app.database.redis_client import get_redis
from app.auth.jwt_handler import get_current_user
from upstash_redis import Redis
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tasks"])


@router.post(
    "/addnewusertodo",
    response_model=TaskResponse,
    responses={
        401: {"model": ErrorResponse},
        400: {"model": ErrorResponse}
    },
    summary="Create new task",
    description="Create a new root-level task or subtask under an existing task"
)
async def create_task(
    task_data: CreateTaskRequest,
    user_id: str = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):
    """
    **Create a new task**
    
    - **title**: Task title (required, 1-500 characters)
    - **description**: Task description (optional, max 5000 characters)
    - **parent_id**: Parent task ID for subtasks, "0" for root tasks
    
    Returns the created task with generated ID.
    Broadcasts creation event to all user's active SSE connections.
    """
    try:
        service = TaskService(redis)
        task = await service.create_task(user_id, task_data)
        
        # Broadcast real-time update
        await sse_manager.broadcast_task_created(
            user_id,
            task.model_dump()
        )
        
        return TaskResponse(task=task)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/getusertodos",
    response_model=TaskListResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Get all user tasks",
    description="Retrieve all tasks for authenticated user in hierarchical structure"
)
async def get_tasks(
    user_id: str = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):
    """
    **Retrieve all tasks for the authenticated user**
    
    Returns tasks in hierarchical structure:
    - Root-level tasks contain nested subtasks
    - Sorted by creation date (newest first)
    - Excludes soft-deleted tasks
    
    Optimized for performance using Redis pipelines to avoid N+1 queries.
    """
    try:
        service = TaskService(redis)
        tasks = await service.get_user_tasks(user_id)
        
        return TaskListResponse(
            tasks=tasks,
            count=len(tasks)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put(
    "/edittodo",
    response_model=TaskResponse,
    responses={
        401: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    },
    summary="Update task",
    description="Update task details or toggle completion status"
)
async def update_task(
    update_data: UpdateTaskRequest,
    user_id: str = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):
    """
    **Update an existing task**
    
    - **task_id**: ID of task to update (required)
    - **title**: New title (optional)
    - **description**: New description (optional)
    - **completed**: Toggle completion status (optional boolean)
    
    At least one update field must be provided.
    Broadcasts update event to all user's active SSE connections.
    """
    try:
        service = TaskService(redis)
        task = await service.update_task(user_id, update_data)
        
        # Broadcast real-time update
        await sse_manager.broadcast_task_updated(
            user_id,
            task.model_dump()
        )
        
        return TaskResponse(task=task)
        
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/deletetodos",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse},
        400: {"model": ErrorResponse}
    },
    summary="Delete tasks",
    description="Soft delete one or more tasks with cascade to subtasks"
)
async def delete_tasks(
    delete_data: DeleteTasksRequest,
    user_id: str = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):
    """
    **Soft delete tasks**
    
    - **task_ids**: List of task IDs to delete
    
    Performs soft delete (sets deleted_at timestamp) with cascade:
    - All subtasks of deleted tasks are also soft-deleted
    - Tasks remain in database but excluded from queries
    - Returns total count of deleted tasks including subtasks
    
    Broadcasts deletion event to all user's active SSE connections.
    """
    try:
        service = TaskService(redis)
        deleted_count = await service.delete_tasks(user_id, delete_data.task_ids)
        
        # Broadcast real-time update
        await sse_manager.broadcast_task_deleted(
            user_id,
            delete_data.task_ids,
            deleted_count
        )
        
        return DeleteResponse(
            deleted_count=deleted_count,
            message=f"Successfully deleted {deleted_count} task(s)"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/stream",
    summary="SSE stream for real-time updates",
    description="Server-Sent Events endpoint for receiving live task updates"
)
async def sse_stream(
    user_id: str = Depends(get_current_user)
):
    """
    **Real-time updates via Server-Sent Events**
    
    Establishes a persistent connection for receiving live updates:
    - Task creation events
    - Task update events
    - Task deletion events
    - Heartbeat messages every 30 seconds
    
    Connection is user-specific; only receives updates for authenticated user's tasks.
    
    **Client Implementation:**
    ```javascript
    const eventSource = new EventSource('/stream', {
        headers: { 'Authorization': 'Bearer YOUR_JWT_TOKEN' }
    });
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received update:', data);
    };
    ```
    """
    return StreamingResponse(
        sse_manager.subscribe(user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
