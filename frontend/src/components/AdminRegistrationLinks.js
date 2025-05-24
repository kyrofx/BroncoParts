import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../services/AuthContext'; // Corrected import path
import {
    Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField, /*Checkbox,*/ FormControlLabel,
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, IconButton, Typography, Box,
    /*Select, MenuItem, FormControl, InputLabel,*/ Grid, /*Tooltip,*/ CircularProgress, Container, Alert, DialogContentText, Switch
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit'; // Corrected import path
import DeleteIcon from '@mui/icons-material/Delete'; // Final correction for import path

function AdminRegistrationLinks() {
    const [links, setLinks] = useState([]);
    const { user } = useAuth(); // Re-enabled useAuth hook
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true); 
    const [error, setError] = useState('');
    // const { user } = useAuth(); // Removed duplicate and ensured it's commented
    // const navigate = useNavigate(); // Removed duplicate

    const [openFormDialog, setOpenFormDialog] = useState(false);
    const [currentLink, setCurrentLink] = useState(null); // For editing
    const [formData, setFormData] = useState({
        custom_path: '',
        max_uses: 1,
        default_permission: 'readonly',
        auto_enable_new_users: false,
        expires_at: '',
        fixed_username: '',
        fixed_email: '',
        is_active: true,
    });

    const fetchLinks = useCallback(async () => {
        try {
            setLoading(true); // Use 'setLoading'
            const response = await api.get('/admin/registration-links');
            setLinks(response.data.links || []);
            setError('');
        } catch (err) {
            setError('Failed to fetch registration links. ' + (err.response?.data?.message || err.message));
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (user?.permission !== 'admin') { // Re-enabled auth check
            navigate('/'); 
        } else {
            fetchLinks();
        }
    }, [user, navigate, fetchLinks]); // Re-added user to dependency array

    const handleDelete = async (linkId) => {
        if (window.confirm('Are you sure you want to delete this registration link?')) {
            try {
                await api.delete(`/admin/registration-links/${linkId}`);
                setLinks(links.filter(link => link.id !== linkId));
                alert('Link deleted successfully.');
            } catch (err) {
                setError('Failed to delete link. ' + (err.response?.data?.message || err.message));
                console.error(err);
            }
        }
    };

    const handleOpenFormDialog = (link = null) => {
        setCurrentLink(link);
        if (link) {
            setFormData({
                custom_path: link.custom_path || '',
                max_uses: link.max_uses,
                default_permission: link.default_permission,
                auto_enable_new_users: link.auto_enable_new_users,
                expires_at: link.expires_at ? link.expires_at.substring(0, 16) : '', // Format for datetime-local
                fixed_username: link.fixed_username || '',
                fixed_email: link.fixed_email || '',
                is_active: link.is_active,
            });
        } else {
            setFormData({
                custom_path: '',
                max_uses: 1,
                default_permission: 'readonly',
                auto_enable_new_users: false,
                expires_at: '',
                fixed_username: '',
                fixed_email: '',
                is_active: true,
            });
        }
        setOpenFormDialog(true);
    };

    const handleCloseFormDialog = () => {
        setOpenFormDialog(false);
        setCurrentLink(null);
        setError('');
    };

    const handleFormChange = (event) => {
        const { name, value, type, checked } = event.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value,
        }));
    };
    
    const handleFormSubmit = async () => {
        try {
            const payload = { ...formData };
            if (!payload.custom_path) delete payload.custom_path; // Send as undefined if empty
            if (!payload.expires_at) delete payload.expires_at; // Send as undefined if empty
            else payload.expires_at = new Date(payload.expires_at).toISOString();

            if (parseInt(payload.max_uses) !== 1) {
                delete payload.fixed_username;
                delete payload.fixed_email;
            } else {
                 if (!payload.fixed_username) delete payload.fixed_username;
                 if (!payload.fixed_email) delete payload.fixed_email;
            }


            if (currentLink) {
                await api.put(`/admin/registration-links/${currentLink.id}`, payload);
                alert('Link updated successfully.');
            } else {
                await api.post('/admin/registration-links', payload);
                alert('Link created successfully.');
            }
            fetchLinks();
            handleCloseFormDialog();
        } catch (err) {
            setError('Failed to save link. ' + (err.response?.data?.message || err.message));
            console.error(err);
        }
    };


    if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}><CircularProgress /></Box>; // Ensure 'loading' is used
    
    const getRegistrationUrl = (link) => {
        const baseUrl = window.location.origin;
        return `${baseUrl}/register/${link.link_identifier}`;
    };

    return (
        <Container maxWidth="lg" sx={{ marginTop: 4, marginBottom: 4 }}>
            <Paper elevation={3} sx={{ padding: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                    <Typography variant="h4" component="h1">
                        Manage Registration Links
                    </Typography>
                    <Button
                        variant="contained"
                        color="primary"
                        startIcon={<AddIcon />}
                        onClick={() => handleOpenFormDialog()}
                    >
                        Create New Link
                    </Button>
                </Box>

                {error && <Alert severity="error" sx={{ marginBottom: 2 }} onClose={() => setError('')}>{error}</Alert>}

                {links.length > 0 ? (
                    <TableContainer component={Paper} sx={{ marginTop: 2 }}>
                        <Table sx={{ minWidth: 650 }} aria-label="registration links table">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Link URL / Identifier</TableCell>
                                    <TableCell>Max Uses</TableCell>
                                    <TableCell>Current Uses</TableCell>
                                    <TableCell>Expires At</TableCell>
                                    <TableCell>Default Permission</TableCell>
                                    <TableCell>Auto Enable</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell>Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {links.map(link => (
                                    <TableRow key={link.id}>
                                        <TableCell>
                                            <a href={getRegistrationUrl(link)} target="_blank" rel="noopener noreferrer">
                                                {link.link_identifier}
                                            </a>
                                            {link.custom_path && <Typography variant="caption" display="block">(Custom: {link.custom_path})</Typography>}
                                            {!link.custom_path && <Typography variant="caption" display="block">(Token: {link.token ? link.token.substring(0, 8) + '...' : 'N/A'})</Typography>} {/* Added check for link.token existence and shortened display */}
                                        </TableCell>
                                        <TableCell>{link.max_uses === -1 ? 'Unlimited' : link.max_uses}</TableCell>
                                        <TableCell>{link.current_uses}</TableCell>
                                        <TableCell>{link.expires_at ? new Date(link.expires_at).toLocaleString() : 'Never'}</TableCell>
                                        <TableCell>{link.default_permission}</TableCell>
                                        <TableCell>{link.auto_enable_new_users ? 'Yes' : 'No'}</TableCell>
                                        <TableCell>{link.is_active ? (link.is_currently_valid ? 'Active' : 'Inactive (Expired/Used)') : 'Disabled'}</TableCell>
                                        <TableCell>
                                            <IconButton onClick={() => handleOpenFormDialog(link)} color="primary" size="small">
                                                <EditIcon />
                                            </IconButton>
                                            <IconButton onClick={() => handleDelete(link.id)} color="error" size="small"> {/* Changed to "error" for consistency */}
                                                <DeleteIcon />
                                            </IconButton>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                ) : (
                    !loading && <Typography variant="body1" sx={{ marginTop: 2 }}>No registration links found.</Typography>
                )}
            </Paper>

            <Dialog open={openFormDialog} onClose={handleCloseFormDialog} maxWidth="md" fullWidth>
                <DialogTitle>{currentLink ? 'Edit' : 'Create'} Registration Link</DialogTitle>
                <DialogContent>
                    <DialogContentText sx={{mb: 2}}>
                        Configure the details for the registration link.
                        {formData.max_uses === 1 && " For single-use links, you can pre-define username and email."}
                    </DialogContentText>
                    {error && <Alert severity="error" sx={{ marginBottom: 2 }} onClose={() => setError('')}>{error}</Alert>}
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                            <TextField
                                margin="dense"
                                label="Custom Path (optional)"
                                type="text"
                                fullWidth
                                name="custom_path"
                                value={formData.custom_path}
                                onChange={handleFormChange}
                                helperText="Alphanumeric, underscores, hyphens. e.g., 'special-invite'"
                            />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <TextField
                                margin="dense"
                                label="Max Uses (-1 for unlimited)"
                                type="number"
                                fullWidth
                                name="max_uses"
                                value={formData.max_uses}
                                onChange={handleFormChange}
                                required
                            />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <TextField
                                margin="dense"
                                label="Default Permission"
                                select
                                fullWidth
                                name="default_permission"
                                value={formData.default_permission}
                                onChange={handleFormChange}
                                SelectProps={{ native: true }}
                                required
                            >
                                <option value="readonly">Read-only</option>
                                <option value="viewer">Viewer</option>
                                <option value="editor">Editor</option>
                                {/* <option value="project_manager">Project Manager</option> Should match backend options */}
                                {/* <option value="admin">Admin</option> Usually not for self-reg links */}
                            </TextField>
                        </Grid>
                         <Grid item xs={12} sm={6}>
                            <TextField
                                margin="dense"
                                label="Expires At (optional)"
                                type="datetime-local"
                                fullWidth
                                name="expires_at"
                                value={formData.expires_at}
                                onChange={handleFormChange}
                                InputLabelProps={{ shrink: true }}
                            />
                        </Grid>
                        {parseInt(formData.max_uses) === 1 && (
                            <>
                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        margin="dense"
                                        label="Fixed Username (for single use)"
                                        type="text"
                                        fullWidth
                                        name="fixed_username"
                                        value={formData.fixed_username}
                                        onChange={handleFormChange}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        margin="dense"
                                        label="Fixed Email (for single use)"
                                        type="email"
                                        fullWidth
                                        name="fixed_email"
                                        value={formData.fixed_email}
                                        onChange={handleFormChange}
                                    />
                                </Grid>
                            </>
                        )}
                        <Grid item xs={12} sm={6}>
                            <FormControlLabel
                                control={<Switch checked={formData.auto_enable_new_users} onChange={handleFormChange} name="auto_enable_new_users" />}
                                label="Auto-enable New Users"
                            />
                        </Grid>
                         <Grid item xs={12} sm={6}>
                            <FormControlLabel
                                control={<Switch checked={formData.is_active} onChange={handleFormChange} name="is_active" />}
                                label="Link Active"
                            />
                        </Grid>
                    </Grid>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseFormDialog}>Cancel</Button>
                    <Button onClick={handleFormSubmit} color="primary" variant="contained">
                        {currentLink ? 'Save Changes' : 'Create Link'}
                    </Button>
                </DialogActions>
            </Dialog>

        </Container>
    );
}

export default AdminRegistrationLinks;
