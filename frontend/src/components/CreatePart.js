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
    const [quantity, setQuantity] = useState(1); // New state for Quantity
    const [machineId, setMachineId] = useState(''); // New state for Machine
    const [subteamId, setSubteamId] = useState(''); // New state for Subteam
    const [subsystemId, setSubsystemId] = useState(''); // New state for Subsystem
    const [rawMaterial, setRawMaterial] = useState(''); // New state for Raw Material
    const [postProcessIds, setPostProcessIds] = useState([]); // New state for Post Processes (array of IDs)
    
    const [projects, setProjects] = useState([]);
    const [parts, setParts] = useState([]); // Assemblies for parent part selection
    const [machines, setMachines] = useState([]); // New state for machines list
    const [postProcesses, setPostProcesses] = useState([]); // New state for post processes list
    const [projectAssemblies, setProjectAssemblies] = useState([]); // New state for project assemblies (for Subteam/Subsystem)

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

                    // Fetch assemblies for Subteam/Subsystem dropdowns
                    const assembliesResponse = await api.get(`/projects/${projectId}/assemblies`);
                    setProjectAssemblies(assembliesResponse.data.assemblies || []);

                } catch (err) {
                    setError('Failed to fetch parts or assemblies for project.');
                    console.error(err);
                }
            } else {
                setParts([]);
                setProjectAssemblies([]);
            }
        };
        fetchPartsForProject();
    }, [projectId]);

    // New useEffect to fetch machines
    useEffect(() => {
        const fetchMachines = async () => {
            try {
                const response = await api.get('/machines');
                setMachines(response.data.machines || []);
            } catch (err) {
                setError('Failed to fetch machines.');
                console.error(err);
            }
        };
        fetchMachines();
    }, []);

    // New useEffect to fetch post processes
    useEffect(() => {
        const fetchPostProcesses = async () => {
            try {
                const response = await api.get('/post-processes');
                setPostProcesses(response.data.post_processes || []);
            } catch (err) {
                setError('Failed to fetch post processes.');
                console.error(err);
            }
        };
        fetchPostProcesses();
    }, []);

    // useEffect to fetch derived hierarchy info when parentPartId changes
    useEffect(() => {
        const fetchDerivedHierarchy = async () => {
            if (parentPartId && projectId) { // Ensure projectId is also available
                try {
                    const response = await api.get(`/parts/derived-hierarchy-info?parent_assembly_id=${parentPartId}`);
                    const { derived_subteam_id, derived_subsystem_id } = response.data;
                    if (derived_subteam_id) {
                        setSubteamId(derived_subteam_id.toString());
                    } else {
                        setSubteamId(''); // Clear if not derived
                    }
                    if (derived_subsystem_id) {
                        setSubsystemId(derived_subsystem_id.toString());
                    } else {
                        setSubsystemId(''); // Clear if not derived
                    }
                } catch (err) {
                    console.error("Failed to fetch derived hierarchy info:", err);
                    // Optionally set an error message for the user
                    // setError(\'Could not auto-derive Subteam/Subsystem.\');
                    // Clear them if fetching fails to avoid stale data
                    setSubteamId('');
                    setSubsystemId('');
                }
            } else {
                // Clear subteam and subsystem if no parent is selected
                setSubteamId('');
                setSubsystemId('');
            }
        };

        fetchDerivedHierarchy();
    }, [parentPartId, projectId]); // Add projectId as a dependency

    const handlePostProcessChange = (e) => {
        const { value, checked } = e.target;
        setPostProcessIds(prevIds => {
            if (checked) {
                // Add the ID if checked and not already in the array
                return prevIds.includes(value) ? prevIds : [...prevIds, value];
            } else {
                // Remove the ID if unchecked
                return prevIds.filter(id => id !== value);
            }
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        if (!name || !projectId || (partType === 'part' && (!quantity || !machineId || !rawMaterial))) {
            setError('Part name, project, quantity, machine, and raw material are required for parts.');
            setIsLoading(false);
            return;
        }
        if (partType === 'assembly' && !name || !projectId) {
             setError('Assembly name and project are required.');
            setIsLoading(false);
            return;
        }


        const partData = {
            name,
            description,
            project_id: parseInt(projectId),
            parent_id: parentPartId ? parseInt(parentPartId) : null,
            type: partType,
        };

        if (partType === 'part') {
            partData.quantity = parseInt(quantity);
            partData.machine_id = machineId ? parseInt(machineId) : null;
            partData.raw_material = rawMaterial;
            partData.post_process_ids = postProcessIds.map(id => parseInt(id));
            if (subteamId) partData.subteam_id = parseInt(subteamId);
            if (subsystemId) partData.subsystem_id = parseInt(subsystemId);
        }

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
            <h2>Create New {partType === 'assembly' ? 'Assembly' : 'Part'}</h2>
            {error && <div className="alert alert-danger">{error}</div>}
            <form onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label htmlFor="partName" className="form-label">Name</label>
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
                        <option value="part">Part</option>
                        <option value="assembly">Assembly</option>
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
                    <label htmlFor="parentPartSelect" className="form-label">Parent Assembly</label>
                    <select
                        className="form-select"
                        id="parentPartSelect"
                        value={parentPartId}
                        onChange={(e) => {
                            setParentPartId(e.target.value);
                            // Clearing subteam/subsystem here is one approach, 
                            // but the useEffect above will handle it based on new parentPartId
                        }}
                        disabled={!projectId || parts.length === 0}
                    >
                        <option value="">None</option>
                        {parts.map(part => (
                            <option key={part.id} value={part.id}>
                                {part.name} (Part Number: {part.part_number})
                            </option>
                        ))}
                    </select>
                    {!projectId && <small className="form-text text-muted">Select a project to see available parent assemblies.</small>}
                    {projectId && parts.length === 0 && <small className="form-text text-muted">No assemblies available in the selected project to be a parent.</small>}
                </div>

                {/* New fields only for type 'part' */}
                {partType === 'part' && (
                    <>
                        <div className="mb-3">
                            <label htmlFor="quantity" className="form-label">Quantity</label>
                            <input
                                type="number"
                                className="form-control"
                                id="quantity"
                                value={quantity}
                                onChange={(e) => setQuantity(e.target.value)}
                                required
                                min="1"
                            />
                        </div>

                        <div className="mb-3">
                            <label htmlFor="machineSelect" className="form-label">Machine</label>
                            <select
                                className="form-select"
                                id="machineSelect"
                                value={machineId}
                                onChange={(e) => setMachineId(e.target.value)}
                                required
                            >
                                <option value="">Select a Machine</option>
                                {machines.map(machine => (
                                    <option key={machine.id} value={machine.id}>
                                        {machine.name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="mb-3">
                            <label htmlFor="rawMaterial" className="form-label">Raw Material</label>
                            <input
                                type="text"
                                className="form-control"
                                id="rawMaterial"
                                value={rawMaterial}
                                onChange={(e) => setRawMaterial(e.target.value)}
                                required
                            />
                        </div>

                        <div className="mb-3">
                            <label className="form-label">Post Processes</label>
                            <div className="border rounded p-3" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                                {postProcesses.length === 0 ? (
                                    <div className="text-muted">No post processes available</div>
                                ) : (
                                    postProcesses.map(pp => (
                                        <div key={pp.id} className="form-check">
                                            <input
                                                className="form-check-input"
                                                type="checkbox"
                                                id={`postProcess-${pp.id}`}
                                                value={pp.id}
                                                checked={postProcessIds.includes(pp.id.toString())}
                                                onChange={handlePostProcessChange}
                                            />
                                            <label className="form-check-label" htmlFor={`postProcess-${pp.id}`}>
                                                {pp.name}
                                            </label>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                        
                        <div className="mb-3">
                            <label htmlFor="subteamSelect" className="form-label">Subteam</label>
                            <select
                                className="form-select"
                                id="subteamSelect"
                                value={subteamId}
                                onChange={(e) => setSubteamId(e.target.value)}
                                disabled={!projectId || projectAssemblies.length === 0}
                            >
                                <option value="">Select Subteam (Optional)</option>
                                {projectAssemblies.map(assembly => (
                                    <option key={assembly.id} value={assembly.id}>
                                        {assembly.name}
                                    </option>
                                ))}
                            </select>
                             {!projectId && <small className="form-text text-muted">Select a project to see available assemblies for Subteam.</small>}
                             {projectId && projectAssemblies.length === 0 && <small className="form-text text-muted">No assemblies available in the selected project for Subteam.</small>}
                        </div>

                        <div className="mb-3">
                            <label htmlFor="subsystemSelect" className="form-label">Subsystem</label>
                            <select
                                className="form-select"
                                id="subsystemSelect"
                                value={subsystemId}
                                onChange={(e) => setSubsystemId(e.target.value)}
                                disabled={!projectId || projectAssemblies.length === 0}
                            >
                                <option value="">Select Subsystem (Optional)</option>
                                {projectAssemblies.map(assembly => (
                                    <option key={assembly.id} value={assembly.id}>
                                        {assembly.name}
                                    </option>
                                ))}
                            </select>
                            {!projectId && <small className="form-text text-muted">Select a project to see available assemblies for Subsystem.</small>}
                            {projectId && projectAssemblies.length === 0 && <small className="form-text text-muted">No assemblies available in the selected project for Subsystem.</small>}
                        </div>
                    </>
                )}
                {/* ... end of new fields ... */}

                <button type="submit" className="btn btn-primary" disabled={isLoading}>
                    {isLoading ? 'Creating...' : `Create ${partType === 'assembly' ? 'Assembly' : 'Part'}`}
                </button>
            </form>
        </div>
    );
}

export default CreatePart;
