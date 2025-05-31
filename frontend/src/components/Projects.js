import React, { useState, useEffect } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom'; // Renamed Link to RouterLink, Added useNavigate
import api from '../services/api'; // We will create this next
import { Typography, Button, Box, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, CircularProgress, Alert, TableSortLabel } from '@mui/material'; // Import Material UI components

const Projects = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' }); // Added for sorting
  const navigate = useNavigate(); // Added useNavigate hook

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setLoading(true); // Set loading true at the start of fetch
        const response = await api.get('/projects');
        setProjects(response.data.projects);
        setError(null); // Clear any previous errors
      } catch (err) {
        setError(err.message || 'Failed to fetch projects');
        console.error(err); // Log error for debugging
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, []);

  const sortedProjects = React.useMemo(() => {
    // Ensure projects is always an array
    const safeProjects = Array.isArray(projects) ? projects : [];
    let sortableProjects = [...safeProjects];
    if (sortConfig && sortConfig.key !== null) {
      sortableProjects.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableProjects;
  }, [projects, sortConfig]);

  const handleSortRequest = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const handleRowClick = (projectId) => {
    navigate(`/projects/${projectId}`);
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error" sx={{ margin: 2 }}>{error}</Alert>;

  return (
    <Paper elevation={3} sx={{ padding: 3, marginTop: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
        <Typography variant="h4" component="h1">
          Projects
        </Typography>
        <Button component={RouterLink} to="/create-project" variant="contained" color="primary">
          Create New Project
        </Button>
      </Box>
      {projects.length === 0 ? (
        <Typography variant="body1" sx={{ marginTop: 2 }}>No projects found.</Typography>
      ) : (
        <TableContainer component={Paper} sx={{ marginTop: 2 }}>
          <Table sx={{ minWidth: 650 }} aria-label="projects table">
            <TableHead>
              <TableRow>
                <TableCell sx={{ padding: '4px 8px', fontSize: '0.875rem' }}>
                  <TableSortLabel
                    active={sortConfig.key === 'name'}
                    direction={sortConfig.key === 'name' ? sortConfig.direction : 'asc'}
                    onClick={() => handleSortRequest('name')}
                  >
                    Name
                  </TableSortLabel>
                </TableCell>
                <TableCell sx={{ padding: '4px 8px', fontSize: '0.875rem' }}>
                  <TableSortLabel
                    active={sortConfig.key === 'prefix'}
                    direction={sortConfig.key === 'prefix' ? sortConfig.direction : 'asc'}
                    onClick={() => handleSortRequest('prefix')}
                  >
                    Prefix
                  </TableSortLabel>
                </TableCell>
                <TableCell sx={{ padding: '4px 8px', fontSize: '0.875rem', width: '40%' }}>
                  <TableSortLabel
                    active={sortConfig.key === 'description'}
                    direction={sortConfig.key === 'description' ? sortConfig.direction : 'asc'}
                    onClick={() => handleSortRequest('description')}
                  >
                    Description
                  </TableSortLabel>
                </TableCell>
                <TableCell sx={{ padding: '4px 8px', fontSize: '0.875rem' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortedProjects.map(project => ( // Use sortedProjects here
                <TableRow
                  key={project.id}
                  hover // Added hover effect
                  onClick={() => handleRowClick(project.id)} // Added onClick handler
                  sx={{
                    '& td, & th': { padding: '4px 8px', fontSize: '0.875rem' }, // Adjusted padding
                    cursor: 'pointer' // Added cursor pointer
                  }}
                >
                  <TableCell component="th" scope="row">
                    {project.name}
                  </TableCell>
                  <TableCell>{project.prefix}</TableCell>
                  <TableCell>{project.description}</TableCell>
                  <TableCell>
                    <Button component={RouterLink} to={`/projects/${project.id}`} variant="outlined" size="small" sx={{ textTransform: 'none', fontSize: '0.875rem' }}>
                      View
                    </Button>
                    {/* Add Edit/Delete links later, protected by permissions */}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
};

export default Projects;
