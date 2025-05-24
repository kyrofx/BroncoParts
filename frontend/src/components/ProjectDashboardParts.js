import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';

// TODO: Implement filtering, sorting, and pagination for parts list

function ProjectDashboardParts() {
    const { projectId } = useParams();
    const [project, setProject] = useState(null);
    const [parts, setParts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchProjectParts = async () => {
            try {
                setLoading(true);
                const projectRes = await api.get(`/projects/${projectId}`);
                setProject(projectRes.data);

                // Assuming an endpoint like /projects/:projectId/parts exists
                // If not, this needs to be adjusted or parts fetched via a general /parts endpoint and filtered
                const partsRes = await api.get(`/projects/${projectId}/parts`); 
                setParts(partsRes.data);
                setError('');
            } catch (err) {
                setError('Failed to load parts for the project. ' + (err.response?.data?.message || err.message));
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchProjectParts();
    }, [projectId]);

    if (loading) return <p>Loading project parts...</p>;
    if (error) return <p style={{ color: 'red' }}>{error}</p>;
    if (!project) return <p>Project not found.</p>;

    return (
        <div>
            <h2>Parts for Project: {project.name}</h2>
            <p>
                <Link to={`/projects/${projectId}/dashboard`}>Back to Project Dashboard</Link> | 
                <Link to={`/create-part?projectId=${projectId}`}>Add New Part to this Project</Link>
            </p>

            {parts.length > 0 ? (
                <table>
                    <thead>
                        <tr>
                            <th>Number</th>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {parts.map(part => (
                            <tr key={part.id}>
                                <td>{part.number}</td>
                                <td>{part.name}</td>
                                <td>{part.status}</td>
                                <td>
                                    <Link to={`/parts/${part.id}`}>View</Link> | 
                                    <Link to={`/parts/${part.id}/edit`}>Edit</Link>
                                    {/* Delete button might be here or on the part details page */}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) : (
                <p>No parts found for this project yet.</p>
            )}
            {/* TODO: Add filtering options, pagination if list is long */}
        </div>
    );
}

export default ProjectDashboardParts;
