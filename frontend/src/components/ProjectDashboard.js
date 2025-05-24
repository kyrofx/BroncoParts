import React, { useState, useEffect } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom'; // Changed Link to RouterLink
import api from '../services/api';
import { Typography, Button, Box, Paper, CircularProgress, Alert, Grid, Card, CardContent, Container } from '@mui/material'; // Material UI components

// TODO: Fetch actual project-specific dashboard data, including stats

function ProjectDashboard() {
    const { projectId } = useParams();
    const [project, setProject] = useState(null);
    const [projectStats, setProjectStats] = useState({ // Placeholder for stats
        totalParts: 0,
        assembliesCount: 0,
        partsPendingReview: 0,
        // Add more relevant stats as needed
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchProjectDashboardData = async () => {
            try {
                setLoading(true);
                const projectRes = await api.get(`/projects/${projectId}`);
                setProject(projectRes.data.project); // Assuming API returns { project: {...} }

                // TODO: Fetch actual stats for this project
                // Example: const statsRes = await api.get(`/projects/${projectId}/dashboard-stats`);
                // setProjectStats(statsRes.data);
                // For now, using placeholder or data from project object if available
                setProjectStats({
                    totalParts: projectRes.data.project?.parts_count || 0,
                    assembliesCount: projectRes.data.project?.assemblies_count || 0, // Assuming this might exist
                    partsPendingReview: 0, // Placeholder
                });

                setError('');
            } catch (err) {
                setError('Failed to load project dashboard data. ' + (err.response?.data?.message || err.message));
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchProjectDashboardData();
    }, [projectId]);

    if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 'calc(100vh - 64px)' }}><CircularProgress /></Box>;
    if (error) return <Alert severity="error" sx={{ margin: 2 }}>{error}</Alert>;
    if (!project) return <Alert severity="info" sx={{ margin: 2 }}>Project not found.</Alert>;

    return (
        <Container maxWidth="lg" sx={{ marginTop: 4, marginBottom: 4 }}>
            <Paper elevation={3} sx={{ padding: 3, marginBottom: 4 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                    <Typography variant="h4" component="h1">
                        Dashboard: {project.name}
                    </Typography>
                    <Button component={RouterLink} to={`/projects/${projectId}`} variant="outlined">
                        Back to Project Details
                    </Button>
                </Box>
            </Paper>

            <Grid container spacing={3} sx={{ marginBottom: 4 }}>
                {/* Stats Cards */}
                <Grid item xs={12} sm={6} md={4}>
                    <Card>
                        <CardContent sx={{ textAlign: 'center' }}>
                            <Typography variant="h5" component="div">
                                {projectStats.totalParts}
                            </Typography>
                            <Typography sx={{ mb: 1.5 }} color="text.secondary">
                                Total Parts
                            </Typography>
                            <Button component={RouterLink} to={`/projects/${projectId}`} size="small">View All Parts</Button>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                    <Card>
                        <CardContent sx={{ textAlign: 'center' }}>
                            <Typography variant="h5" component="div">
                                {projectStats.assembliesCount}
                            </Typography>
                            <Typography sx={{ mb: 1.5 }} color="text.secondary">
                                Assemblies
                            </Typography>
                            {/* Link to a filtered view of assemblies if possible */}
                            <Button component={RouterLink} to={`/projects/${projectId}?type=assembly`} size="small">View Assemblies</Button>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                    <Card>
                        <CardContent sx={{ textAlign: 'center' }}>
                            <Typography variant="h5" component="div">
                                {projectStats.partsPendingReview}
                            </Typography>
                            <Typography sx={{ mb: 1.5 }} color="text.secondary">
                                Parts Pending Review
                            </Typography>
                            {/* Link to a filtered list of these parts */}
                            <Button size="small" disabled>View Pending</Button>
                        </CardContent>
                    </Card>
                </Grid>
                {/* Add more stats cards as needed */}
            </Grid>

            <Paper elevation={3} sx={{ padding: 3, marginTop: 2 }}>
                <Typography variant="h5" component="h2" gutterBottom>
                    Project Actions
                </Typography>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={4}>
                        <Button fullWidth component={RouterLink} to={`/create-part?projectId=${projectId}&type=part`} variant="contained" color="success">
                            Add New Part
                        </Button>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                        <Button fullWidth component={RouterLink} to={`/create-part?projectId=${projectId}&type=assembly`} variant="contained" color="success">
                            Add New Assembly
                        </Button>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                        <Button fullWidth component={RouterLink} to={`/projects/${project.id}/edit`} variant="outlined" color="primary">
                            Edit Project Details
                        </Button>
                    </Grid>
                     <Grid item xs={12} sm={6} md={4}>
                        <Button fullWidth component={RouterLink} to={`/projects/${projectId}/tree`} variant="outlined">
                            View Tree Structure
                        </Button>
                    </Grid>
                    {/* Add other relevant actions */}
                </Grid>
            </Paper>
            
            {/* TODO: Display more project-specific info, charts, recent activity within the project etc. */}
        </Container>
    );
}

export default ProjectDashboard;
