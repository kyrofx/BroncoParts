import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Container, Typography, TextField, Button } from '@mui/material';
import api from '../services/api';

const OnshapeSettings = () => {
  const { projectId } = useParams();
  const [form, setForm] = useState({
    client_id: '',
    client_secret: '',
    part_number_format: '',
    base_url: 'https://cad.onshape.com'
  });
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const resp = await api.get(`/projects/${projectId}/onshape-settings`);
        if (resp.data.settings) setForm(resp.data.settings);
      } catch (err) {
        console.error(err);
      }
    };
    fetchSettings();
  }, [projectId]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/projects/${projectId}/onshape-settings`, form);
      setMessage('Settings saved');
    } catch (err) {
      console.error(err);
      setMessage('Error saving settings');
    }
  };

  return (
    <Container>
      <Typography variant="h4" gutterBottom sx={{ mt: 2 }}>Onshape Settings</Typography>
      <form onSubmit={handleSubmit}>
        <TextField label="Client ID" name="client_id" value={form.client_id} onChange={handleChange} fullWidth margin="normal" />
        <TextField label="Client Secret" name="client_secret" value={form.client_secret} onChange={handleChange} fullWidth margin="normal" />
        <TextField label="Part Number Format" name="part_number_format" value={form.part_number_format} onChange={handleChange} fullWidth margin="normal" />
        <TextField label="Base URL" name="base_url" value={form.base_url} onChange={handleChange} fullWidth margin="normal" />
        <Button type="submit" variant="contained" sx={{ mt: 2 }}>Save</Button>
      </form>
      {message && <Typography sx={{ mt: 2 }}>{message}</Typography>}
    </Container>
  );
};

export default OnshapeSettings;
