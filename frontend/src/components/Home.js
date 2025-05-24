import React, { useState, useEffect } from 'react';
import api from '../services/api'; // Assuming you have an api service
import { Typography, Grid, Card, CardContent, CircularProgress, Box } from '@mui/material';

const Home = () => {
  const [stats, setStats] = useState({
    activeUsers: 0,
    projects: 0,
    parts: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const usersResponse = await api.get('/stats/active-users');
        const projectsResponse = await api.get('/stats/projects');
        const partsResponse = await api.get('/stats/parts');
        
        // Placeholder data
        // await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API delay
        // const placeholderStats = {
        //   activeUsers: 15, // Example data
        //   projects: 50,    // Example data
        //   parts: 1250,     // Example data
        // };

        // setStats(placeholderStats);
        setStats({
          activeUsers: usersResponse.data.count,
          projects: projectsResponse.data.count,
          parts: partsResponse.data.count,
        });
        setError(null);
      } catch (err) {
        console.error("Failed to fetch stats:", err);
        setError("Failed to load statistics. Please try again later.");
        // Fallback to zeros or keep previous stats if partial load is acceptable
        setStats({ activeUsers: 0, projects: 0, parts: 0 });
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom component="h2" sx={{ mb: 3, textAlign: 'center' }}>
        Welcome to Bronco Parts!
      </Typography>
      <Typography variant="subtitle1" gutterBottom sx={{ mb: 4, textAlign: 'center' }}>
        The Bronco Solution for Parts Management. 
      </Typography>

      <Typography variant="h5" gutterBottom component="h3" sx={{ mb: 2, textAlign: 'center' }}>
        System Statistics
      </Typography>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
          <CircularProgress />
        </Box>
      )}
      {error && (
        <Typography color="error" sx={{ textAlign: 'center', my: 3 }}>
          {error}
        </Typography>
      )}
      {!loading && !error && (
        <Grid container spacing={3} justifyContent="center">
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ textAlign: 'center' }}>
              <CardContent>
                <Typography variant="h6" component="div">
                  Active Users
                </Typography>
                <Typography variant="h3" component="p">
                  {stats.activeUsers}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ textAlign: 'center' }}>
              <CardContent>
                <Typography variant="h6" component="div">
                  Total Projects
                </Typography>
                <Typography variant="h3" component="p">
                  {stats.projects}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ textAlign: 'center' }}>
              <CardContent>
                <Typography variant="h6" component="div">
                  Total Parts
                </Typography>
                <Typography variant="h3" component="p">
                  {stats.parts}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default Home;
