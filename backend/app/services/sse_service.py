"""
Server-Sent Events (SSE) service for real-time updates.
Manages user-specific event streams and broadcasts task changes.
"""

from typing import Dict, Set, AsyncGenerator
from asyncio import Queue, create_task, sleep
import json
import logging

logger = logging.getLogger(__name__)


class SSEManager:
    """
    Manages SSE connections and event broadcasting.
    Maintains separate queues for each user's active connections.
    """
    
    def __init__(self):
        # Maps user_id to set of queues (one per connection)
        self._connections: Dict[str, Set[Queue]] = {}
    
    async def subscribe(self, user_id: str) -> AsyncGenerator[str, None]:
        """
        Create SSE stream for a user.
        
        Args:
            user_id: ID of the user subscribing
            
        Yields:
            str: SSE-formatted event messages
        """
        queue: Queue = Queue()
        
        # Register this connection
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(queue)
        
        logger.info(f"📡 User {user_id} connected to SSE (total: {len(self._connections[user_id])})")
        
        try:
            # Send initial connection confirmation
            yield f"data: {json.dumps({'type': 'connected', 'timestamp': str(datetime.now())})}\n\n"
            
            # Keep connection alive and send events
            while True:
                try:
                    # Wait for events with timeout for heartbeat
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
                    
        except GeneratorExit:
            logger.info(f"📡 User {user_id} disconnected from SSE")
        finally:
            # Clean up connection
            if user_id in self._connections:
                self._connections[user_id].discard(queue)
                if not self._connections[user_id]:
                    del self._connections[user_id]
    
    async def broadcast_to_user(self, user_id: str, event: dict):
        """
        Broadcast event to all connections for a specific user.
        
        Args:
            user_id: Target user ID
            event: Event data dictionary
        """
        if user_id not in self._connections:
            logger.debug(f"No active connections for user {user_id}")
            return
        
        # Send to all user's connections
        disconnected_queues = []
        for queue in self._connections[user_id]:
            try:
                await queue.put(event)
            except Exception as e:
                logger.error(f"Failed to send event to queue: {e}")
                disconnected_queues.append(queue)
        
        # Clean up disconnected queues
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


# Global SSE manager instance
sse_manager = SSEManager()


# Import for timestamp generation
from datetime import datetime
import asyncio
