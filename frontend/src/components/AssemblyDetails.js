import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link as RouterLink, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../services/AuthContext';
import {
    Container, Typography, Button, Box, Paper, CircularProgress, Alert,
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow, IconButton,
    Divider, Grid, TableSortLabel, Breadcrumbs
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';

// Helper function to fetch a part's details (used for parent assembly in breadcrumbs)
const fetchPartForBreadcrumb = async (partId) => {
    if (!partId) return null;
    try {
        const response = await api.get(`/parts/${partId}`);
        return response.data.part;
    } catch (error) {
        console.error(`Failed to fetch part ${partId} for breadcrumbs:`, error);
        return null;
    }
};

// Recursive function to build breadcrumb data
const buildBreadcrumbData = async (part, currentBreadcrumbs = []) => {
    if (!part) return currentBreadcrumbs;

    // Add current part to the beginning of the breadcrumbs list
    currentBreadcrumbs.unshift({ name: part.name, id: part.id, type: part.type });

    if (part.parent_id) {
        const parentPart = await fetchPartForBreadcrumb(part.parent_id);
        if (parentPart) {
            // Recursively call for the parent
            return buildBreadcrumbData(parentPart, currentBreadcrumbs);
        }
    }
    // Base case: no more parents, or parent fetch failed
    return currentBreadcrumbs;
};


function AssemblyDetails() {
    const { partId } = useParams(); // This is the ID of the current assembly
    const [assembly, setAssembly] = useState(null);
    const [project, setProject] = useState(null);
    const [containedParts, setContainedParts] = useState([]);
    const [breadcrumbParts, setBreadcrumbParts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { user } = useAuth();
    const navigate = useNavigate();
    const [sortConfig, setSortConfig] = useState({ key: 'part_number', direction: 'asc' });

    const handleContainedPartRowClick = (part) => {
        if (part.type === 'assembly') {
            navigate(`/assemblies/${part.id}`);
        } else {
            navigate(`/parts/${part.id}`);
        }
    };

    useEffect(() => {
        const fetchDetails = async () => {
            try {
                setLoading(true);
                setError('');

                const assemblyResponse = await api.get(`/parts/${partId}`);
                const currentAssembly = assemblyResponse.data.part;

                if (!currentAssembly) {
                    setError('Assembly not found.');
                    setLoading(false);
                    return;
                }
                // Ensure it's an assembly, or handle as a generic part if your design allows
                // For now, strictly checking type, adjust if assemblies are just parts with children
                if (currentAssembly.type !== 'assembly') {
                     // If it's not an assembly, maybe redirect to part details or show an error
                    // For now, setting it, but UI might need to adapt or show error.
                    // setError('This part is not an assembly. Displaying basic part info.');
                    // setAssembly(currentAssembly); // Or navigate(`/parts/${partId}`)
                    // For this component, we expect an assembly.
                     setError('The requested item is not an assembly.');
                     setAssembly(null); // Clear assembly if not correct type
                     setLoading(false);
                     return;
                }
                setAssembly(currentAssembly);

                if (currentAssembly.project_id) {
                    const projectResponse = await api.get(`/projects/${currentAssembly.project_id}`);
                    setProject(projectResponse.data.project);
                }

                const containedPartsResponse = await api.get(`/parts?parent_id=${partId}`);
                setContainedParts(containedPartsResponse.data.parts || []);

                const bData = await buildBreadcrumbData(currentAssembly); // currentAssembly is the starting point
                setBreadcrumbParts(bData);

            } catch (err) {
                setError('Failed to fetch assembly details. ' + (err.response?.data?.message || err.message));
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchDetails();
    }, [partId]);

    const sortedContainedParts = useMemo(() => {
        let sortable = [...containedParts];
        if (sortConfig.key) {
            sortable.sort((a, b) => {
                let aValue = a[sortConfig.key];
                let bValue = b[sortConfig.key];
                if (sortConfig.key === 'name') { // Changed from 'description'
                    aValue = a.name; // Directly use name
                    bValue = b.name; // Directly use name
                }

                if (aValue === null || aValue === undefined) aValue = '';
                if (bValue === null || bValue === undefined) bValue = '';

                if (typeof aValue === 'string' && typeof bValue === 'string') {
                    aValue = aValue.toLowerCase();
                    bValue = bValue.toLowerCase();
                }

                if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
                if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
                return 0;
            });
        }
        return sortable;
    }, [containedParts, sortConfig]);

    const handleSortRequest = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const handleDeleteAssembly = async () => {
        if (window.confirm('Are you sure you want to delete this assembly? This may also affect contained parts depending on backend setup.')) {
            try {
                await api.delete(`/parts/${partId}`);
                alert('Assembly deleted successfully.');
                if (assembly?.project_id) {
                    navigate(`/projects/${assembly.project_id}`);
                } else {
                    navigate('/projects'); 
                }
            } catch (err) {
                setError('Failed to delete assembly. ' + (err.response?.data?.message || err.message));
            }
        }
    };

    const handleDeleteContainedPart = async (partIdToDelete) => {
        if (window.confirm('Are you sure you want to delete this part?')) {
            try {
                await api.delete(`/parts/${partIdToDelete}`);
                setContainedParts(prev => prev.filter(p => p.id !== partIdToDelete));
            } catch (err) {
                setError('Failed to delete contained part. ' + (err.response?.data?.message || err.message));
            }
        }
    };

    const canManage = user?.permission === 'admin' || user?.permission === 'editor';

    if (loading) return <Container sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Container>;
    // Error specific to assembly not being found or not being an assembly type
    if (!assembly && error) return <Container sx={{ mt: 4 }}><Alert severity="error">{error}</Alert></Container>;
    if (!assembly) return <Container sx={{ mt: 4 }}><Alert severity="warning">Assembly data is not available.</Alert></Container>;
    // General error display if assembly is loaded but other errors occurred (e.g., delete error)
    const generalError = error && assembly ? error : null;


    const assemblyDetailsArray = [
        project && { label: 'Project', value: <RouterLink to={`/projects/${project.id}`}>{project.name}</RouterLink> },
        { label: 'Part Number', value: assembly.part_number },
        { label: 'Description', value: assembly.description || assembly.name },
        { label: 'Notes', value: assembly.notes },
    ].filter(Boolean);

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            {generalError && <Alert severity="error" sx={{ mb: 2 }}>{generalError}</Alert>}

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h4" component="h1">
                    Assembly: {assembly.name}
                </Typography>
                {canManage && (
                    <Box>
                        <Button
                            component={RouterLink}
                            to={`/create-part?projectId=${assembly.project_id}&type=part&parent_part_id=${assembly.id}`}
                            variant="contained" color="success" sx={{ mr: 1 }}
                        >
                            New Part
                        </Button>
                        <Button
                            component={RouterLink}
                            to={`/create-part?projectId=${assembly.project_id}&type=assembly&parent_part_id=${assembly.id}`}
                            variant="contained" color="success"
                        >
                            New Assembly
                        </Button>
                    </Box>
                )}
            </Box>

            <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb" sx={{ mb: 2 }}>
                {project && (
                    <RouterLink to={`/projects/${project.id}`} sx={{textDecoration: 'none', color: 'inherit'}}>
                        {project.name}
                    </RouterLink>
                )}
                {breadcrumbParts.map((bp, index) => (
                    index === breadcrumbParts.length - 1 ? (
                        <Typography key={bp.id} color="text.primary">{bp.name}</Typography>
                    ) : (
                        <RouterLink key={bp.id} to={bp.type === 'assembly' ? `/assemblies/${bp.id}` : `/parts/${bp.id}`} sx={{textDecoration: 'none', color: 'inherit'}}>
                            {bp.name}
                        </RouterLink>
                    )
                ))}
            </Breadcrumbs>

            <Typography variant="h6" component="h2" sx={{ mt: 3, mb: 1 }}>
                Parts & assemblies contained within this assembly:
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 4 }}>
                <Table sx={{ minWidth: 650 }} aria-label="contained parts table" size="small">
                    <TableHead>
                        <TableRow>
                            {['part_number', 'type', 'name'].map((headCellKey) => ( // Changed 'description' to 'name'
                                <TableCell key={headCellKey} sx={{ padding: '4px 8px', fontSize: '0.875rem', width: headCellKey === 'name' ? '40%' : undefined }}> {/* Adjusted padding */}
                                    <TableSortLabel
                                        active={sortConfig.key === headCellKey}
                                        direction={sortConfig.key === headCellKey ? sortConfig.direction : 'asc'}
                                        onClick={() => handleSortRequest(headCellKey)}
                                    >
                                        {headCellKey.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                    </TableSortLabel>
                                </TableCell>
                            ))}
                            <TableCell sx={{ padding: '4px 8px', fontSize: '0.875rem' }}>Action</TableCell>{/* Adjusted padding */}
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {sortedContainedParts.length > 0 ? sortedContainedParts.map((part) => (
                            <TableRow 
                                key={part.id} 
                                hover // Added hover effect
                                onClick={() => handleContainedPartRowClick(part)} // Added onClick handler
                                sx={{ 
                                    '& td, & th': { padding: '4px 8px', fontSize: '0.875rem' }, // Adjusted padding
                                    cursor: 'pointer' // Added cursor pointer
                                }}
                            >
                                <TableCell>
                                    {/* Keep button for explicit navigation if desired, or remove if row click is sufficient */}
                                    <Button component={RouterLink} to={part.type === 'assembly' ? `/assemblies/${part.id}` : `/parts/${part.id}`} color="primary" sx={{ padding: '0px 3px', textTransform: 'none', justifyContent: 'flex-start', fontSize: '0.875rem' }} onClick={(e) => e.stopPropagation()}>
                                        {part.part_number}
                                    </Button>
                                </TableCell>
                                <TableCell>{part.type === 'assembly' ? 'Assembly' : 'Part'}</TableCell> {/* Capitalized */}
                                <TableCell>{part.name}</TableCell> {/* Changed from part.description || part.name */}
                                <TableCell>
                                    {canManage && (
                                        <>
                                            <IconButton component={RouterLink} to={`/parts/${part.id}/edit`} size="small" color="primary" aria-label="edit part" sx={{ padding: '4px' }} onClick={(e) => e.stopPropagation()}>
                                                <EditIcon fontSize="small" />
                                            </IconButton>
                                            <IconButton onClick={(e) => {e.stopPropagation(); handleDeleteContainedPart(part.id);}} size="small" color="error" aria-label="delete part" sx={{ padding: '4px' }}>
                                                <DeleteIcon fontSize="small" />
                                            </IconButton>
                                        </>
                                    )}
                                </TableCell>
                            </TableRow>
                        )) : (
                            <TableRow>
                                <TableCell colSpan={4} align="center">No parts or assemblies found within this assembly.</TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

            <Typography variant="h6" component="h2" sx={{ mt: 4, mb: 1 }}>
                Assembly Details:
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 2 }}>
                <Table aria-label="assembly details table" size="small">
                    <TableBody>
                        {assemblyDetailsArray.map((detail) => (
                            <TableRow key={detail.label}>
                                <TableCell component="th" scope="row" sx={{ fontWeight: 'bold', padding: '6px 8px', fontSize: '0.875rem' }}>
                                    {detail.label}
                                </TableCell>
                                <TableCell sx={{ padding: '6px 8px', fontSize: '0.875rem' }}>{detail.value}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            {canManage && (
                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-start' }}>
                    <Button component={RouterLink} to={`/parts/${assembly.id}/edit`} variant="contained" color="primary" sx={{ mr: 1 }}>
                        Edit this assembly
                    </Button>
                    <Button onClick={handleDeleteAssembly} variant="contained" color="error">
                        Delete this assembly
                    </Button>
                </Box>
            )}
        </Container>
    );
}

export default AssemblyDetails;
