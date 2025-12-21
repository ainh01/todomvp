/**
 * Individual task item component with hierarchical rendering
 */

import { useState } from 'react';
import { DeleteButton } from './DeleteButton';
import { TaskForm } from './TaskForm';
import { formatRelativeTime } from '../utils/dateFormat';

export const TaskItem = ({ task, onToggleComplete, onUpdate, onDelete, onAddSubtask, level = 0 }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [showSubtaskForm, setShowSubtaskForm] = useState(false);
  const [showSubtasks, setShowSubtasks] = useState(true);

  const isCompleted = Boolean(task.completed_at);
  const hasSubtasks = task.subtasks && task.subtasks.length > 0;

  const handleToggleComplete = async () => {
    try {
      await onToggleComplete(task.id, isCompleted);
    } catch (error) {
      console.error('Failed to toggle completion:', error);
    }
  };

  const handleUpdate = async (updateData) => {
    try {
      await onUpdate(task.id, updateData);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const handleAddSubtask = async (subtaskData) => {
    try {
      await onAddSubtask({ ...subtaskData, parent_id: task.id });
      setShowSubtaskForm(false);
    } catch (error) {
      console.error('Failed to add subtask:', error);
    }
  };

  const handleDelete = async (taskId) => {
    await onDelete([taskId]);
  };

  // Calculate indentation based on nesting level
  const indentStyle = {
    marginLeft: `${level * 24}px`,
    borderLeft: level > 0 ? '2px solid #e0e0e0' : 'none',
    paddingLeft: level > 0 ? '12px' : '0'
  };

  return (
    <div className="task-item" style={indentStyle}>
      <div className={`task-content ${isCompleted ? 'task-completed' : ''}`}>
        {/* Checkbox for completion toggle */}
        <input
          type="checkbox"
          checked={isCompleted}
          onChange={handleToggleComplete}
          className="task-checkbox"
          title={isCompleted ? 'Mark as incomplete' : 'Mark as complete'}
        />

        {/* Task details or edit form */}
        {isEditing ? (
          <div className="task-edit-form">
            <TaskForm
              initialData={task}
              onSubmit={handleUpdate}
              onCancel={() => setIsEditing(false)}
              parentId={task.parent_id}
            />
          </div>
        ) : (
          <div className="task-details" onClick={() => !isCompleted && setIsEditing(true)}>
            <h3 className="task-title">{task.title}</h3>
            {task.description && (
              <p className="task-description">{task.description}</p>
            )}
            <div className="task-meta">
              <span className="task-date" title={task.created_at}>
                Created {formatRelativeTime(task.created_at)}
              </span>
              {isCompleted && (
                <span className="task-completed-badge">
                  ✓ Completed {formatRelativeTime(task.completed_at)}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="task-actions">
          {!isCompleted && !isEditing && (
            <>
              <button
                onClick={() => setShowSubtaskForm(!showSubtaskForm)}
                className="btn-add-subtask"
                title="Add subtask"
              >
                ➕
              </button>
              <button
                onClick={() => setIsEditing(true)}
                className="btn-edit"
                title="Edit task"
              >
                ✏️
              </button>
            </>
          )}
          
          <DeleteButton
            taskId={task.id}
            onDelete={handleDelete}
            disabled={isEditing}
          />

          {/* Collapse/expand subtasks */}
          {hasSubtasks && (
            <button
              onClick={() => setShowSubtasks(!showSubtasks)}
              className="btn-toggle-subtasks"
              title={showSubtasks ? 'Collapse subtasks' : 'Expand subtasks'}
            >
              {showSubtasks ? '▼' : '▶'}
            </button>
          )}
        </div>
      </div>

      {/* Subtask creation form */}
      {showSubtaskForm && !isCompleted && (
        <div className="subtask-form-container">
          <TaskForm
            onSubmit={handleAddSubtask}
            onCancel={() => setShowSubtaskForm(false)}
            parentId={task.id}
          />
        </div>
      )}

      {/* Render subtasks recursively */}
      {hasSubtasks && showSubtasks && (
        <div className="subtasks-container">
          {task.subtasks.map(subtask => (
            <TaskItem
              key={subtask.id}
              task={subtask}
              onToggleComplete={onToggleComplete}
              onUpdate={onUpdate}
              onDelete={onDelete}
              onAddSubtask={onAddSubtask}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};
