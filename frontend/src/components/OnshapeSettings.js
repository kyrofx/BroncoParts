import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../services/api';

function OnshapeSettings() {
  const { projectId } = useParams();
  const [form, setForm] = useState({ document_id: '', workspace_id: '', naming_scheme: 'OS', client_id: '', client_secret: '', access_token: '', refresh_token: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await api.get(`/projects/${projectId}/onshape`);
        if (res.data.config) setForm(res.data.config);
      } catch (err) {
        console.error(err);
        setError('Failed to load settings');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [projectId]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.put(`/projects/${projectId}/onshape`, form);
      alert('Settings saved');
    } catch (err) {
      console.error(err);
      setError('Failed to save settings');
    }
  };

  if (loading) return <p>Loading...</p>;

  return (
    <div className="container mt-4">
      <h2>Onshape Settings</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="form-label">Document ID</label>
          <input className="form-control" name="document_id" value={form.document_id || ''} onChange={handleChange} />
        </div>
        <div className="mb-3">
          <label className="form-label">Workspace ID</label>
          <input className="form-control" name="workspace_id" value={form.workspace_id || ''} onChange={handleChange} />
        </div>
        <div className="mb-3">
          <label className="form-label">Naming Scheme</label>
          <input className="form-control" name="naming_scheme" value={form.naming_scheme || ''} onChange={handleChange} />
        </div>
        <div className="mb-3">
          <label className="form-label">Client ID</label>
          <input className="form-control" name="client_id" value={form.client_id || ''} onChange={handleChange} />
        </div>
        <div className="mb-3">
          <label className="form-label">Client Secret</label>
          <input className="form-control" name="client_secret" value={form.client_secret || ''} onChange={handleChange} />
        </div>
        <div className="mb-3">
          <label className="form-label">Access Token</label>
          <input className="form-control" name="access_token" value={form.access_token || ''} onChange={handleChange} />
        </div>
        <div className="mb-3">
          <label className="form-label">Refresh Token</label>
          <input className="form-control" name="refresh_token" value={form.refresh_token || ''} onChange={handleChange} />
        </div>
        <button type="submit" className="btn btn-primary">Save</button>
      </form>
    </div>
  );
}

export default OnshapeSettings;
