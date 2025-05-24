import React, { useState, useEffect, useMemo } from 'react'; // Added useMemo
import { Link as RouterLink } from 'react-router-dom'; // Renamed Link to RouterLink
import api from '../services/api'; // We will create this next
import { Typography, Button, Box, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, CircularProgress, Alert, TableSortLabel, IconButton } from '@mui/material'; // Import Material UI components
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { useAuth } from '../services/AuthContext'; // Assuming AuthContext provides user info for permissions

const Parts = () => {
  const [parts, setParts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'part_number', direction: 'asc' });
  const { user } = useAuth(); // Get user for permission checks

  useEffect(() => {
    const fetchParts = async () => {
      try {
        const response = await api.get('/parts');
        setParts(response.data.parts);
        setLoading(false);
      } catch (err) {
        setError(err.message || 'Failed to fetch parts');
        setLoading(false);
      }
    };
    fetchParts();
  }, []);

  const sortedParts = useMemo(() => {
    let sortableParts = [...parts];
    if (sortConfig.key !== null) {
      sortableParts.sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];

        if (sortConfig.key === 'description') {
            aValue = a.description || a.name;
            bValue = b.description || b.name;
        }

        if (aValue === null || aValue === undefined) aValue = ''; // Handle null/undefined for sorting
        if (bValue === null || bValue === undefined) bValue = ''; // Handle null/undefined for sorting


        if (typeof aValue === 'string' && typeof bValue === 'string') {
            return sortConfig.direction === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
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
  
  const handleDeletePart = async (partIdToDelete) => {
    if (window.confirm('Are you sure you want to delete this part?')) {
        try {
            await api.delete(`/parts/${partIdToDelete}`);
            setParts(prevParts => prevParts.filter(p => p.id !== partIdToDelete));
        } catch (err) {
            setError('Failed to delete part. ' + (err.response?.data?.message || err.message));
            console.error(err);
        }
    }
  };


  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error" sx={{ margin: 2 }}>{error}</Alert>;
  
  const canManageParts = user?.permission === 'admin' || user?.permission === 'editor';

  return (
    <Paper elevation={3} sx={{ padding: 3, marginTop: 4, marginBottom: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
        <Typography variant="h4" component="h1">
          All Parts
        </Typography>
        {canManageParts && (
            <Button component={RouterLink} to="/create-part" variant="contained" color="success">
                Create New Part
            </Button>
        )}
      </Box>
      {parts.length === 0 ? (
        <Typography variant="body1" sx={{ marginTop: 2 }}>No parts found.</Typography>
      ) : (
        <TableContainer component={Paper} sx={{ marginTop: 2 }}>
          <Table sx={{ minWidth: 650 }} aria-label="all parts table">
            <TableHead>
              <TableRow>
                <TableCell sx={{ padding: '6px 8px', fontSize: '0.875rem' }}>
                    <TableSortLabel
                        active={sortConfig.key === 'part_number'}
                        direction={sortConfig.key === 'part_number' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSortRequest('part_number')}
                    >
                        Part Number
                    </TableSortLabel>
                </TableCell>
                <TableCell sx={{ padding: '6px 8px', fontSize: '0.875rem', width: '30%' }}>
                    <TableSortLabel
                        active={sortConfig.key === 'description'}
                        direction={sortConfig.key === 'description' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSortRequest('description')}
                    >
                        Description
                    </TableSortLabel>
                </TableCell>
                <TableCell sx={{ padding: '6px 8px', fontSize: '0.875rem' }}>
                    <TableSortLabel
                        active={sortConfig.key === 'project_id'}
                        direction={sortConfig.key === 'project_id' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSortRequest('project_id')}
                    >
                        Project ID
                    </TableSortLabel>
                </TableCell>
                <TableCell sx={{ padding: '6px 8px', fontSize: '0.875rem' }}>
                    <TableSortLabel
                        active={sortConfig.key === 'type'}
                        direction={sortConfig.key === 'type' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSortRequest('type')}
                    >
                        Type
                    </TableSortLabel>
                </TableCell>
                <TableCell sx={{ padding: '6px 8px', fontSize: '0.875rem' }}>
                    <TableSortLabel
                        active={sortConfig.key === 'status'}
                        direction={sortConfig.key === 'status' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSortRequest('status')}
                    >
                        Status
                    </TableSortLabel>
                </TableCell>
                <TableCell sx={{ padding: '6px 8px', fontSize: '0.875rem' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortedParts.map(part => (
                <TableRow key={part.id} sx={{ '& td, & th': { padding: '6px 8px', fontSize: '0.875rem' } }}>
                  <TableCell>
                    <Button component={RouterLink} to={part.type === 'assembly' ? `/assemblies/${part.id}` : `/parts/${part.id}`} color="primary" sx={{ padding: '0px 3px', textTransform: 'none', justifyContent: 'flex-start', fontSize: '0.875rem' }}>{part.part_number}</Button>
                  </TableCell>
                  <TableCell>{part.description || part.name}</TableCell>
                  <TableCell>{part.project_id}</TableCell>
                  <TableCell>{part.type}</TableCell>
                  <TableCell>{part.status}</TableCell>
                  <TableCell>
                    {canManageParts && (
                        <>
                            <IconButton component={RouterLink} to={part.type === 'assembly' ? `/parts/${part.id}/edit` : `/parts/${part.id}/edit`} size="small" color="primary" aria-label="edit part" sx={{ padding: '4px'}}>
                                <EditIcon fontSize="small" />
                            </IconButton>
                            <IconButton onClick={() => handleDeletePart(part.id)} size="small" color="error" aria-label="delete part" sx={{ padding: '4px'}}>
                                <DeleteIcon fontSize="small" />
                            </IconButton>
                        </>
                    )}
                    {!canManageParts && (
                         <Button component={RouterLink} to={part.type === 'assembly' ? `/assemblies/${part.id}` : `/parts/${part.id}`} variant="outlined" size="small" sx={{ textTransform: 'none', fontSize: '0.875rem' }}>
                            View
                        </Button>
                    )}
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

export default Parts;
