import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../services/AuthContext';

const CreateProject = () => {
  const [name, setName] = useState('');
  const [prefix, setPrefix] = useState('');
  const [description, setDescription] = useState('');
  const [hideDashboards, setHideDashboards] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth(); // To check permissions if needed for UI elements

  console.log('User object in CreateProject:', user); // <-- ADD THIS LINE

  // Basic permission check for UI (actual enforcement is on backend)
  if (user && !['editor', 'admin'].includes(user.permission)) {
    return <p>You do not have permission to create new projects.</p>;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (!name.trim() || !prefix.trim()) {
      setError('Project Name and Prefix are required.');
      setLoading(false);
      return;
    }

    try {
      const projectData = {
        name,
        prefix,
        description,
        hide_dashboards: hideDashboards,
      };
      const response = await api.post('/projects', projectData);
      alert('Project created successfully!'); // Replace with a more subtle notification
      // Navigate to the new project's page or the projects list
      navigate(`/projects/${response.data.project.id}`); // Assuming API returns project with id
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to create project. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div>
      <h2>Create New Project</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="name">Project Name:</label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="prefix">Project Prefix:</label>
          <input
            type="text"
            id="prefix"
            value={prefix}
            onChange={(e) => setPrefix(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="description">Description:</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="hideDashboards">
            <input
              type="checkbox"
              id="hideDashboards"
              checked={hideDashboards}
              onChange={(e) => setHideDashboards(e.target.checked)}
            />
            Hide from main dashboards
          </label>
        </div>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? 'Creating Project...' : 'Create Project'}
        </button>
      </form>
    </div>
  );
};

export default CreateProject;
