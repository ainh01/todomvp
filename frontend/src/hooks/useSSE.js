/**  
 * Custom hook for Server-Sent Events (SSE) connection.  
 * Handles connection, reconnection with exponential backoff, and event processing.  
 */  

import { useEffect, useRef, useCallback } from 'react';  
import { getSSEUrl } from '../api/taskApi';  

const JWT_TOKEN = import.meta.env.VITE_JWT_TOKEN;  

/**  
 * Hook for managing SSE connection with automatic reconnection.  
 *   
 * @param {Function} onTaskCreated - Callback for task creation events  
 * @param {Function} onTaskUpdated - Callback for task update events  
 * @param {Function} onTaskDeleted - Callback for task deletion events  
 * @param {boolean} enabled - Whether SSE connection is enabled  
 * @returns {Object} Connection status and manual reconnect function  
 */  
export const useSSE = (onTaskCreated, onTaskUpdated, onTaskDeleted, enabled = true) => {  
  const eventSourceRef = useRef(null);  
  const reconnectTimeoutRef = useRef(null);  
  const reconnectAttemptsRef = useRef(0);  
  const maxReconnectDelay = 30000; // 30 seconds max  
  const baseReconnectDelay = 1000; // 1 second base  

  /**  
   * Calculate exponential backoff delay for reconnection  
   */  
  const getReconnectDelay = useCallback(() => {  
    const delay = Math.min(  
      baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current),  
      maxReconnectDelay  
    );  
    return delay + Math.random() * 1000; // Add jitter  
  }, []);  

  /**  
   * Connect to SSE stream  
   */  
  const connect = useCallback(() => {  
    if (!enabled || !JWT_TOKEN) {  
      console.warn('SSE connection disabled or JWT token missing');  
      return;  
    }  

    // Close existing connection  
    if (eventSourceRef.current) {  
      eventSourceRef.current.close();  
    }  

    console.log('📡 Connecting to SSE stream...');  

    try {  
      // Note: EventSource doesn't support custom headers directly  
      // For production, use a library like @microsoft/fetch-event-source  
      // or pass token as query parameter (less secure)  
      const url = `${getSSEUrl()}?token=${JWT_TOKEN}`;  
      const eventSource = new EventSource(url);  

      eventSource.onopen = () => {  
        console.log('✅ SSE connection established');  
        reconnectAttemptsRef.current = 0;  
      };  

      eventSource.onmessage = (event) => {  
        try {  
          const data = JSON.parse(event.data);  
          
          switch (data.type) {  
            case 'connected':  
              console.log('🔗 SSE connected at', data.timestamp);  
              break;  
              
            case 'task_created':  
              console.log('📝 Task created:', data.task);  
              onTaskCreated?.(data.task);  
              break;  
              
            case 'task_updated':  
              console.log('✏️ Task updated:', data.task);  
              onTaskUpdated?.(data.task);  
              break;  
              
            case 'task_deleted':  
              console.log('🗑️ Tasks deleted:', data.task_ids);  
              onTaskDeleted?.(data.task_ids, data.deleted_count);  
              break;  
              
            default:  
              console.log('📨 Unknown event type:', data.type);  
          }  
        } catch (error) {  
          console.error('Failed to parse SSE message:', error);  
        }  
      };  

      eventSource.onerror = (error) => {  
        console.error('❌ SSE connection error:', error);  
        eventSource.close();  
        
        // Attempt reconnection with exponential backoff  
        reconnectAttemptsRef.current++;  
        const delay = getReconnectDelay();  
        
        console.log(`🔄 Reconnecting in ${Math.round(delay / 1000)}s (attempt ${reconnectAttemptsRef.current})`);  
        
        reconnectTimeoutRef.current = setTimeout(() => {  
          connect();  
        }, delay);  
      };  

      eventSourceRef.current = eventSource;  

    } catch (error) {  
      console.error('Failed to create SSE connection:', error);  
    }  
  }, [enabled, onTaskCreated, onTaskUpdated, onTaskDeleted, getReconnectDelay]);  

  /**  
   * Disconnect from SSE stream  
   */  
  const disconnect = useCallback(() => {  
    if (reconnectTimeoutRef.current) {  
      clearTimeout(reconnectTimeoutRef.current);  
      reconnectTimeoutRef.current = null;  
    }  

    if (eventSourceRef.current) {  
      eventSourceRef.current.close();  
      eventSourceRef.current = null;  
      console.log('👋 SSE connection closed');  
    }  
  }, []);  

  /**  
   * Manual reconnection trigger  
   */  
  const reconnect = useCallback(() => {  
    reconnectAttemptsRef.current = 0;  
    disconnect();  
    connect();  
  }, [connect, disconnect]);  

  // Setup and cleanup  
  useEffect(() => {  
    connect();  
    return () => {  
      disconnect();  
    };  
  }, [connect, disconnect]);  

  return {  
    reconnect,  
    isConnected: eventSourceRef.current?.readyState === EventSource.OPEN  
  };  
};  