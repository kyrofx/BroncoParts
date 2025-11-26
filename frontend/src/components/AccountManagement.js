import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { useAuth } from '../services/AuthContext';
import { Link as RouterLink } from 'react-router-dom';
import {
    Container,
    Paper,
    Typography,
    Alert,
    Button,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    Box,
} from '@mui/material';

function AccountManagement() {
    const { user } = useAuth();
    const [users, setUsers] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');

    const fetchUsers = useCallback(async () => {
        if (user?.permission !== 'admin') {
            setError('You do not have permission to access this page.');
            setIsLoading(false);
            return;
        }
        try {
            setIsLoading(true);
            const response = await api.get('/users');
            setUsers(response.data.users || response.data);
            setError('');
        } catch (err) {
            setError('Failed to fetch users. ' + (err.response?.data?.message || err.message));
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    }, [user]);

    const handleApproveUser = async (userIdToApprove) => {
        if (window.confirm('Are you sure you want to approve this user? They will be enabled and able to log in.')) {
            try {
                await api.post(`/users/${userIdToApprove}/approve`);
                fetchUsers();
                alert('User approved successfully.');
            } catch (err) {
                setError('Failed to approve user. ' + (err.response?.data?.message || err.message));
                console.error(err);
            }
        }
    };

    useEffect(() => {
        if (user) {
            fetchUsers();
        }
    }, [user, fetchUsers]);

    const handleDeleteUser = async (userIdToDelete) => {
        if (window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
            try {
                await api.delete(`/users/${userIdToDelete}`);
                setUsers(prevUsers => prevUsers.filter(u => u.id !== userIdToDelete));
                alert('User deleted successfully.');
            } catch (err) {
                setError('Failed to delete user. ' + (err.response?.data?.message || err.message));
                console.error(err);
            }
        }
    };

    if (!user) {
        return (
            <Container maxWidth="lg">
                <Typography sx={{ mt: 4 }}>Loading user data...</Typography>
            </Container>
        );
    }

    if (user.permission !== 'admin') {
        return (
            <Container maxWidth="lg">
                <Typography sx={{ mt: 4 }}>Access Denied. You must be an administrator to view this page.</Typography>
            </Container>
        );
    }

    if (isLoading) {
        return (
            <Container maxWidth="lg">
                <Typography sx={{ mt: 4 }}>Loading accounts...</Typography>
            </Container>
        );
    }

    if (error && users.length === 0) {
        return (
            <Container maxWidth="lg">
                <Alert severity="error" sx={{ mt: 4 }}>{error}</Alert>
            </Container>
        );
    }

    return (
        <Container maxWidth="lg">
            <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
                <Typography variant="h4" component="h2" gutterBottom>
                    User Account Management
                </Typography>
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                <Button
                    component={RouterLink}
                    to="/admin/create-user"
                    variant="contained"
                    color="primary"
                    sx={{ mb: 3 }}
                >
                    Create New User
                </Button>

                {users.length > 0 ? (
                    <TableContainer component={Paper} variant="outlined">
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>ID</TableCell>
                                    <TableCell>Username</TableCell>
                                    <TableCell>Email</TableCell>
                                    <TableCell>Permission</TableCell>
                                    <TableCell>Enabled</TableCell>
                                    <TableCell>Approval Status</TableCell>
                                    <TableCell>Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {users.map(managedUser => (
                                    <TableRow key={managedUser.id}>
                                        <TableCell>{managedUser.id}</TableCell>
                                        <TableCell>{managedUser.username}</TableCell>
                                        <TableCell>{managedUser.email}</TableCell>
                                        <TableCell>{managedUser.permission}</TableCell>
                                        <TableCell>{managedUser.enabled ? 'Yes' : 'No'}</TableCell>
                                        <TableCell>
                                            {managedUser.is_approved ?
                                                <Chip label="Approved" color="success" size="small" /> :
                                                <Chip
                                                    label={`Pending since ${managedUser.requested_at ? new Date(managedUser.requested_at).toLocaleDateString() : 'N/A'}`}
                                                    color="warning"
                                                    size="small"
                                                />
                                            }
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                                {!managedUser.is_approved && (
                                                    <Button
                                                        onClick={() => handleApproveUser(managedUser.id)}
                                                        variant="contained"
                                                        color="success"
                                                        size="small"
                                                        disabled={managedUser.id === user.id}
                                                    >
                                                        Approve
                                                    </Button>
                                                )}
                                                <Button
                                                    component={RouterLink}
                                                    to={`/admin/edit-user/${managedUser.id}`}
                                                    variant="outlined"
                                                    size="small"
                                                >
                                                    Edit
                                                </Button>
                                                <Button
                                                    onClick={() => handleDeleteUser(managedUser.id)}
                                                    variant="outlined"
                                                    color="error"
                                                    size="small"
                                                    disabled={managedUser.id === user.id}
                                                >
                                                    Delete
                                                </Button>
                                            </Box>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                ) : (
                    !error && <Typography>No user accounts found.</Typography>
                )}
            </Paper>
        </Container>
    );
}

export default AccountManagement;
