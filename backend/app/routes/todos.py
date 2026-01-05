from fastapi import APIRouter, Depends, HTTPException, status, Query
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
from app.auth.jwt_handler import get_current_user, get_current_user_sse
from upstash_redis.asyncio import Redis
import logging
from jose import jwt  
from app.config import get_settings

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
    try:
        service = TaskService(redis)
        task = await service.create_task(user_id, task_data)
        
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
    try:
        service = TaskService(redis)
        task = await service.update_task(user_id, update_data)
        
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
    user_id: str = Depends(get_current_user_sse) 
):
    return StreamingResponse(
        sse_manager.subscribe(user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" 
        }
    )
