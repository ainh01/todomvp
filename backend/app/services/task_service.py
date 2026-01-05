from upstash_redis.asyncio import Redis
from app.database.lua_scripts import (
    CREATE_TASK_SCRIPT,
    TOGGLE_COMPLETE_SCRIPT,
    SOFT_DELETE_SCRIPT,
    GET_USER_TASKS_SCRIPT
)
from app.models.task import Task, CreateTaskRequest, UpdateTaskRequest
from datetime import datetime, timezone
from typing import List, Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)


class TaskService:
    
    def __init__(self, redis: Redis):
        self.redis = redis
    
    def _get_iso_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()
    
    def _get_unix_timestamp(self) -> float:
        return time.time()
    
    async def create_task(
        self,
        user_id: str,
        task_data: CreateTaskRequest
    ) -> Task:
        iso_timestamp = self._get_iso_timestamp()
        unix_timestamp = self._get_unix_timestamp()
        
        if task_data.parent_id != "0":
            parent_exists = await self.redis.exists(f"task:{task_data.parent_id}")
            if not parent_exists:
                raise ValueError(f"Parent task {task_data.parent_id} does not exist")
        
        try:
            task_id = await self.redis.eval(
                CREATE_TASK_SCRIPT,
                keys=[],
                args=[
                    user_id,
                    task_data.title,
                    task_data.description,
                    task_data.parent_id,
                    iso_timestamp,
                    str(unix_timestamp)
                ]
            )
            
            logger.info(f"Created task {task_id} for user {user_id}")
            
            return Task(
                id=str(task_id),
                user_id=user_id,
                title=task_data.title,
                description=task_data.description,
                parent_id=task_data.parent_id,
                created_at=iso_timestamp,
                completed_at="",
                deleted_at="",
                updated_at=iso_timestamp,
                subtasks=[]
            )
        except Exception as e:
            logger.error(f"❌ Failed to create task: {e}")
            raise
    


    async def get_user_tasks(self, user_id: str) -> List[Task]:
        try:
            raw_tasks = await self.redis.eval(
                GET_USER_TASKS_SCRIPT,
                keys=[],
                args=[user_id]
            )
            
            logger.info(f"🔍 DEBUG: raw_tasks type = {type(raw_tasks)}")
            logger.info(f"🔍 DEBUG: raw_tasks length = {len(raw_tasks) if raw_tasks else 0}")
            if raw_tasks and len(raw_tasks) <= 50: 
                logger.info(f"🔍 DEBUG: raw_tasks content = {raw_tasks}")
            
            if not raw_tasks:
                logger.info(f"📥 No tasks found for user {user_id}")
                return []
            
            if not isinstance(raw_tasks, list):
                logger.error(f"❌ Unexpected Redis response type: {type(raw_tasks)}")
                return []
            
            if len(raw_tasks) > 0 and isinstance(raw_tasks[0], list):
                logger.info("🔍 Detected nested array structure, flattening...")
                flattened = []
                for task_array in raw_tasks:
                    if isinstance(task_array, list):
                        flattened.extend(task_array)
                raw_tasks = flattened
                logger.info(f"🔍 Flattened to {len(raw_tasks)} elements")
            
            tasks_dict: Dict[str, Task] = {}
            
            i = 0
            task_count = 0
            
            while i < len(raw_tasks):
                task_data = {}
                
                fields_collected = 0
                
                while fields_collected < 9 and i + 1 < len(raw_tasks):
                    try:
                        key = raw_tasks[i].decode('utf-8') if isinstance(raw_tasks[i], bytes) else str(raw_tasks[i])
                        val = raw_tasks[i + 1].decode('utf-8') if isinstance(raw_tasks[i + 1], bytes) else str(raw_tasks[i + 1])
                        
                        task_data[key] = val
                        i += 2
                        fields_collected += 1
                        
                    except (AttributeError, UnicodeDecodeError) as e:
                        logger.error(f"❌ Error parsing field at index {i}: {e}")
                        i += 2 
                        continue
                
                if 'id' in task_data and task_data['id']:
                    try:
                        if task_data.get('deleted_at') and task_data['deleted_at'] != '':
                            logger.debug(f"Skipping deleted task {task_data['id']}")
                            continue
                        
                        task = Task(**task_data, subtasks=[])
                        tasks_dict[task.id] = task
                        task_count += 1
                        logger.debug(f"✅ Parsed task {task.id}: {task.title}")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to create Task object: {e}, data: {task_data}")
                        continue
                else:
                    logger.warning(f"⚠️ Task data missing 'id' field: {task_data}")
            
            logger.info(f"📊 Parsed {task_count} valid tasks from {len(raw_tasks)} elements")
            
            root_tasks = []
            
            for task in tasks_dict.values():
                if task.parent_id == "0":
                    root_tasks.append(task)
                elif task.parent_id in tasks_dict:
                    tasks_dict[task.parent_id].subtasks.append(task)
                else:
                    logger.warning(f"⚠️ Task {task.id} has missing parent {task.parent_id}, treating as root")
                    root_tasks.append(task)
            
            def sort_subtasks(task: Task):
                task.subtasks.sort(key=lambda t: t.created_at)
                for subtask in task.subtasks:
                    sort_subtasks(subtask)
            
            for task in root_tasks:
                sort_subtasks(task)
            
            root_tasks.sort(key=lambda t: t.created_at, reverse=True)
            
            logger.info(f"📥 Retrieved {len(tasks_dict)} tasks ({len(root_tasks)} root) for user {user_id}")
            return root_tasks
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve tasks: {e}", exc_info=True)
            return []


    async def update_task(
        self,
        user_id: str,
        update_data: UpdateTaskRequest
    ) -> Task:
        task_key = f"task:{update_data.task_id}"
        iso_timestamp = self._get_iso_timestamp()
        unix_timestamp = self._get_unix_timestamp()
        
        task_user_id = await self.redis.hget(task_key, "user_id")
        if not task_user_id:
            raise ValueError(f"Task {update_data.task_id} not found")
        
        if task_user_id != user_id:
            raise ValueError("Unauthorized: Task belongs to different user")
        
        if update_data.completed is not None:
            result = await self.redis.eval(
                TOGGLE_COMPLETE_SCRIPT,
                keys=[],
                args=[update_data.task_id, iso_timestamp, str(unix_timestamp)]
            )
            logger.info(f"✅ Task {update_data.task_id} marked as {result}")
        
        update_fields = {}
        if update_data.title is not None:
            update_fields['title'] = update_data.title
        if update_data.description is not None:
            update_fields['description'] = update_data.description
        
        if update_fields:
            update_fields['updated_at'] = iso_timestamp
            await self.redis.hset(task_key, update_fields)
            logger.info(f"✅ Updated task {update_data.task_id} fields")
        
        task_data = await self.redis.hgetall(task_key)
        return Task(**task_data, subtasks=[])
    
    async def delete_tasks(
        self,
        user_id: str,
        task_ids: List[str]
    ) -> int:
        iso_timestamp = self._get_iso_timestamp()
        
        for task_id in task_ids:
            task_user_id = await self.redis.hget(f"task:{task_id}", "user_id")
            if not task_user_id:
                raise ValueError(f"Task {task_id} not found")
            if task_user_id != user_id:
                raise ValueError(f"Unauthorized: Task {task_id} belongs to different user")
        
        try:
            deleted_count = await self.redis.eval(
                SOFT_DELETE_SCRIPT,
                keys=[],
                args=[*task_ids, iso_timestamp]
            )
            
            logger.info(f"🗑️ Soft deleted {deleted_count} tasks (including subtasks)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Failed to delete tasks: {e}")
            raise
