/**
 * Task creation and editing form component
 */

import { useState, useEffect } from 'react';

export const TaskForm = ({ onSubmit, onCancel, initialData = null, parentId = "0" }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (initialData) {
      setTitle(initialData.title || '');
      setDescription(initialData.description || '');
    }
  }, [initialData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!title.trim()) {
      alert('Task title is required');
      return;
    }

    try {
      setSubmitting(true);
      await onSubmit({
        title: title.trim(),
        description: description.trim(),
        parent_id: parentId
      });
      
      // Reset form
      setTitle('');
      setDescription('');
    } catch (error) {
      console.error('Form submission failed:', error);
      alert('Failed to save task. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="task-form">
      <div className="form-group">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Task title *"
          maxLength={500}
          disabled={submitting}
          className="form-input"
          autoFocus
        />
      </div>
      
      <div className="form-group">
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description (optional)"
          maxLength={5000}
          rows={3}
          disabled={submitting}
          className="form-textarea"
        />
      </div>
      
      <div className="form-actions">
        <button
          type="submit"
          disabled={submitting || !title.trim()}
          className="btn-primary"
        >
          {submitting ? 'Saving...' : (initialData ? 'Update' : 'Add Task')}
        </button>
        
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="btn-secondary"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
};
