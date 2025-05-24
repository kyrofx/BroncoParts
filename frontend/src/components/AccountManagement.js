import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { useAuth } from '../services/AuthContext';
import { Link } from 'react-router-dom';

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
            const response = await api.get('/users'); // Assuming endpoint /api/users exists
            setUsers(response.data.users || response.data); // Adjust based on actual API response
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
                // Refresh the user list to show updated status
                fetchUsers(); 
                alert('User approved successfully.');
            } catch (err) {
                setError('Failed to approve user. ' + (err.response?.data?.message || err.message));
                console.error(err);
            }
        }
    };

    useEffect(() => {
        if (user) { // Ensure user object is available before checking permission
            fetchUsers();
        }
    }, [user, fetchUsers]);

    const handleDeleteUser = async (userIdToDelete) => {
        if (window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
            try {
                await api.delete(`/users/${userIdToDelete}`);
                // Refresh the list of users after deletion
                setUsers(prevUsers => prevUsers.filter(u => u.id !== userIdToDelete));
                alert('User deleted successfully.');
            } catch (err) {
                setError('Failed to delete user. ' + (err.response?.data?.message || err.message));
                console.error(err);
            }
        }
    };

    if (!user) {
        return <p>Loading user data...</p>; // Or redirect to login
    }

    if (user.permission !== 'admin') {
        return <p>Access Denied. You must be an administrator to view this page.</p>;
    }

    if (isLoading) return <p>Loading accounts...</p>;
    if (error && users.length === 0) return <p style={{ color: 'red' }}>{error}</p>; // Show error if loading failed and no users

    return (
        <div className="container mt-4">
            <h2>User Account Management</h2>
            {error && <div className="alert alert-danger">{error}</div>} 
            <Link to="/admin/create-user" className="btn btn-primary mb-3">Create New User</Link>
            
            {users.length > 0 ? (
                <table className="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Username</th>
                            <th>Email</th>
                            <th>Permission</th>
                            <th>Enabled</th>
                            <th>Approval Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map(managedUser => (
                            <tr key={managedUser.id}>
                                <td>{managedUser.id}</td>
                                <td>{managedUser.username}</td>
                                <td>{managedUser.email}</td>
                                <td>{managedUser.permission}</td>
                                <td>{managedUser.enabled ? 'Yes' : 'No'}</td>
                                <td>
                                    {managedUser.is_approved ? 
                                        <span className="badge bg-success">Approved</span> : 
                                        <span className="badge bg-warning text-dark">Pending since {managedUser.requested_at ? new Date(managedUser.requested_at).toLocaleDateString() : 'N/A'}</span>
                                    }
                                </td>
                                <td>
                                    {!managedUser.is_approved && (
                                        <button 
                                            onClick={() => handleApproveUser(managedUser.id)} 
                                            className="btn btn-sm btn-success me-1"
                                            disabled={managedUser.id === user.id}
                                        >
                                            Approve
                                        </button>
                                    )}
                                    <Link to={`/admin/edit-user/${managedUser.id}`} className="btn btn-sm btn-outline-secondary me-1">Edit</Link>
                                    <button 
                                        onClick={() => handleDeleteUser(managedUser.id)} 
                                        className="btn btn-sm btn-outline-danger"
                                        disabled={managedUser.id === user.id} // Prevent admin from deleting themselves
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) : (
                !error && <p>No user accounts found.</p> // Show only if no error and no users
            )}
        </div>
    );
}

export default AccountManagement;
