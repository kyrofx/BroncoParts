import React, { useState, useEffect } from 'react';
import apiClient from '../services/api';
import { 
  Container, Typography, Box, Grid, Paper, TextField, Button, 
  List, ListItem, ListItemText, ListItemSecondaryAction, IconButton,
  Divider, Snackbar, Alert
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

const MachinesPostProcesses = () => {
  const [machines, setMachines] = useState([]);
  const [postProcesses, setPostProcesses] = useState([]);
  const [newMachineName, setNewMachineName] = useState('');
  const [newPostProcessName, setNewPostProcessName] = useState('');
  const [alert, setAlert] = useState({ open: false, message: '', severity: 'success' });

  // Fetch machines and post processes on component mount
  useEffect(() => {
    fetchMachines();
    fetchPostProcesses();
  }, []);

  // Fetch machines from API
  const fetchMachines = async () => {
    try {
      const response = await apiClient.get('/machines');
      setMachines(response.data.machines || []);
    } catch (error) {
      console.error('Error fetching machines:', error);
      showAlert('Error fetching machines', 'error');
    }
  };

  // Fetch post processes from API
  const fetchPostProcesses = async () => {
    try {
      const response = await apiClient.get('/post-processes');
      setPostProcesses(response.data.post_processes || []);
    } catch (error) {
      console.error('Error fetching post processes:', error);
      showAlert('Error fetching post processes', 'error');
    }
  };

  // Add a new machine
  const addMachine = async () => {
    if (!newMachineName.trim()) {
      showAlert('Machine name cannot be empty', 'error');
      return;
    }

    try {
      await apiClient.post('/machines', { name: newMachineName });
      setNewMachineName('');
      fetchMachines();
      showAlert('Machine added successfully', 'success');
    } catch (error) {
      console.error('Error adding machine:', error);
      showAlert(error.response?.data?.message || 'Error adding machine', 'error');
    }
  };

  // Add a new post process
  const addPostProcess = async () => {
    if (!newPostProcessName.trim()) {
      showAlert('Post process name cannot be empty', 'error');
      return;
    }

    try {
      await apiClient.post('/post-processes', { name: newPostProcessName });
      setNewPostProcessName('');
      fetchPostProcesses();
      showAlert('Post process added successfully', 'success');
    } catch (error) {
      console.error('Error adding post process:', error);
      showAlert(error.response?.data?.message || 'Error adding post process', 'error');
    }
  };

  // Delete a machine
  const deleteMachine = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete machine "${name}"?`)) {
      return;
    }

    try {
      await apiClient.delete(`/machines/${id}`);
      fetchMachines();
      showAlert(`Machine "${name}" deleted successfully`, 'success');
    } catch (error) {
      console.error('Error deleting machine:', error);
      showAlert(error.response?.data?.message || 'Error deleting machine', 'error');
    }
  };

  // Delete a post process
  const deletePostProcess = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete post process "${name}"?`)) {
      return;
    }

    try {
      await apiClient.delete(`/post-processes/${id}`);
      fetchPostProcesses();
      showAlert(`Post process "${name}" deleted successfully`, 'success');
    } catch (error) {
      console.error('Error deleting post process:', error);
      showAlert(error.response?.data?.message || 'Error deleting post process', 'error');
    }
  };

  // Show alert message
  const showAlert = (message, severity) => {
    setAlert({ open: true, message, severity });
  };

  // Close alert
  const handleCloseAlert = () => {
    setAlert({ ...alert, open: false });
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" component="h1" gutterBottom sx={{ mt: 4 }}>
        Machines & Post Processes Management
      </Typography>
      
      <Grid container spacing={4}>
        {/* Machines Section */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h5" component="h2" gutterBottom>
              Machines
            </Typography>
            
            <Box sx={{ mb: 3, display: 'flex', gap: 1 }}>
              <TextField
                label="New Machine Name"
                variant="outlined"
                fullWidth
                value={newMachineName}
                onChange={(e) => setNewMachineName(e.target.value)}
              />
              <Button 
                variant="contained" 
                color="primary" 
                onClick={addMachine}
                sx={{ minWidth: '120px' }}
              >
                Add
              </Button>
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            <List>
              {machines.length > 0 ? (
                machines.map((machine) => (
                  <ListItem key={machine.id}>
                    <ListItemText primary={machine.name} />
                    <ListItemSecondaryAction>
                      <IconButton 
                        edge="end" 
                        aria-label="delete" 
                        onClick={() => deleteMachine(machine.id, machine.name)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))
              ) : (
                <ListItem>
                  <ListItemText primary="No machines found" />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>
        
        {/* Post Processes Section */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h5" component="h2" gutterBottom>
              Post Processes
            </Typography>
            
            <Box sx={{ mb: 3, display: 'flex', gap: 1 }}>
              <TextField
                label="New Post Process Name"
                variant="outlined"
                fullWidth
                value={newPostProcessName}
                onChange={(e) => setNewPostProcessName(e.target.value)}
              />
              <Button 
                variant="contained" 
                color="primary" 
                onClick={addPostProcess}
                sx={{ minWidth: '120px' }}
              >
                Add
              </Button>
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            <List>
              {postProcesses.length > 0 ? (
                postProcesses.map((postProcess) => (
                  <ListItem key={postProcess.id}>
                    <ListItemText primary={postProcess.name} />
                    <ListItemSecondaryAction>
                      <IconButton 
                        edge="end" 
                        aria-label="delete" 
                        onClick={() => deletePostProcess(postProcess.id, postProcess.name)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))
              ) : (
                <ListItem>
                  <ListItemText primary="No post processes found" />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>
      </Grid>
      
      <Snackbar 
        open={alert.open} 
        autoHideDuration={6000} 
        onClose={handleCloseAlert}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseAlert} severity={alert.severity} sx={{ width: '100%' }}>
          {alert.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default MachinesPostProcesses;