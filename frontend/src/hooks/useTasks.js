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
   * ✅ Helper: Check if task exists in tree (prevents duplicates)
   */
  const taskExistsInTree = useCallback((taskList, taskId) => {
    for (const task of taskList) {
      if (task.id === taskId) return true;
      if (task.subtasks && task.subtasks.length > 0) {
        if (taskExistsInTree(task.subtasks, taskId)) return true;
      }
    }
    return false;
  }, []);

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
    if (newTask.parent_id === "0") {
      return [newTask, ...taskList];
    }

    return taskList.map(task => {
      if (task.id === newTask.parent_id) {
        return {
          ...task,
          subtasks: [...(task.subtasks || []), newTask]
        };
      }
      if (task.subtasks?.length) {
        return {
          ...task,
          subtasks: addTaskToTree(task.subtasks, newTask)
        };
      }
      return task;
    });
  }, []);

  /**
   * ✅ SSE Event Handler - Task Created
   */
  const handleTaskCreated = useCallback((newTask) => {
    setTasks(prevTasks => {
      // ✅ Check if task already exists (prevent duplicates)
      if (taskExistsInTree(prevTasks, newTask.id)) {
        console.log('⚠️ Task already exists, skipping duplicate:', newTask.id);
        return prevTasks;
      }
      
      console.log('✅ Adding new task from SSE:', newTask.id);
      return addTaskToTree(prevTasks, newTask);
    });
  }, [addTaskToTree, taskExistsInTree]);

  /**
   * ✅ SSE Event Handler - Task Updated
   */
  const handleTaskUpdated = useCallback((updatedTask) => {
    setTasks(prevTasks => 
      updateTaskInTree(prevTasks, updatedTask.id, () => updatedTask)
    );
  }, [updateTaskInTree]);

  /**
   * ✅ SSE Event Handler - Task Deleted
   */
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
   * ✅ Create new task - NO OPTIMISTIC UPDATE
   * Let SSE handle the UI update for reliability
   */
  const handleCreateTask = useCallback(async (taskData) => {
    try {
      const newTask = await createTask(taskData);
      // ✅ Don't update state here - let SSE handle it
      console.log('✅ Task created, waiting for SSE event:', newTask.id);
      return newTask;
    } catch (err) {
      console.error('Failed to create task:', err);
      throw err;
    }
  }, []);

  /**
   * ✅ Update existing task - NO OPTIMISTIC UPDATE
   * Let SSE handle the UI update for reliability
   */
  const handleUpdateTask = useCallback(async (taskId, updateData) => {
    try {
      const updatedTask = await updateTask({ task_id: taskId, ...updateData });
      // ✅ Don't update state here - let SSE handle it
      console.log('✅ Task updated, waiting for SSE event:', taskId);
      return updatedTask;
    } catch (err) {
      console.error('Failed to update task:', err);
      throw err;
    }
  }, []);

  /**
   * ✅ Toggle task completion status - NO OPTIMISTIC UPDATE
   * Let SSE handle the UI update for reliability
   */
  const handleToggleComplete = useCallback(async (taskId, currentStatus) => {
    try {
      await updateTask({
        task_id: taskId,
        completed: !currentStatus
      });
      // ✅ Don't update state here - let SSE handle it
      console.log('✅ Task toggled, waiting for SSE event:', taskId);
    } catch (err) {
      console.error('Failed to toggle task completion:', err);
      throw err;
    }
  }, []);

  /**
   * ✅ Delete tasks - NO OPTIMISTIC UPDATE
   * Let SSE handle the UI update for reliability
   */
  const handleDeleteTasks = useCallback(async (taskIds) => {
    try {
      const result = await deleteTasks(taskIds);
      // ✅ Don't update state here - let SSE handle it
      console.log('✅ Tasks deleted, waiting for SSE event:', taskIds);
      return result;
    } catch (err) {
      console.error('Failed to delete tasks:', err);
      throw err;
    }
  }, []);

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
