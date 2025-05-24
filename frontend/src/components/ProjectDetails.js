import React, { useState, useEffect, useMemo } from 'react'; // Added useMemo
import { useParams, Link as RouterLink, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../services/AuthContext';
import { Container, Typography, Button, Box, Paper, CircularProgress, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, IconButton, Divider, Grid, TableSortLabel } from '@mui/material'; // Added TableSortLabel
import { alpha } from '@mui/material/styles'; // Import alpha for hover effect
import EditIcon from '@mui/icons-material/Edit'; // Added
import DeleteIcon from '@mui/icons-material/Delete'; // Added

function ProjectDetails() {
    const { projectId } = useParams();
    const [project, setProject] = useState(null);
    const [parts, setParts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { user } = useAuth();
    const navigate = useNavigate();
    const [sortConfig, setSortConfig] = useState({ key: 'part_number', direction: 'asc' });

    const handlePartRowClick = (part) => {
        if (part.type === 'assembly') {
            navigate(`/assemblies/${part.id}`);
        } else {
            navigate(`/parts/${part.id}`);
        }
    };

    const handleDeletePart = async (partIdToDelete) => {
        if (window.confirm('Are you sure you want to delete this part?')) {
            try {
                await api.delete(`/parts/${partIdToDelete}`);
                setParts(prevParts => prevParts.filter(p => p.id !== partIdToDelete));
                // Optionally, show a success message e.g., alert('Part deleted successfully');
            } catch (err) {
                setError('Failed to delete part. ' + (err.response?.data?.message || err.message));
                console.error(err);
            }
        }
    };

    const handleDeleteProject = async () => {
        if (window.confirm('Are you sure you want to delete this project and all its associated parts?')) {
            try {
                await api.delete(`/projects/${projectId}`);
                navigate('/projects'); // Navigate to projects list after deletion
            } catch (err) {
                setError('Failed to delete project. ' + (err.response?.data?.message || err.message));
                console.error(err);
            }
        }
    };

    useEffect(() => {
        const fetchProjectDetails = async () => {
            try {
                setLoading(true);
                const projectResponse = await api.get(`/projects/${projectId}`);
                setProject(projectResponse.data.project);

                const partsResponse = await api.get(`/projects/${projectId}/parts`);
                setParts(partsResponse.data.parts);

                setError('');
            } catch (err) {
                setError('Failed to fetch project details. ' + (err.response?.data?.message || err.message));
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchProjectDetails();
    }, [projectId]);

    const sortedParts = useMemo(() => {
        let sortableParts = [...parts];
        if (sortConfig.key !== null) {
            sortableParts.sort((a, b) => {
                let aValue = a[sortConfig.key];
                let bValue = b[sortConfig.key];

                // Handle cases like name which might use name as fallback (previously description)
                if (sortConfig.key === 'name') { // Changed from 'description'
                    aValue = a.name; // Directly use name
                    bValue = b.name; // Directly use name
                }
                // Handle parent assembly name sorting
                if (sortConfig.key === 'parent') {
                    const parentA = a.parent_id ? parts.find(p => p.id === a.parent_id) : null;
                    const parentB = b.parent_id ? parts.find(p => p.id === b.parent_id) : null;
                    aValue = parentA ? parentA.name : '';
                    bValue = parentB ? parentB.name : '';
                }

                if (aValue === null || aValue === undefined) aValue = ''; // Treat null/undefined as empty string for sorting
                if (bValue === null || bValue === undefined) bValue = '';

                if (typeof aValue === 'string' && typeof bValue === 'string') {
                    aValue = aValue.toLowerCase();
                    bValue = bValue.toLowerCase();
                }

                if (aValue < bValue) {
                    return sortConfig.direction === 'asc' ? -1 : 1;
                }
                if (aValue > bValue) {
                    return sortConfig.direction === 'asc' ? 1 : -1;
                }
                return 0;
            });
        }
        return sortableParts;
    }, [parts, sortConfig]);

    const handleSortRequest = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}><CircularProgress /></Box>;
    if (error && !project) return <Alert severity="error" sx={{ margin: 2 }}>{error}</Alert>; // Show general error if project couldn't be loaded
    if (!project) return <Alert severity="warning" sx={{ margin: 2 }}>Project not found.</Alert>;

    // Permissions for creating/editing parts
    const canManageParts = user?.permission === 'admin' || user?.permission === 'editor';

    return (
        <Container maxWidth="lg" sx={{ marginTop: 4, marginBottom: 4 }}>
            {error && project && <Alert severity="error" sx={{ margin: 2, marginBottom: 2 }}>{error}</Alert>} {/* Show error that might occur after project load, e.g., part deletion error */}
            <Paper elevation={3} sx={{ padding: 3, marginBottom: 4 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                    <Typography variant="h4" component="h1">
                        {project.name} - All Parts & Assemblies
                    </Typography>
                    <Box> 
                        {canManageParts && (
                            <> 
                                <Button component={RouterLink} to={`/create-part?projectId=${project.id}&type=part`} variant="contained" color="success" sx={{ marginRight: 1 }}>
                                    New Part
                                </Button>
                                <Button component={RouterLink} to={`/create-part?projectId=${project.id}&type=assembly`} variant="contained" color="success">
                                    New Assembly
                                </Button>
                            </>
                        )}
                    </Box>
                </Box>
            </Paper>

            <Paper elevation={3} sx={{ padding: 3, marginTop: 4 }}>
                <Typography variant="h5" component="h2" gutterBottom>
                    Parts in this Project
                </Typography>
                {parts.length > 0 ? (
                    <TableContainer component={Paper} sx={{ marginTop: 2 }}>
                        <Table sx={{ minWidth: 650 }} aria-label="parts table">
                            <TableHead>
                                <TableRow>
                                    <TableCell sx={{ padding: '4px 8px', fontSize: '0.875rem' }}>
                                        <TableSortLabel
                                            active={sortConfig.key === 'part_number'}
                                            direction={sortConfig.key === 'part_number' ? sortConfig.direction : 'asc'}
                                            onClick={() => handleSortRequest('part_number')}
                                        >
                                            Part Number
                                        </TableSortLabel>
                                    </TableCell>
                                    <TableCell sx={{ padding: '4px 8px', fontSize: '0.875rem' }}>
                                        <TableSortLabel
                                            active={sortConfig.key === 'type'}
                                            direction={sortConfig.key === 'type' ? sortConfig.direction : 'asc'}
                                            onClick={() => handleSortRequest('type')}
                                        >
                                            Type
                                        </TableSortLabel>
                                    </TableCell>
                                    <TableCell sx={{ padding: '4px 8px', fontSize: '0.875rem', width: '40%' }}>
                                        <TableSortLabel
                                            active={sortConfig.key === 'name'} // Changed from 'description'
                                            direction={sortConfig.key === 'name' ? sortConfig.direction : 'asc'} // Changed from 'description'
                                            onClick={() => handleSortRequest('name')} // Changed from 'description'
                                        >
                                            Name 
                                        </TableSortLabel>
                                    </TableCell>
                                    <TableCell sx={{ padding: '4px 8px', fontSize: '0.875rem' }}>
                                        <TableSortLabel
                                            active={sortConfig.key === 'parent'}
                                            direction={sortConfig.key === 'parent' ? sortConfig.direction : 'asc'}
                                            onClick={() => handleSortRequest('parent')}
                                        >
                                            Parent
                                        </TableSortLabel>
                                    </TableCell>
                                    <TableCell sx={{ padding: '4px 8px', fontSize: '0.875rem' }}>Action</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {sortedParts.map(part => { // Use sortedParts here
                                    const parentAssembly = part.parent_id
                                        ? parts.find(p => p.id === part.parent_id) // Keep original parts lookup for parent name display
                                        : null;
                                    return (
                                        <TableRow 
                                            key={part.id} 
                                            hover // Added hover effect
                                            onClick={() => handlePartRowClick(part)} // Added onClick handler
                                            sx={{
                                                '& td, & th': { padding: '4px 8px', fontSize: '0.875rem' }, // Adjusted padding
                                                cursor: 'pointer' // Added cursor pointer
                                            }}
                                        >
                                            <TableCell>
                                                {/* Keep button for explicit navigation if desired, or remove if row click is sufficient */}
                                                <Button component={RouterLink} to={part.type === 'assembly' ? `/assemblies/${part.id}` : `/parts/${part.id}`} color="primary" sx={{ padding: '0px 3px', textTransform: 'none', justifyContent: 'flex-start', fontSize: '0.875rem' }} onClick={(e) => e.stopPropagation()}>{part.part_number}</Button>
                                            </TableCell>
                                            <TableCell>{part.type === 'assembly' ? 'Assembly' : 'Part'}</TableCell> {/* Capitalized */}
                                            <TableCell>{part.name}</TableCell> {/* Changed from part.description || part.name */}
                                            <TableCell>
                                                {parentAssembly ? (
                                                    <Button component={RouterLink} to={`/assemblies/${parentAssembly.id}`} color="primary" sx={{ padding: '0px 3px', textTransform: 'none', justifyContent: 'flex-start', fontSize: '0.875rem' }} onClick={(e) => e.stopPropagation()}>
                                                        {parentAssembly.name}
                                                    </Button>
                                                ) : ''}
                                            </TableCell>
                                            <TableCell>
                                                {canManageParts && (
                                                    <>
                                                        <IconButton component={RouterLink} to={part.type === 'assembly' ? `/parts/${part.id}/edit` : `/parts/${part.id}/edit`} size="small" color="primary" aria-label="edit part" sx={{ padding: '4px'}} onClick={(e) => e.stopPropagation()}>
                                                            <EditIcon fontSize="small" />
                                                        </IconButton>
                                                        <IconButton onClick={(e) => { e.stopPropagation(); handleDeletePart(part.id);}} size="small" color="error" aria-label="delete part" sx={{ padding: '4px', '&:hover': { backgroundColor: (theme) => alpha(theme.palette.error.main, theme.palette.action.hoverOpacity)} }}>
                                                            <DeleteIcon fontSize="small" />
                                                        </IconButton>
                                                    </>
                                                )}
                                            </TableCell>
                                        </TableRow>
                                    );
                                })}
                            </TableBody>
                        </Table>
                    </TableContainer>
                ) : (
                    <TableRow>
                        <TableCell colSpan={5} align="center">No parts found for this project.</TableCell>{/* Adjusted colSpan */}
                    </TableRow>
                )}
            </Paper>

            <Divider sx={{ my: 3 }} />

            <Box sx={{ mt: 2 }}>
                <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} md={6}>
                        {project.part_number_prefix && (
                            <Typography variant="body1">
                                <strong>Project Prefix:</strong> {project.part_number_prefix}
                            </Typography>
                        )}
                    </Grid>
                    <Grid item xs={12} md={6} sx={{ display: 'flex', justifyContent: { xs: 'flex-start', md: 'flex-end' }, mt: { xs: 2, md: 0 } }}>
                        <Button component={RouterLink} to={`/projects/${projectId}/tree`} variant="outlined" sx={{ mr: 1 }}>
                            View Tree
                        </Button>
                        <Button
                            variant="outlined"
                            color="primary"
                            component={RouterLink}
                            to={`/projects/${projectId}/edit`} // Changed from project.id to projectId
                            sx={{ mr: 1 }}
                        >
                            Edit Project
                        </Button>
                        <Button
                            variant="outlined"
                            color="error"
                            onClick={handleDeleteProject}
                            sx={{
                                '&:hover': {
                                    backgroundColor: (theme) => alpha(theme.palette.error.main, theme.palette.action.hoverOpacity),
                                    borderColor: (theme) => theme.palette.error.dark, // Optional: darken border slightly
                                }
                            }}
                        >
                            Delete Project
                        </Button>
                    </Grid>
                </Grid>
            </Box>
        </Container>
    );
}

export default ProjectDetails;
