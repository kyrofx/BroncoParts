import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { toast } from 'react-toastify';

const RegisterViaLink = () => {
    const { linkIdentifier } = useParams();
    const navigate = useNavigate();
    const [linkDetails, setLinkDetails] = useState(null);
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        firstName: '',
        lastName: '',
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchLinkDetails = async () => {
            try {
                setLoading(true);
                // Corrected API endpoint: remove leading /api as it's in the apiClient baseURL
                const response = await api.get(`/register/${linkIdentifier}`);
                if (response.data && response.data.is_currently_valid) {
                    setLinkDetails(response.data);
                    // Pre-fill form if details are fixed by the link
                    setFormData(prev => ({
                        ...prev,
                        username: response.data.fixed_username || '',
                        email: response.data.fixed_email || '',
                    }));
                } else {
                    setError(response.data.message || 'This registration link is invalid or has expired.');
                    toast.error(response.data.message || 'This registration link is invalid or has expired.');
                }
            } catch (err) {
                setError('Failed to fetch link details. The link may be invalid or expired.');
                toast.error('Failed to fetch link details. The link may be invalid or expired.');
            } finally {
                setLoading(false);
            }
        };
        fetchLinkDetails();
    }, [linkIdentifier]);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (formData.password !== formData.confirmPassword) {
            toast.error('Passwords do not match.');
            return;
        }
        setLoading(true);
        try {
            const payload = {
                username: formData.username,
                email: formData.email,
                password: formData.password,
                first_name: formData.firstName,
                last_name: formData.lastName,
            };
            // Corrected API endpoint: remove leading /api as it's in the apiClient baseURL
            await api.post(`/register/${linkIdentifier}`, payload);
            toast.success('Registration successful! You can now log in.');
            navigate('/login');
        } catch (err) {
            const errorMessage = err.response?.data?.message || 'Registration failed. Please try again.';
            setError(errorMessage);
            toast.error(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    if (loading && !linkDetails) {
        return <div className="container mt-5"><p>Loading link details...</p></div>;
    }

    if (error) {
        return <div className="container mt-5 alert alert-danger"><p>{error}</p></div>;
    }

    if (!linkDetails) {
        // This case should ideally be handled by the error state, but as a fallback:
        return <div className="container mt-5 alert alert-warning"><p>Could not load registration link information.</p></div>;
    }

    return (
        <div className="container mt-5">
            <h2>Register New Account</h2>
            <p>
                You are registering using a special link. 
                Default permission: <strong>{linkDetails.default_permission}</strong>. 
                Account will be <strong>{linkDetails.auto_enable_new_users ? 'automatically enabled' : 'disabled pending admin approval'}</strong>.
            </p>
            <form onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label htmlFor="username" className="form-label">Username</label>
                    <input
                        type="text"
                        className="form-control"
                        id="username"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        required
                        disabled={!!linkDetails.fixed_username}
                    />
                    {linkDetails.fixed_username && <small className="form-text text-muted">Username is pre-defined by the link.</small>}
                </div>
                <div className="mb-3">
                    <label htmlFor="email" className="form-label">Email</label>
                    <input
                        type="email"
                        className="form-control"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                        disabled={!!linkDetails.fixed_email}
                    />
                    {linkDetails.fixed_email && <small className="form-text text-muted">Email is pre-defined by the link.</small>}
                </div>
                <div className="mb-3">
                    <label htmlFor="password_register_link" className="form-label">Password</label>
                    <input
                        type="password"
                        className="form-control"
                        id="password_register_link"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        required
                        autoComplete="new-password"
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="confirmPassword_register_link" className="form-label">Confirm Password</label>
                    <input
                        type="password"
                        className="form-control"
                        id="confirmPassword_register_link"
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        required
                        autoComplete="new-password"
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="firstName" className="form-label">First Name</label>
                    <input
                        type="text"
                        className="form-control"
                        id="firstName"
                        name="firstName"
                        value={formData.firstName}
                        onChange={handleChange}
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="lastName" className="form-label">Last Name</label>
                    <input
                        type="text"
                        className="form-control"
                        id="lastName"
                        name="lastName"
                        value={formData.lastName}
                        onChange={handleChange}
                    />
                </div>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? 'Registering...' : 'Register'}
                </button>
            </form>
        </div>
    );
};

export default RegisterViaLink;
