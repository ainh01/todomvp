/**
 * Task list container component
 */

import { TaskItem } from './TaskItem';

export const TaskList = ({ tasks, onToggleComplete, onUpdate, onDelete, onAddSubtask }) => {
  if (tasks.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📝</div>
        <h2>No tasks yet</h2>
        <p>Create your first task to get started!</p>
      </div>
    );
  }

  return (
    <div className="task-list">
      {tasks.map(task => (
        <TaskItem
          key={task.id}
          task={task}
          onToggleComplete={onToggleComplete}
          onUpdate={onUpdate}
          onDelete={onDelete}
          onAddSubtask={onAddSubtask}
          level={0}
        />
      ))}
    </div>
  );
};
