"""
Business logic layer for task operations.
Handles all CRUD operations and coordinates Redis interactions.
"""

from upstash_redis import Redis
from app.database.lua_scripts import (
    CREATE_TASK_SCRIPT,
    TOGGLE_COMPLETE_SCRIPT,
    SOFT_DELETE_SCRIPT,
    GET_USER_TASKS_SCRIPT
)
from app.models.task import Task, CreateTaskRequest, UpdateTaskRequest
from datetime import datetime, timezone
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TaskService:
    """
    Service layer for task management operations.
    Implements business logic and Redis data access.
    """
    
    def __init__(self, redis: Redis):
        self.redis = redis
    
    def _get_iso_timestamp(self) -> str:
        """Get current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()
    
    async def create_task(
        self,
        user_id: str,
        task_data: CreateTaskRequest
    ) -> Task:
        """
        Create a new task (root or subtask).
        
        Args:
            user_id: ID of the user creating the task
            task_data: Task creation request data
            
        Returns:
            Task: Newly created task with generated ID
            
        Raises:
            Exception: If parent task doesn't exist (for subtasks)
        """
        timestamp = self._get_iso_timestamp()
        
        # Validate parent task exists if not root
        if task_data.parent_id != "0":
            parent_exists = await self.redis.exists(f"task:{task_data.parent_id}")
            if not parent_exists:
                raise ValueError(f"Parent task {task_data.parent_id} does not exist")
        
        # Execute atomic creation script
        try:
            task_id = await self.redis.eval(
                CREATE_TASK_SCRIPT,
                keys=[],
                args=[
                    user_id,
                    task_data.title,
                    task_data.description,
                    task_data.parent_id,
                    timestamp
                ]
            )
            
            logger.info(f"✅ Created task {task_id} for user {user_id}")
            
            # Return created task
            return Task(
                id=str(task_id),
                user_id=user_id,
                title=task_data.title,
                description=task_data.description,
                parent_id=task_data.parent_id,
                created_at=timestamp,
                completed_at="",
                deleted_at="",
                updated_at=timestamp,
                subtasks=[]
            )
        except Exception as e:
            logger.error(f"❌ Failed to create task: {e}")
            raise
    
    async def get_user_tasks(self, user_id: str) -> List[Task]:
        """
        Retrieve all tasks for a user with hierarchical structure.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List[Task]: Root-level tasks with nested subtasks
        """
        try:
            # Execute batch retrieval script
            raw_tasks = await self.redis.eval(
                GET_USER_TASKS_SCRIPT,
                keys=[],
                args=[user_id]
            )
            
            if not raw_tasks:
                return []
            
            # Parse raw Redis response into Task objects
            tasks_dict: Dict[str, Task] = {}
            
            # Convert flat array to list of dicts
            # Redis returns: [key1, val1, key2, val2, ...]
            for i in range(0, len(raw_tasks), 2):
                if i == 0 or raw_tasks[i] == b'id':  # Start of new task
                    task_data = {}
                    # Collect all fields for this task
                    j = i
                    while j < len(raw_tasks) and j < i + 18:  # 9 fields * 2
                        key = raw_tasks[j].decode() if isinstance(raw_tasks[j], bytes) else raw_tasks[j]
                        val = raw_tasks[j+1].decode() if isinstance(raw_tasks[j+1], bytes) else raw_tasks[j+1]
                        task_data[key] = val
                        j += 2
                    
                    if 'id' in task_data:
                        task = Task(**task_data, subtasks=[])
                        tasks_dict[task.id] = task
            
            # Build hierarchy: attach subtasks to parents
            root_tasks = []
            
            for task in tasks_dict.values():
                if task.parent_id == "0":
                    root_tasks.append(task)
                elif task.parent_id in tasks_dict:
                    tasks_dict[task.parent_id].subtasks.append(task)
            
            # Recursively sort subtasks by created_at
            def sort_subtasks(task: Task):
                task.subtasks.sort(key=lambda t: t.created_at)
                for subtask in task.subtasks:
                    sort_subtasks(subtask)
            
            for task in root_tasks:
                sort_subtasks(task)
            
            root_tasks.sort(key=lambda t: t.created_at, reverse=True)
            
            logger.info(f"📥 Retrieved {len(tasks_dict)} tasks for user {user_id}")
            return root_tasks
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve tasks: {e}")
            raise
    
    async def update_task(
        self,
        user_id: str,
        update_data: UpdateTaskRequest
    ) -> Task:
        """
        Update task details or toggle completion status.
        
        Args:
            user_id: ID of the user (for authorization)
            update_data: Update request data
            
        Returns:
            Task: Updated task
            
        Raises:
            ValueError: If task doesn't exist or unauthorized
        """
        task_key = f"task:{update_data.task_id}"
        timestamp = self._get_iso_timestamp()
        
        # Verify task exists and belongs to user
        task_user_id = await self.redis.hget(task_key, "user_id")
        if not task_user_id:
            raise ValueError(f"Task {update_data.task_id} not found")
        
        if task_user_id != user_id:
            raise ValueError("Unauthorized: Task belongs to different user")
        
        # Handle completion toggle
        if update_data.completed is not None:
            result = await self.redis.eval(
                TOGGLE_COMPLETE_SCRIPT,
                keys=[],
                args=[update_data.task_id, timestamp]
            )
            logger.info(f"✅ Task {update_data.task_id} marked as {result}")
        
        # Handle field updates
        update_fields = {}
        if update_data.title is not None:
            update_fields['title'] = update_data.title
        if update_data.description is not None:
            update_fields['description'] = update_data.description
        
        if update_fields:
            update_fields['updated_at'] = timestamp
            await self.redis.hset(task_key, update_fields)
            logger.info(f"✅ Updated task {update_data.task_id} fields")
        
        # Fetch and return updated task
        task_data = await self.redis.hgetall(task_key)
        return Task(**task_data, subtasks=[])
    
    async def delete_tasks(
        self,
        user_id: str,
        task_ids: List[str]
    ) -> int:
        """
        Soft delete tasks with cascade to subtasks.
        
        Args:
            user_id: ID of the user (for authorization)
            task_ids: List of task IDs to delete
            
        Returns:
            int: Total number of tasks deleted (including subtasks)
            
        Raises:
            ValueError: If any task doesn't exist or unauthorized
        """
        timestamp = self._get_iso_timestamp()
        
        # Verify all tasks belong to user
        for task_id in task_ids:
            task_user_id = await self.redis.hget(f"task:{task_id}", "user_id")
            if not task_user_id:
                raise ValueError(f"Task {task_id} not found")
            if task_user_id != user_id:
                raise ValueError(f"Unauthorized: Task {task_id} belongs to different user")
        
        # Execute atomic soft delete with cascade
        try:
            deleted_count = await self.redis.eval(
                SOFT_DELETE_SCRIPT,
                keys=[],
                args=[*task_ids, timestamp]
            )
            
            logger.info(f"🗑️ Soft deleted {deleted_count} tasks (including subtasks)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Failed to delete tasks: {e}")
            raise
