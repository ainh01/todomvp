/**
 * Custom hook for task state management.
 * Handles fetching, creating, updating, and deleting tasks with real-time updates.
 */

import { useState, useCallback, useEffect } from 'react';
import { getTasks, createTask, updateTask, deleteTasks } from '../api/taskApi';
import { useSSE } from './useSSE';

/**
 * Hook for managing task state and operations.
 * Integrates with SSE for real-time synchronization across clients.
 * 
 * @returns {Object} Task state and operation methods
 */
export const useTasks = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Fetch all tasks from API
   */
  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedTasks = await getTasks();
      setTasks(fetchedTasks);
    } catch (err) {
      console.error('Failed to fetch tasks:', err);
      setError(err.response?.data?.detail || 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Initial fetch on mount
   */
  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  /**
   * Helper function to recursively find and update task in tree
   */
  const updateTaskInTree = useCallback((taskList, taskId, updateFn) => {
    return taskList.map(task => {
      if (task.id === taskId) {
        return updateFn(task);
      }
      if (task.subtasks && task.subtasks.length > 0) {
        return {
          ...task,
          subtasks: updateTaskInTree(task.subtasks, taskId, updateFn)
        };
      }
      return task;
    });
  }, []);

  /**
   * Helper function to recursively remove task from tree
   */
  const removeTaskFromTree = useCallback((taskList, taskIds) => {
    const taskIdSet = new Set(taskIds);
    
    const filterTasks = (tasks) => {
      return tasks
        .filter(task => !taskIdSet.has(task.id))
        .map(task => ({
          ...task,
          subtasks: task.subtasks ? filterTasks(task.subtasks) : []
        }));
    };
    
    return filterTasks(taskList);
  }, []);

  /**
   * Helper function to add task to tree at correct location
   */
  const addTaskToTree = useCallback((taskList, newTask) => {
    // Root level task
    if (newTask.parent_id === "0") {
      return [newTask, ...taskList];
    }

    // Subtask - find parent and add
    return taskList.map(task => {
      if (task.id === newTask.parent_id) {
        return {
          ...task,
          subtasks: [...(task.subtasks || []), newTask]
        };
      }
      if (task.subtasks && task.subtasks.length > 0) {
        return {
          ...task,
          subtasks: addTaskToTree(task.subtasks, newTask)
        };
      }
      return task;
    });
  }, []);

  /**
   * SSE Event Handlers
   */
  const handleTaskCreated = useCallback((newTask) => {
    setTasks(prevTasks => addTaskToTree(prevTasks, newTask));
  }, [addTaskToTree]);

  const handleTaskUpdated = useCallback((updatedTask) => {
    setTasks(prevTasks => 
      updateTaskInTree(prevTasks, updatedTask.id, () => updatedTask)
    );
  }, [updateTaskInTree]);

  const handleTaskDeleted = useCallback((taskIds) => {
    setTasks(prevTasks => removeTaskFromTree(prevTasks, taskIds));
  }, [removeTaskFromTree]);

  // Setup SSE connection
  const { reconnect, isConnected } = useSSE(
    handleTaskCreated,
    handleTaskUpdated,
    handleTaskDeleted,
    true
  );

  /**
   * Create new task with optimistic update
   */
  const handleCreateTask = useCallback(async (taskData) => {
    try {
      const newTask = await createTask(taskData);
      // SSE will handle the update, but we do optimistic update for immediate feedback
      setTasks(prevTasks => addTaskToTree(prevTasks, newTask));
      return newTask;
    } catch (err) {
      console.error('Failed to create task:', err);
      throw err;
    }
  }, [addTaskToTree]);

  /**
   * Update existing task with optimistic update
   */
  const handleUpdateTask = useCallback(async (taskId, updateData) => {
    try {
      const updatedTask = await updateTask({ task_id: taskId, ...updateData });
      // SSE will handle the update, but we do optimistic update for immediate feedback
      setTasks(prevTasks => 
        updateTaskInTree(prevTasks, taskId, () => updatedTask)
      );
      return updatedTask;
    } catch (err) {
      console.error('Failed to update task:', err);
      throw err;
    }
  }, [updateTaskInTree]);

  /**
   * Toggle task completion status
   */
  const handleToggleComplete = useCallback(async (taskId, currentStatus) => {
    try {
      await updateTask({
        task_id: taskId,
        completed: !currentStatus
      });
      // SSE will handle the actual update
    } catch (err) {
      console.error('Failed to toggle task completion:', err);
      throw err;
    }
  }, []);

  /**
   * Delete tasks with optimistic update
   */
  const handleDeleteTasks = useCallback(async (taskIds) => {
    try {
      const result = await deleteTasks(taskIds);
      // SSE will handle the update, but we do optimistic update for immediate feedback
      setTasks(prevTasks => removeTaskFromTree(prevTasks, taskIds));
      return result;
    } catch (err) {
      console.error('Failed to delete tasks:', err);
      throw err;
    }
  }, [removeTaskFromTree]);

  return {
    tasks,
    loading,
    error,
    createTask: handleCreateTask,
    updateTask: handleUpdateTask,
    toggleComplete: handleToggleComplete,
    deleteTasks: handleDeleteTasks,
    refreshTasks: fetchTasks,
    reconnectSSE: reconnect,
    isSSEConnected: isConnected
  };
};
