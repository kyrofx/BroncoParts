import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom'; // Added useLocation
import api from '../services/api';
import { useAuth } from '../services/AuthContext'; // Changed import

function CreatePart() {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [projectId, setProjectId] = useState('');
    const [parentPartId, setParentPartId] = useState('');
    const [partType, setPartType] = useState('part'); // Added partType state, default to 'part'
    const [projects, setProjects] = useState([]);
    const [parts, setParts] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const location = useLocation(); // Added location
    const { user } = useAuth(); // Changed to useAuth hook

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const type = params.get('type');
        const projId = params.get('projectId');
        const parentIdParam = params.get('parent_part_id'); // Read parent_part_id
        if (type) {
            setPartType(type);
        }
        if (projId) {
            setProjectId(projId);
        }
        if (parentIdParam) { // If parent_part_id is in URL
            setParentPartId(parentIdParam); // Set it
        }
    }, [location.search]);

    useEffect(() => {
        const fetchProjects = async () => {
            try {
                const response = await api.get('/projects');
                const fetchedProjects = response.data.projects; // Assuming response.data.projects is the array
                setProjects(fetchedProjects || []);

                // Check URL parameters to determine if a projectId is already specified
                const currentParams = new URLSearchParams(location.search);
                const projIdFromUrl = currentParams.get('projectId');

                // Only set a default project if no projectId is specified in the URL
                // and if projects were successfully fetched and are available.
                if (!projIdFromUrl && fetchedProjects && fetchedProjects.length > 0) {
                    setProjectId(fetchedProjects[0].id.toString()); // Default to first project's ID, ensure it's a string
                }
                // If projIdFromUrl is present, the other useEffect (or this one on a subsequent run if combined)
                // will have already set it, or will set it based on the URL.
            } catch (err) {
                setError('Failed to fetch projects.');
                console.error(err); // Log the error object for better debugging
            }
        };
        fetchProjects();
    }, [location.search]); // Changed dependency array from [] to [location.search]

    useEffect(() => {
        const fetchPartsForProject = async () => {
            if (projectId) {
                try {
                    const response = await api.get(`/parts?project_id=${projectId}`);
                    // Filter for parts that are assemblies AND strictly belong to the selected project
                    const projectSpecificAssemblies = response.data.parts.filter(
                        part => part.type === 'assembly' && part.project_id.toString() === projectId
                    );
                    setParts(projectSpecificAssemblies);
                } catch (err) {
                    setError('Failed to fetch parts for project.');
                    console.error(err);
                }
            } else {
                setParts([]);
            }
        };
        fetchPartsForProject();
    }, [projectId]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        if (!name || !projectId) {
            setError('Part name and project are required.');
            setIsLoading(false);
            return;
        }

        const partData = {
            name,
            description,
            project_id: parseInt(projectId),
            parent_id: parentPartId ? parseInt(parentPartId) : null,
            type: partType, // Added type to partData
        };

        try {
            await api.post('/parts', partData);
            if (parentPartId) {
                navigate(`/assemblies/${parentPartId}`); // Redirect to the parent part's detail page
            } else {
                navigate(`/projects/${projectId}`); // Redirect to the project details page
            }
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to create part. Please try again.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    if (!user) {
        return <p>You must be logged in to create parts.</p>;
    }

    return (
        <div className="container mt-4">
            <h2>Create New {partType === 'assembly' ? 'Assembly' : 'Part'}</h2> {/* Dynamically set title */}
            {error && <div className="alert alert-danger">{error}</div>}
            <form onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label htmlFor="partName" className="form-label">Part Name</label>
                    <input
                        type="text"
                        className="form-control"
                        id="partName"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="partDescription" className="form-label">Description</label>
                    <textarea
                        className="form-control"
                        id="partDescription"
                        rows="3"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                    ></textarea>
                </div>
                <div className="mb-3">
                    <label htmlFor="partTypeSelect" className="form-label">Type</label>
                    <select
                        className="form-select"
                        id="partTypeSelect"
                        value={partType}
                        onChange={(e) => setPartType(e.target.value)}
                        required
                    >
                        <option value="part">Part</option> {/* Capitalized */}
                        <option value="assembly">Assembly</option> {/* Capitalized */}
                    </select>
                </div>
                <div className="mb-3">
                    <label htmlFor="projectSelect" className="form-label">Project</label>
                    <select
                        className="form-select"
                        id="projectSelect"
                        value={projectId}
                        onChange={(e) => setProjectId(e.target.value)}
                        required
                    >
                        <option value="">Select a Project</option>
                        {projects.map(project => (
                            <option key={project.id} value={project.id}>
                                {project.name} (ID: {project.id})
                            </option>
                        ))}
                    </select>
                </div>
                <div className="mb-3">
                    <label htmlFor="parentPartSelect" className="form-label">Parent Assembly (Optional)</label>
                    <select
                        className="form-select"
                        id="parentPartSelect"
                        value={parentPartId}
                        onChange={(e) => setParentPartId(e.target.value)}
                        disabled={!projectId || parts.length === 0}
                    >
                        <option value="">None</option>
                        {parts.map(part => ( // Now 'parts' only contains assemblies
                            <option key={part.id} value={part.id}>
                                {part.name} (Part Number: {part.part_number})
                            </option>
                        ))}
                    </select>
                    {!projectId && <small className="form-text text-muted">Select a project to see available parent parts.</small>}
                    {projectId && parts.length === 0 && <small className="form-text text-muted">No assemblies available in the selected project to be a parent.</small>}
                </div>
                <button type="submit" className="btn btn-primary" disabled={isLoading}>
                    {isLoading ? 'Creating...' : `Create ${partType === 'assembly' ? 'Assembly' : 'Part'}`}{/* Dynamically set button text */}
                </button>
            </form>
        </div>
    );
}

export default CreatePart;
