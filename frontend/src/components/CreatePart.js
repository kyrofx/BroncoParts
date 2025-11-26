import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../services/AuthContext';
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  Paper,
  Container,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  FormGroup,
  FormControlLabel,
  Checkbox,
} from '@mui/material';

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
        return (
            <Container maxWidth="md">
                <Typography sx={{ mt: 4 }}>You must be logged in to create parts.</Typography>
            </Container>
        );
    }

    return (
        <Container maxWidth="md">
            <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
                <Typography variant="h4" component="h2" gutterBottom>
                    Create New {partType === 'assembly' ? 'Assembly' : 'Part'}
                </Typography>
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                <Box component="form" onSubmit={handleSubmit}>
                    <TextField
                        fullWidth
                        label="Name"
                        id="partName"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                        margin="normal"
                    />
                    <TextField
                        fullWidth
                        label="Description"
                        id="partDescription"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        multiline
                        rows={3}
                        margin="normal"
                    />
                    <FormControl fullWidth margin="normal" required>
                        <InputLabel id="partTypeSelect-label">Type</InputLabel>
                        <Select
                            labelId="partTypeSelect-label"
                            id="partTypeSelect"
                            value={partType}
                            label="Type"
                            onChange={(e) => setPartType(e.target.value)}
                        >
                            <MenuItem value="part">Part</MenuItem>
                            <MenuItem value="assembly">Assembly</MenuItem>
                        </Select>
                    </FormControl>
                    <FormControl fullWidth margin="normal" required>
                        <InputLabel id="projectSelect-label">Project</InputLabel>
                        <Select
                            labelId="projectSelect-label"
                            id="projectSelect"
                            value={projectId}
                            label="Project"
                            onChange={(e) => setProjectId(e.target.value)}
                        >
                            <MenuItem value="">Select a Project</MenuItem>
                            {projects.map(project => (
                                <MenuItem key={project.id} value={project.id}>
                                    {project.name} (ID: {project.id})
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                    <FormControl fullWidth margin="normal" disabled={!projectId || parts.length === 0}>
                        <InputLabel id="parentPartSelect-label">Parent Assembly</InputLabel>
                        <Select
                            labelId="parentPartSelect-label"
                            id="parentPartSelect"
                            value={parentPartId}
                            label="Parent Assembly"
                            onChange={(e) => setParentPartId(e.target.value)}
                        >
                            <MenuItem value="">None</MenuItem>
                            {parts.map(part => (
                                <MenuItem key={part.id} value={part.id}>
                                    {part.name} (Part Number: {part.part_number})
                                </MenuItem>
                            ))}
                        </Select>
                        {!projectId && <FormHelperText>Select a project to see available parent assemblies.</FormHelperText>}
                        {projectId && parts.length === 0 && <FormHelperText>No assemblies available in the selected project to be a parent.</FormHelperText>}
                    </FormControl>

                    {partType === 'part' && (
                        <>
                            <TextField
                                fullWidth
                                label="Quantity"
                                type="number"
                                id="quantity"
                                value={quantity}
                                onChange={(e) => setQuantity(e.target.value)}
                                required
                                inputProps={{ min: 1 }}
                                margin="normal"
                            />

                            <FormControl fullWidth margin="normal" required>
                                <InputLabel id="machineSelect-label">Machine</InputLabel>
                                <Select
                                    labelId="machineSelect-label"
                                    id="machineSelect"
                                    value={machineId}
                                    label="Machine"
                                    onChange={(e) => setMachineId(e.target.value)}
                                >
                                    <MenuItem value="">Select a Machine</MenuItem>
                                    {machines.map(machine => (
                                        <MenuItem key={machine.id} value={machine.id}>
                                            {machine.name}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>

                            <TextField
                                fullWidth
                                label="Raw Material"
                                id="rawMaterial"
                                value={rawMaterial}
                                onChange={(e) => setRawMaterial(e.target.value)}
                                required
                                margin="normal"
                            />

                            <Box sx={{ mt: 2, mb: 2 }}>
                                <Typography variant="subtitle1" gutterBottom>Post Processes</Typography>
                                <Paper variant="outlined" sx={{ p: 2, maxHeight: 200, overflowY: 'auto' }}>
                                    {postProcesses.length === 0 ? (
                                        <Typography color="text.secondary">No post processes available</Typography>
                                    ) : (
                                        <FormGroup>
                                            {postProcesses.map(pp => (
                                                <FormControlLabel
                                                    key={pp.id}
                                                    control={
                                                        <Checkbox
                                                            id={`postProcess-${pp.id}`}
                                                            value={pp.id}
                                                            checked={postProcessIds.includes(pp.id.toString())}
                                                            onChange={handlePostProcessChange}
                                                        />
                                                    }
                                                    label={pp.name}
                                                />
                                            ))}
                                        </FormGroup>
                                    )}
                                </Paper>
                            </Box>

                            <FormControl fullWidth margin="normal" disabled={!projectId || projectAssemblies.length === 0}>
                                <InputLabel id="subteamSelect-label">Subteam</InputLabel>
                                <Select
                                    labelId="subteamSelect-label"
                                    id="subteamSelect"
                                    value={subteamId}
                                    label="Subteam"
                                    onChange={(e) => setSubteamId(e.target.value)}
                                >
                                    <MenuItem value="">Select Subteam (Optional)</MenuItem>
                                    {projectAssemblies.map(assembly => (
                                        <MenuItem key={assembly.id} value={assembly.id}>
                                            {assembly.name}
                                        </MenuItem>
                                    ))}
                                </Select>
                                {!projectId && <FormHelperText>Select a project to see available assemblies for Subteam.</FormHelperText>}
                                {projectId && projectAssemblies.length === 0 && <FormHelperText>No assemblies available in the selected project for Subteam.</FormHelperText>}
                            </FormControl>

                            <FormControl fullWidth margin="normal" disabled={!projectId || projectAssemblies.length === 0}>
                                <InputLabel id="subsystemSelect-label">Subsystem</InputLabel>
                                <Select
                                    labelId="subsystemSelect-label"
                                    id="subsystemSelect"
                                    value={subsystemId}
                                    label="Subsystem"
                                    onChange={(e) => setSubsystemId(e.target.value)}
                                >
                                    <MenuItem value="">Select Subsystem (Optional)</MenuItem>
                                    {projectAssemblies.map(assembly => (
                                        <MenuItem key={assembly.id} value={assembly.id}>
                                            {assembly.name}
                                        </MenuItem>
                                    ))}
                                </Select>
                                {!projectId && <FormHelperText>Select a project to see available assemblies for Subsystem.</FormHelperText>}
                                {projectId && projectAssemblies.length === 0 && <FormHelperText>No assemblies available in the selected project for Subsystem.</FormHelperText>}
                            </FormControl>
                        </>
                    )}

                    <Button
                        type="submit"
                        variant="contained"
                        color="primary"
                        disabled={isLoading}
                        sx={{ mt: 3 }}
                    >
                        {isLoading ? 'Creating...' : `Create ${partType === 'assembly' ? 'Assembly' : 'Part'}`}
                    </Button>
                </Box>
            </Paper>
        </Container>
    );
}

export default CreatePart;
