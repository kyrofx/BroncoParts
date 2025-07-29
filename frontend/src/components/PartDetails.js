import React, { useState, useEffect } from 'react';
import { useParams, Link as RouterLink, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../services/AuthContext';
import {
    Table, TableBody, TableCell, TableContainer, TableRow, Paper, Typography, Button, Box, Container, Breadcrumbs, Link as MuiLink
} from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext'; // Added NavigateNextIcon

// Helper function to fetch a part's details for breadcrumbs
const fetchPartForBreadcrumb = async (partId) => {
    if (!partId) return null;
    try {
        const response = await api.get(`/parts/${partId}`);
        // Ensure the response contains the part data directly or nested (e.g., response.data.part)
        // Assuming response.data.part contains { id, name, type, parent_id }
        return response.data.part || response.data;
    } catch (error) {
        console.error(`Error fetching part ${partId} for breadcrumb:`, error);
        return null;
    }
};

// Recursive function to build breadcrumb data
const buildBreadcrumbData = async (part, currentBreadcrumbs = []) => {
    if (!part) return currentBreadcrumbs;

    currentBreadcrumbs.unshift({
        name: part.name || `Part ${part.id}`,
        id: part.id,
        type: part.type, // Used to determine link path
        parent_id: part.parent_id
    });

    if (part.parent_id) {
        const parentPart = await fetchPartForBreadcrumb(part.parent_id);
        if (parentPart) {
            // Pass the fetched parent part, which should include its own parent_id
            return buildBreadcrumbData(parentPart, currentBreadcrumbs);
        }
    }
    return currentBreadcrumbs;
};


function PartDetails() {
    const { partId } = useParams();
    const [part, setPart] = useState(null);
    const [project, setProject] = useState(null);
    const [breadcrumbParts, setBreadcrumbParts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { user } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        const fetchDetails = async () => {
            try {
                setLoading(true);
                setError('');
                setProject(null);

                const response = await api.get(`/parts/${partId}`);
                const fetchedPart = response.data.part; // Assuming the part data is in response.data.part
                setPart(fetchedPart);

                if (fetchedPart) {
                    if (fetchedPart.project_id) {
                        try {
                            const projectResponse = await api.get(`/projects/${fetchedPart.project_id}`);
                            setProject(projectResponse.data.project);
                        } catch (projErr) {
                            console.error("Failed to fetch project details for part:", projErr);
                        }
                    }

                    // Build breadcrumbs
                    buildBreadcrumbData(fetchedPart)
                        .then(crumbs => setBreadcrumbParts(crumbs))
                        .catch(err => console.error("Error building breadcrumbs:", err));
                } else {
                    setError('Part not found.');
                }

            } catch (err) {
                // Use a more specific check for part not found, e.g., based on status code
                if (err.response && err.response.status === 404) {
                    setError('Part not found.');
                } else {
                    setError('Failed to fetch part details. ' + (err.response?.data?.message || err.message));
                }
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchDetails();
    }, [partId]);

    const handleDeletePart = async () => {
        if (window.confirm('Are you sure you want to delete this part?')) {
            try {
                await api.delete(`/parts/${partId}`);
                alert('Part deleted successfully');
                navigate('/parts');
            } catch (err) {
                setError('Failed to delete part. ' + (err.response?.data?.message || err.message));
                console.error(err);
            }
        }
    };

    if (loading) return <p>Loading part details...</p>;
    if (error) return <p sx={{ color: 'error.main' }}>{error}</p>;
    if (!part) return <p>Part not found.</p>;

    const canEdit = user?.permissions?.includes('admin') || user?.permissions?.includes('engineer');
    const canDelete = user?.permissions?.includes('admin');

    // Updated partDetailsArray to include new fields
    const partDetailsArray = [
        project && { label: 'Project', value: <RouterLink to={`/projects/${project.id}`}>{project.name}</RouterLink> },
        { label: 'Part Number', value: part?.part_number },
        { label: 'Name', value: part?.name }, // Added Name explicitly
        { label: 'Description', value: part?.description }, // This is for Airtable Notes
        { label: 'Type', value: part?.type },
        { label: 'Status', value: part?.status },
        part?.type === 'part' && { label: 'Quantity', value: part?.quantity },
        part?.type === 'part' && part?.machine && { label: 'Machine', value: part.machine.name },
        part?.type === 'part' && { label: 'Raw Material', value: part?.raw_material },
        part?.type === 'part' && part?.post_processes && part.post_processes.length > 0 && {
            label: 'Post Processes',
            value: part.post_processes.map(pp => pp.name).join(', ')
        },
        part?.subteam && { label: 'Subteam', value: <RouterLink to={`/assemblies/${part.subteam.id}`}>{part.subteam.name}</RouterLink> },
        part?.subsystem && { label: 'Subsystem', value: <RouterLink to={`/assemblies/${part.subsystem.id}`}>{part.subsystem.name}</RouterLink> },
        // { label: \'Notes\', value: part?.notes }, // part.description is used for Notes as per spec
    ].filter(Boolean); // Filter out any null/false entries (e.g. if part.type is not 'part')


    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}> {/* Changed maxWidth to lg */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h4" component="h1">
                    Part: {part?.name || part?.part_number} {/* Changed title format */}
                </Typography>
                {/* Edit and Delete buttons removed from here */}
            </Box>

            {breadcrumbParts.length > 0 && (
                <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb" sx={{ mb: 2 }}>
                    {breadcrumbParts.map((item, index) => {
                        const isLast = index === breadcrumbParts.length - 1;
                        const path = item.type && item.type.toLowerCase() === 'assembly' ? `/assemblies/${item.id}` : `/parts/${item.id}`;

                        if (isLast) {
                            return (
                                <Typography key={item.id} color="text.primary">
                                    {item.name}
                                </Typography>
                            );
                        }
                        return (
                            <MuiLink
                                component={RouterLink}
                                key={item.id}
                                to={path}
                                underline="hover"
                                color="inherit"
                            >
                                {item.name}
                            </MuiLink>
                        );
                    })}
                </Breadcrumbs>
            )}
            
            <TableContainer component={Paper} sx={{ mb: 2 }}>
                <Table aria-label="part details table" size="small"> {/* Added size="small" */}
                    <TableBody>
                        {partDetailsArray.map((detail) => (
                            <TableRow key={detail.label}>
                                <TableCell component="th" scope="row" sx={{ fontWeight: 'bold', padding: '6px 8px', fontSize: '0.875rem' }}> {/* Matched styles */}
                                    {detail.label}
                                </TableCell>
                                <TableCell sx={{ padding: '6px 8px', fontSize: '0.875rem' }}>{detail.value}</TableCell> {/* Matched styles */}
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* TODO: Add more fields as necessary, e.g., quantity, drawing_link, etc. */}

            {/* Edit and Delete Part buttons moved here from the header */}
            {(canEdit || canDelete) && (
                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-start' }}>
                    {canEdit && (
                        <Button component={RouterLink} to={`/parts/${partId}/edit`} variant="contained" color="primary" sx={{ mr: 1 }}>
                            Edit Part
                        </Button>
                    )}
                    {canDelete && (
                        <Button onClick={handleDeletePart} variant="contained" color="error">
                            Delete Part
                        </Button>
                    )}
                </Box>
            )}
            
            <Box sx={{ mt: 3 }}>
                {part.project_id && 
                    <Button component={RouterLink} to={`/projects/${part.project_id}`} variant="outlined">
                        Back to Project
                    </Button>
                }
            </Box>
        </Container>
    );
}

export default PartDetails;
