import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../services/AuthContext';

function EditUser() {
    const { userId } = useParams();
    const navigate = useNavigate();
    const { user: adminUser } = useAuth(); // Renaming to avoid conflict with user being edited

    const [userData, setUserData] = useState({
        username: '',
        email: '',
        permission: 'viewer',
        enabled: true,
        password: '', // Added password field
        is_approved: false, // Added for account approval
    });
    const [originalUsername, setOriginalUsername] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchUserData = async () => {
            if (adminUser?.permission !== 'admin') {
                setError('You do not have permission to access this page.');
                setIsLoading(false);
                return;
            }
            try {
                setIsLoading(true);
                const response = await api.get(`/users/${userId}`);
                const fetchedUser = response.data.user || response.data; // Adjust based on API response
                setUserData({
                    username: fetchedUser.username || '',
                    email: fetchedUser.email || '',
                    permission: fetchedUser.permission || 'viewer',
                    enabled: fetchedUser.enabled !== undefined ? fetchedUser.enabled : true,
                    is_approved: fetchedUser.is_approved !== undefined ? fetchedUser.is_approved : false, // Set is_approved
                    password: '', // Initialize password as empty, not fetched
                });
                setOriginalUsername(fetchedUser.username || '');
                setError('');
            } catch (err) {
                setError('Failed to fetch user data. ' + (err.response?.data?.message || err.message));
                console.error(err);
            } finally {
                setIsLoading(false);
            }
        };

        if (adminUser) { // Ensure adminUser object is available
            fetchUserData();
        }
    }, [userId, adminUser]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setUserData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value,
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        if (!userData.email) { // Username is not editable, so not checked here
            setError('Email is required.');
            setIsLoading(false);
            return;
        }

        // Prepare payload, excluding username if it's not meant to be updated
        const { username, ...updatePayload } = userData;

        // Only include password in the payload if it has been changed
        if (!updatePayload.password) {
            delete updatePayload.password; // Remove password field if it's empty
        }

        try {
            await api.put(`/users/${userId}`, updatePayload);
            alert('User updated successfully!');
            navigate('/admin/accounts');
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to update user. Please try again.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    if (!adminUser && !isLoading) { // If still no adminUser after loading attempt
        return <p>Loading user data...</p>; // Or redirect to login
    }

    if (adminUser?.permission !== 'admin') {
        return <p>Access Denied. You must be an administrator to access this page.</p>;
    }

    if (isLoading) return <p>Loading user details...</p>;
    if (error && !userData.email) return <p sx={{ color: 'error.main' }}>{error}</p>; // Show error if loading failed

    return (
        <div className="container mt-4">
            <h2>Edit User: {originalUsername}</h2>
            {error && <div className="alert alert-danger">{error}</div>}
            <form onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label htmlFor="username" className="form-label">Username (Cannot be changed)</label>
                    <input type="text" className="form-control" id="username" name="username" value={userData.username} readOnly disabled />
                </div>
                <div className="mb-3">
                    <label htmlFor="email" className="form-label">Email</label>
                    <input type="email" className="form-control" id="email" name="email" value={userData.email} onChange={handleChange} required />
                </div>
                <div className="mb-3">
                    <label htmlFor="password" className="form-label">New Password (leave blank to keep current)</label>
                    <input type="password" className="form-control" id="password" name="password" value={userData.password} onChange={handleChange} />
                </div>
                <div className="mb-3">
                    <label htmlFor="permission" className="form-label">Permission Level</label>
                    <select className="form-select" id="permission" name="permission" value={userData.permission} onChange={handleChange}>
                        <option value="viewer">Viewer</option>
                        <option value="editor">Editor</option>
                        <option value="project_manager">Project Manager</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>
                <div className="form-check mb-3">
                    <input className="form-check-input" type="checkbox" id="enabled" name="enabled" checked={userData.enabled} onChange={handleChange} />
                    <label className="form-check-label" htmlFor="enabled">
                        Account Enabled
                    </label>
                </div>
                <div className="form-check mb-3">
                    <input className="form-check-input" type="checkbox" id="is_approved" name="is_approved" checked={userData.is_approved} onChange={handleChange} />
                    <label className="form-check-label" htmlFor="is_approved">
                        Account Approved
                    </label>
                </div>
                <button type="submit" className="btn btn-primary" disabled={isLoading}>
                    {isLoading ? 'Updating User...' : 'Update User'}
                </button>
            </form>
        </div>
    );
}

export default EditUser;
