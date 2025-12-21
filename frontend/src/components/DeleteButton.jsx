/**
 * Delete button component with confirmation dialog
 */

import { useState } from 'react';

export const DeleteButton = ({ taskId, onDelete, disabled = false }) => {
  const [showConfirm, setShowConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    try {
      setDeleting(true);
      await onDelete(taskId);
      setShowConfirm(false);
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Failed to delete task. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  if (showConfirm) {
    return (
      <div className="delete-confirm">
        <span className="delete-confirm-text">Delete this task and all subtasks?</span>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="btn-confirm-delete"
        >
          {deleting ? 'Deleting...' : 'Yes'}
        </button>
        <button
          onClick={() => setShowConfirm(false)}
          disabled={deleting}
          className="btn-cancel-delete"
        >
          Cancel
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => setShowConfirm(true)}
      disabled={disabled}
      className="btn-delete"
      title="Delete task"
    >
      🗑️
    </button>
  );
};
