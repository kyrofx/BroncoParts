import React, { useState, useEffect } from 'react';
import apiClient from '../services/api';
import { 
  Container, Typography, Box, Grid, Paper, TextField, Button, 
  List, ListItem, ListItemText, ListItemSecondaryAction, IconButton,
  Divider, Snackbar, Alert, Chip, CircularProgress
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import SyncIcon from '@mui/icons-material/Sync';

const MachinesPostProcesses = () => {
  const [machines, setMachines] = useState([]);
  const [postProcesses, setPostProcesses] = useState([]);
  const [newMachineName, setNewMachineName] = useState('');
  const [newPostProcessName, setNewPostProcessName] = useState('');
  const [alert, setAlert] = useState({ open: false, message: '', severity: 'success' });

  // Airtable options
  const [machineAirtableOptions, setMachineAirtableOptions] = useState([]);
  const [postProcessAirtableOptions, setPostProcessAirtableOptions] = useState([]);

  // Loading states
  const [loadingMachineOptions, setLoadingMachineOptions] = useState(false);
  const [loadingPostProcessOptions, setLoadingPostProcessOptions] = useState(false);
  const [syncingMachines, setSyncingMachines] = useState(false);
  const [syncingPostProcesses, setSyncingPostProcesses] = useState(false);

  // Fetch machines and post processes on component mount
  useEffect(() => {
    fetchMachines();
    fetchPostProcesses();
    fetchMachineAirtableOptions();
    fetchPostProcessAirtableOptions();
  }, []);

  // Fetch machine options from Airtable
  const fetchMachineAirtableOptions = async () => {
    setLoadingMachineOptions(true);
    try {
      const response = await apiClient.get('/machines/airtable-options');
      setMachineAirtableOptions(response.data.options || []);
    } catch (error) {
      console.error('Error fetching machine options from Airtable:', error);
      showAlert('Error fetching machine options from Airtable', 'error');
    } finally {
      setLoadingMachineOptions(false);
    }
  };

  // Fetch post process options from Airtable
  const fetchPostProcessAirtableOptions = async () => {
    setLoadingPostProcessOptions(true);
    try {
      const response = await apiClient.get('/post-processes/airtable-options');
      setPostProcessAirtableOptions(response.data.options || []);
    } catch (error) {
      console.error('Error fetching post process options from Airtable:', error);
      showAlert('Error fetching post process options from Airtable', 'error');
    } finally {
      setLoadingPostProcessOptions(false);
    }
  };

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

  // Sync machines with Airtable
  const syncMachinesWithAirtable = async () => {
    setSyncingMachines(true);
    try {
      const response = await apiClient.post('/machines/sync-with-airtable');
      showAlert('Machines synced successfully with Airtable', 'success');

      // Refresh data
      fetchMachines();
      fetchMachineAirtableOptions();

      // Show details about what was synced
      const addedToDb = response.data.added_to_db || [];
      const addedToAirtable = response.data.added_to_airtable || [];

      if (addedToDb.length > 0 || addedToAirtable.length > 0) {
        let detailMessage = 'Sync details: ';
        if (addedToDb.length > 0) {
          detailMessage += `Added ${addedToDb.length} machine(s) to database. `;
        }
        if (addedToAirtable.length > 0) {
          detailMessage += `Added ${addedToAirtable.length} machine(s) to Airtable.`;
        }
        console.log(detailMessage);
      }
    } catch (error) {
      console.error('Error syncing machines with Airtable:', error);
      showAlert(error.response?.data?.message || 'Error syncing machines with Airtable', 'error');
    } finally {
      setSyncingMachines(false);
    }
  };

  // Sync post processes with Airtable
  const syncPostProcessesWithAirtable = async () => {
    setSyncingPostProcesses(true);
    try {
      const response = await apiClient.post('/post-processes/sync-with-airtable');
      showAlert('Post processes synced successfully with Airtable', 'success');

      // Refresh data
      fetchPostProcesses();
      fetchPostProcessAirtableOptions();

      // Show details about what was synced
      const addedToDb = response.data.added_to_db || [];
      const addedToAirtable = response.data.added_to_airtable || [];

      if (addedToDb.length > 0 || addedToAirtable.length > 0) {
        let detailMessage = 'Sync details: ';
        if (addedToDb.length > 0) {
          detailMessage += `Added ${addedToDb.length} post process(es) to database. `;
        }
        if (addedToAirtable.length > 0) {
          detailMessage += `Added ${addedToAirtable.length} post process(es) to Airtable.`;
        }
        console.log(detailMessage);
      }
    } catch (error) {
      console.error('Error syncing post processes with Airtable:', error);
      showAlert(error.response?.data?.message || 'Error syncing post processes with Airtable', 'error');
    } finally {
      setSyncingPostProcesses(false);
    }
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

      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        This page allows you to manage machines and post processes, and sync them with Airtable.
      </Typography>

      <Grid container spacing={4}>
        {/* Machines Section */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5" component="h2">
                Machines
              </Typography>
              <Button
                variant="outlined"
                color="primary"
                startIcon={syncingMachines ? <CircularProgress size={20} /> : <SyncIcon />}
                onClick={syncMachinesWithAirtable}
                disabled={syncingMachines}
              >
                Sync with Airtable
              </Button>
            </Box>

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

            {/* Airtable Options */}
            <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2, mb: 1 }}>
              Airtable Machine Options:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              {loadingMachineOptions ? (
                <CircularProgress size={24} />
              ) : machineAirtableOptions.length > 0 ? (
                machineAirtableOptions.map((option, index) => (
                  <Chip 
                    key={index} 
                    label={option} 
                    variant="outlined" 
                    color="primary"
                    size="small"
                  />
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No options found in Airtable
                </Typography>
              )}
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
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5" component="h2">
                Post Processes
              </Typography>
              <Button
                variant="outlined"
                color="primary"
                startIcon={syncingPostProcesses ? <CircularProgress size={20} /> : <SyncIcon />}
                onClick={syncPostProcessesWithAirtable}
                disabled={syncingPostProcesses}
              >
                Sync with Airtable
              </Button>
            </Box>

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

            {/* Airtable Options */}
            <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2, mb: 1 }}>
              Airtable Post Process Options:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              {loadingPostProcessOptions ? (
                <CircularProgress size={24} />
              ) : postProcessAirtableOptions.length > 0 ? (
                postProcessAirtableOptions.map((option, index) => (
                  <Chip 
                    key={index} 
                    label={option} 
                    variant="outlined" 
                    color="primary"
                    size="small"
                  />
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No options found in Airtable
                </Typography>
              )}
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
