import React, { useState } from 'react'; // + Import useState
import { BrowserRouter as Router, Route, Link as RouterLink, Routes, Navigate, useNavigate } from 'react-router-dom'; // + Import useNavigate
import './App.css';
import { useAuth } from './services/AuthContext';
// import { ThemeProvider } from '@mui/material/styles'; // Removed ThemeProvider import
// import theme from './theme'; // Import the custom theme - this can be kept if App.js needs to access theme object directly for styling, but it won't provide context.
import { AppBar, Toolbar, Typography, Button, Box, Container, Menu, MenuItem, IconButton } from '@mui/material'; // + Import Menu, MenuItem, IconButton
import AccountCircle from '@mui/icons-material/AccountCircle'; // + Import an icon

// Import actual components
import Home from './components/Home';
import Projects from './components/Projects';
// import Parts from './components/Parts'; // Removed unused import
import Login from './components/Login';
import Register from './components/Register';
import CreateProject from './components/CreateProject';
import CreatePart from './components/CreatePart';
import ProjectDetails from './components/ProjectDetails';
import PartDetails from './components/PartDetails';
import AssemblyDetails from './components/AssemblyDetails'; // Import AssemblyDetails
import EditPart from './components/EditPart';
import EditProject from './components/EditProject';
import Dashboard from './components/Dashboard';
import ProjectDashboard from './components/ProjectDashboard';
import ProjectDashboardParts from './components/ProjectDashboardParts';
import AccountManagement from './components/AccountManagement';
import CreateUser from './components/CreateUser';
import EditUser from './components/EditUser';
import AdminRegistrationLinks from './components/AdminRegistrationLinks'; // Import new component
import RegisterViaLink from './components/RegisterViaLink'; // Import for public registration route
import UserSettings from './components/UserSettings'; // + Import UserSettings
import ProjectTreeView from './components/ProjectTreeView'; // Added ProjectTreeView
import MachinesPostProcesses from './components/MachinesPostProcesses'; // Import MachinesPostProcesses component

// Keep other placeholders for now, or create basic versions of them
// const CreateProject = () => <h2>Create New Project</h2>; // Remove placeholder

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <p>Loading authentication...</p>; // Or a spinner component
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

// Navigation component that uses useNavigate hook
const AppNavigation = () => {
  const { isAuthenticated, logout, user } = useAuth();
  const navigate = useNavigate();

  // State for dropdown menu
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleUserSettings = () => {
    navigate('/user-settings');
    handleClose();
  };

  const handleLogout = () => {
    logout();
    handleClose();
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            <Button color="inherit" component={RouterLink} to="/">BroncoParts</Button>
          </Typography>
          {isAuthenticated ? (
            <>
              <Button color="inherit" component={RouterLink} to="/projects">Projects</Button>
              {user?.permission === 'admin' && (
                <>
                  <Button color="inherit" component={RouterLink} to="/admin/accounts">Account Management</Button>
                  <Button color="inherit" component={RouterLink} to="/admin/registration-links">Manage Reg Links</Button>
                </>
              )}
              <IconButton
                size="large"
                aria-label="account of current user"
                aria-controls="menu-appbar"
                aria-haspopup="true"
                onClick={handleMenu}
                color="inherit"
              >
                <AccountCircle />
                <Typography variant="body1" sx={{ ml: 1 }}>{user?.username}</Typography> 
              </IconButton>
              <Menu
                id="menu-appbar"
                anchorEl={anchorEl}
                anchorOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={open}
                onClose={handleClose}
              >
                <MenuItem onClick={handleUserSettings}>User Settings</MenuItem>
                <MenuItem onClick={handleLogout}>Logout</MenuItem>
              </Menu>
            </>
          ) : (
            <>
              <Button color="inherit" component={RouterLink} to="/login">Login</Button>
              <Button color="inherit" component={RouterLink} to="/register">Register</Button>
            </>
          )}
        </Toolbar>
      </AppBar>

      <Container component="main" sx={{ flexGrow: 1, py: 3 }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route 
            path="/projects" 
            element={
              <ProtectedRoute>
                <Projects />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/create-project" 
            element={
              <ProtectedRoute>
                <CreateProject />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/projects/:projectId" 
            element={
              <ProtectedRoute>
                <ProjectDetails />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/projects/:projectId/tree" 
            element={
              <ProtectedRoute>
                <ProjectTreeView />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/projects/:projectId/edit"
            element={
              <ProtectedRoute>
                <EditProject />
              </ProtectedRoute>
            }
          />
          <Route 
            path="/parts/:partId" 
            element={
              <ProtectedRoute>
                <PartDetails />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/assemblies/:partId" 
            element={
              <ProtectedRoute>
                <AssemblyDetails />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/create-part" 
            element={
              <ProtectedRoute>
                <CreatePart />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/parts/:partId/edit" 
            element={
              <ProtectedRoute>
                <EditPart />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/dashboards" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/projects/:projectId/dashboard" 
            element={
              <ProtectedRoute>
                <ProjectDashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/projects/:projectId/dashboard/parts" 
            element={
              <ProtectedRoute>
                <ProjectDashboardParts />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/accounts" 
            element={
              <ProtectedRoute>
                <AccountManagement />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/create-user" 
            element={
              <ProtectedRoute>
                <CreateUser />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/edit-user/:userId" 
            element={
              <ProtectedRoute>
                <EditUser />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/registration-links" 
            element={
              <ProtectedRoute>
                <AdminRegistrationLinks />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/register/:linkIdentifier" 
            element={<RegisterViaLink />} 
          />
          <Route 
            path="/machines-postprocesses" 
            element={
              <ProtectedRoute>
                <MachinesPostProcesses />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/user-settings"
            element={
              <ProtectedRoute>
                <UserSettings />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Container>

      <Box component="footer" sx={{ bgcolor: 'background.paper', py: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          BroncoParts by kyrofx, for the Bronco Racing team.
        </Typography>
      </Box>
    </Box>
  );
};

function App() {
  return (
    <Router>
      <AppNavigation />
    </Router>
  );
}

export default App;
