import React from 'react';
import { Link } from 'react-router-dom';

// TODO: Fetch actual dashboard data, e.g., stats, recent activity, etc.

function Dashboard() {
    // Placeholder data - replace with actual data fetching and state
    const stats = {
        totalProjects: 0,
        totalParts: 0,
        openOrders: 0, // Assuming orders might be part of a dashboard
    };

    // Placeholder for recent projects or activity
    const recentProjects = [];

    return (
        <div>
            <h2>Main Dashboard</h2>
            
            <div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: '20px' }}>
                <div style={{ border: '1px solid #ccc', padding: '20px', textAlign: 'center' }}>
                    <h3>{stats.totalProjects}</h3>
                    <p>Total Projects</p>
                </div>
                <div style={{ border: '1px solid #ccc', padding: '20px', textAlign: 'center' }}>
                    <h3>{stats.totalParts}</h3>
                    <p>Total Parts</p>
                </div>
                <div style={{ border: '1px solid #ccc', padding: '20px', textAlign: 'center' }}>
                    <h3>{stats.openOrders}</h3>
                    <p>Open Orders</p>
                </div>
            </div>

            <h3>Quick Links</h3>
            <ul>
                <li><Link to="/projects">View All Projects</Link></li>
                <li><Link to="/create-project">Create New Project</Link></li>
                <li><Link to="/parts">View All Parts</Link></li>
                <li><Link to="/create-part">Create New Part</Link></li>
                {/* Add more links as needed, e.g., to orders if implemented */}
            </ul>

            <h3>Recent Projects</h3>
            {recentProjects.length > 0 ? (
                <ul>
                    {recentProjects.map(project => (
                        <li key={project.id}>
                            <Link to={`/projects/${project.id}`}>{project.name}</Link> - 
                            <Link to={`/projects/${project.id}/dashboard`}>View Dashboard</Link>
                        </li>
                    ))}
                </ul>
            ) : (
                <p>No recent projects to display. <Link to="/projects">View projects</Link></p>
            )}
            {/* TODO: Add more sections like recent parts, alerts, etc. based on NEW_README.md */}
        </div>
    );
}

export default Dashboard;
