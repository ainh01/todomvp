/**  
 * API client for task operations.  
 * Provides axios instance with JWT authentication and all CRUD methods.  
 */  

import axios from 'axios';  

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';  
const JWT_TOKEN = import.meta.env.VITE_JWT_TOKEN;  

/**  
 * Axios instance with JWT authentication interceptor.  
 * Automatically adds Authorization header to all requests.  
 */  
const apiClient = axios.create({  
  baseURL: API_URL,  
  headers: {  
    'Content-Type': 'application/json'  
  }  
});  

// Request interceptor to add JWT token  
apiClient.interceptors.request.use(  
  (config) => {  
    if (JWT_TOKEN) {  
      config.headers.Authorization = `Bearer ${JWT_TOKEN}`;  
    }  
    return config;  
  },  
  (error) => {  
    return Promise.reject(error);  
  }  
);  

// Response interceptor for error handling  
apiClient.interceptors.response.use(  
  (response) => response,  
  (error) => {  
    if (error.response?.status === 401) {  
      console.error('Authentication failed - check JWT token');  
    }  
    return Promise.reject(error);  
  }  
);  

/**  
 * Task API methods  
 */  

/**  
 * Create a new task (root or subtask)  
 * @param {Object} taskData - Task creation data  
 * @param {string} taskData.title - Task title (required)  
 * @param {string} taskData.description - Task description (optional)  
 * @param {string} taskData.parent_id - Parent task ID, "0" for root tasks  
 * @returns {Promise<Object>} Created task object  
 */  
export const createTask = async (taskData) => {  
  const response = await apiClient.post('/addnewusertodo', taskData);  
  return response.data.task;  
};  

/**  
 * Fetch all tasks for authenticated user  
 * @returns {Promise<Array>} Array of root-level tasks with nested subtasks  
 */  
export const getTasks = async () => {  
  const response = await apiClient.get('/getusertodos');  
  return response.data.tasks;  
};  

/**  
 * Update existing task  
 * @param {Object} updateData - Update data  
 * @param {string} updateData.task_id - Task ID to update  
 * @param {string} [updateData.title] - New title  
 * @param {string} [updateData.description] - New description  
 * @param {boolean} [updateData.completed] - Completion status  
 * @returns {Promise<Object>} Updated task object  
 */  
export const updateTask = async (updateData) => {  
  const response = await apiClient.put('/edittodo', updateData);  
  return response.data.task;  
};  

/**  
 * Delete one or more tasks (soft delete with cascade)  
 * @param {Array<string>} taskIds - Array of task IDs to delete  
 * @returns {Promise<Object>} Deletion result with count  
 */  
export const deleteTasks = async (taskIds) => {  
  const response = await apiClient.delete('/deletetodos', {  
    data: { task_ids: taskIds }  
  });  
  return response.data;  
};  

/**  
 * Get SSE stream URL with authentication  
 * @returns {string} Full SSE endpoint URL with token  
 */  
export const getSSEUrl = () => {  
  return `${API_URL}/stream`;  
};  

export default apiClient;  