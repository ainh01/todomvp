from typing import Dict, Set, AsyncGenerator
from asyncio import Queue, create_task, sleep
import json
import logging

logger = logging.getLogger(__name__)


class SSEManager:
    def __init__(self):
        self._connections: Dict[str, Set[Queue]] = {}
    
    async def subscribe(self, user_id: str) -> AsyncGenerator[str, None]:
        queue: Queue = Queue()
        
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(queue)
        
        logger.info(f"📡 User {user_id} connected to SSE (total: {len(self._connections[user_id])})")
        
        try:
            yield f"data: {json.dumps({'type': 'connected', 'timestamp': str(datetime.now())})}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f": heartbeat\n\n"
                    
        except GeneratorExit:
            logger.info(f"📡 User {user_id} disconnected from SSE")
        finally:
            if user_id in self._connections:
                self._connections[user_id].discard(queue)
                if not self._connections[user_id]:
                    del self._connections[user_id]
    
    async def broadcast_to_user(self, user_id: str, event: dict):
        if user_id not in self._connections:
            logger.debug(f"No active connections for user {user_id}")
            return
        disconnected_queues = []
        for queue in self._connections[user_id]:
            try:
                await queue.put(event)
            except Exception as e:
                logger.error(f"Failed to send event to queue: {e}")
                disconnected_queues.append(queue)
        for queue in disconnected_queues:
            self._connections[user_id].discard(queue)
        
        logger.debug(f"📤 Broadcasted {event['type']} to {len(self._connections[user_id])} connections")
    
    async def broadcast_task_created(self, user_id: str, task: dict):
        """Broadcast task creation event."""
        await self.broadcast_to_user(user_id, {
            'type': 'task_created',
            'task': task
        })
    
    async def broadcast_task_updated(self, user_id: str, task: dict):
        """Broadcast task update event."""
        await self.broadcast_to_user(user_id, {
            'type': 'task_updated',
            'task': task
        })
    
    async def broadcast_task_deleted(self, user_id: str, task_ids: list, deleted_count: int):
        """Broadcast task deletion event."""
        await self.broadcast_to_user(user_id, {
            'type': 'task_deleted',
            'task_ids': task_ids,
            'deleted_count': deleted_count
        })
sse_manager = SSEManager()