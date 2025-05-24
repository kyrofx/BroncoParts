import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../services/AuthContext';

function CreateUser() {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [userData, setUserData] = useState({
        username: '',
        email: '',
        password: '',
        permission: 'viewer', // Default permission
        enabled: true,
        is_approved: true, // Default to approved for admin creation
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

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

        if (!userData.username || !userData.email || !userData.password) {
            setError('Username, email, and password are required.');
            setIsLoading(false);
            return;
        }

        try {
            // Assuming your API endpoint for creating users is POST /api/users
            // The backend should handle password hashing.
            await api.post('/admin/users', userData); // Changed to /api/admin/users
            alert('User created successfully!');
            navigate('/admin/accounts'); // Redirect to account management page
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to create user. Please try again.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    if (user?.permission !== 'admin') {
        return <p>Access Denied. You must be an administrator to access this page.</p>;
    }

    return (
        <div className="container mt-4">
            <h2>Create New User Account</h2>
            {error && <div className="alert alert-danger">{error}</div>}
            <form onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label htmlFor="username" className="form-label">Username</label>
                    <input type="text" className="form-control" id="username" name="username" value={userData.username} onChange={handleChange} required />
                </div>
                <div className="mb-3">
                    <label htmlFor="email" className="form-label">Email</label>
                    <input type="email" className="form-control" id="email" name="email" value={userData.email} onChange={handleChange} required />
                </div>
                <div className="mb-3">
                    <label htmlFor="password" className="form-label">Password</label>
                    <input type="password" className="form-control" id="password" name="password" value={userData.password} onChange={handleChange} required />
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
                    {isLoading ? 'Creating User...' : 'Create User'}
                </button>
            </form>
        </div>
    );
}

export default CreateUser;
