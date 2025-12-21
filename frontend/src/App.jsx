/**
 * Main application component
 */

import { useState } from 'react';
import { useTasks } from './hooks/useTasks';
import { TaskList } from './components/TaskList';
import { TaskForm } from './components/TaskForm';
import './App.css';

function App() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  
  const {
    tasks,
    loading,
    error,
    createTask,
    updateTask,
    toggleComplete,
    deleteTasks,
    refreshTasks,
    reconnectSSE,
    isSSEConnected
  } = useTasks();

  const handleCreateTask = async (taskData) => {
    await createTask(taskData);
    setShowCreateForm(false);
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading tasks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">📋 Hierarchical Todo</h1>
          
          <div className="header-actions">
            {/* SSE Connection Status */}
            <div className={`connection-status ${isSSEConnected ? 'connected' : 'disconnected'}`}>
              <span className="status-indicator"></span>
              <span className="status-text">
                {isSSEConnected ? 'Live' : 'Reconnecting...'}
              </span>
            </div>

            {/* Refresh Button */}
            <button
              onClick={refreshTasks}
              className="btn-icon"
              title="Refresh tasks"
            >
              🔄
            </button>

            {/* Reconnect SSE Button */}
            {!isSSEConnected && (
              <button
                onClick={reconnectSSE}
                className="btn-reconnect"
                title="Reconnect real-time updates"
              >
                Reconnect
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Error Display */}
      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          <span className="error-message">{error}</span>
          <button onClick={refreshTasks} className="btn-retry">
            Retry
          </button>
        </div>
      )}

      {/* Main Content */}
      <main className="app-main">
        <div className="container">
          {/* Create Task Section */}
          <div className="create-task-section">
            {showCreateForm ? (
              <div className="create-task-form">
                <h2>Create New Task</h2>
                <TaskForm
                  onSubmit={handleCreateTask}
                  onCancel={() => setShowCreateForm(false)}
                  parentId="0"
                />
              </div>
            ) : (
              <button
                onClick={() => setShowCreateForm(true)}
                className="btn-create-task"
              >
                ➕ Create New Task
              </button>
            )}
          </div>

          {/* Task List */}
          <TaskList
            tasks={tasks}
            onToggleComplete={toggleComplete}
            onUpdate={updateTask}
            onDelete={deleteTasks}
            onAddSubtask={createTask}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>
          {tasks.length} {tasks.length === 1 ? 'task' : 'tasks'} total
        </p>
      </footer>
    </div>
  );
}

export default App;
