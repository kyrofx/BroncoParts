import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../services/AuthContext';

function EditProject() {
    const { projectId } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();

    const [projectData, setProjectData] = useState({
        name: '',
        description: '',
        prefix: '',
        onshape_document_id: '',
        onshape_workspace_id: '',
        onshape_access_token: ''
    });
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchProjectDetails = async () => {
            setIsLoading(true);
            try {
                const response = await api.get(`/projects/${projectId}`);
                const fetchedProject = response.data.project;
                setProjectData({
                    name: fetchedProject.name || '',
                    description: fetchedProject.description || '',
                    prefix: fetchedProject.prefix || '',
                    onshape_document_id: fetchedProject.onshape_document_id || '',
                    onshape_workspace_id: fetchedProject.onshape_workspace_id || '',
                    onshape_access_token: fetchedProject.onshape_access_token || ''
                });
                setError('');
            } catch (err) {
                setError('Failed to fetch project details. ' + (err.response?.data?.message || err.message));
                console.error(err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchProjectDetails();
    }, [projectId]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setProjectData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        if (!projectData.name || !projectData.prefix) {
            setError('Project name and prefix are required.');
            setIsLoading(false);
            return;
        }

        try {
            await api.put(`/projects/${projectId}`, projectData);
            alert('Project updated successfully!');
            navigate(`/projects/${projectId}`); // Navigate back to the project details page
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to update project. Please try again.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    // Check permissions
    // Corrected to use user.permission (singular) and to check after isLoading is false
    const canEditProject = !isLoading && (user?.permission === 'admin' || user?.permission === 'project_manager');

    if (isLoading) return <p>Loading project data...</p>;
    
    // Moved permission check to after isLoading is false to ensure user data is available
    if (!canEditProject) { 
        return <p>You do not have permission to edit this project.</p>;
    }

    if (error && !projectData.name && !isLoading) return <p sx={{ color: 'error.main' }}>{error}</p>; // Show error if initial fetch failed

    return (
        <div className="container mt-4">
            <h2>Edit Project: {projectData.name || `ID: ${projectId}`}</h2>
            {error && <div className="alert alert-danger" role="alert">{error}</div>}
            <form onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label htmlFor="name" className="form-label">Project Name</label>
                    <input 
                        type="text" 
                        className="form-control" 
                        id="name" 
                        name="name" 
                        value={projectData.name} 
                        onChange={handleChange} 
                        required 
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="description" className="form-label">Description</label>
                    <textarea 
                        className="form-control" 
                        id="description" 
                        name="description" 
                        rows="3" 
                        value={projectData.description} 
                        onChange={handleChange}
                    ></textarea>
                </div>
                <div className="mb-3">
                    <label htmlFor="prefix" className="form-label">Prefix</label>
                    <input
                        type="text"
                        className="form-control"
                        id="prefix"
                        name="prefix"
                        value={projectData.prefix}
                        onChange={handleChange}
                        required
                        maxLength="10" // Assuming a reasonable max length for prefix
                    />
                     <small className="form-text text-muted">Short prefix for part numbers. Max 10 characters.</small>
                </div>
                <div className="mb-3">
                    <label htmlFor="onshape_document_id" className="form-label">Onshape Document ID</label>
                    <input
                        type="text"
                        className="form-control"
                        id="onshape_document_id"
                        name="onshape_document_id"
                        value={projectData.onshape_document_id}
                        onChange={handleChange}
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="onshape_workspace_id" className="form-label">Onshape Workspace ID</label>
                    <input
                        type="text"
                        className="form-control"
                        id="onshape_workspace_id"
                        name="onshape_workspace_id"
                        value={projectData.onshape_workspace_id}
                        onChange={handleChange}
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="onshape_access_token" className="form-label">Onshape Access Token</label>
                    <input
                        type="text"
                        className="form-control"
                        id="onshape_access_token"
                        name="onshape_access_token"
                        value={projectData.onshape_access_token}
                        onChange={handleChange}
                    />
                </div>
                
                <button type="submit" className="btn btn-primary" disabled={isLoading || !canEditProject}>
                    {isLoading ? 'Updating...' : 'Update Project'}
                </button>
            </form>
        </div>
    );
}

export default EditProject;
