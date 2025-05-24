import React from 'react';
import { AppBar, Toolbar, Typography, Button } from '@mui/material'; // Corrected import path
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../../services/AuthContext'; // Corrected path for useAuth
import { alpha } from '@mui/material/styles'; // Import alpha for hover effect

const Navbar = () => { // Renamed Header to Navbar to match filename
    const { user, logout } = useAuth();

    return (
        <AppBar position="static">
            <Toolbar>
                <Typography variant="h6" sx={{ flexGrow: 1 }}> {/* Changed style to sx */}
                    BroncoParts
                </Typography>
                <>
                    {user?.permission === 'admin' && (
                        <Button color="inherit" component={RouterLink} to="/admin/users">Manage Users</Button>
                    )}
                    {user?.permission === 'admin' && ( // Add link for admins
                        <Button color="inherit" component={RouterLink} to="/admin/registration-links">Manage Reg Links</Button>
                    )}
                    <Button 
                        color="inherit" 
                        onClick={logout}
                        sx={{
                            '&:hover': {
                                backgroundColor: alpha(theme.palette.error.main, 0.1), // Adjusted for a subtle red hover
                                color: theme.palette.error.main // Optional: change text color on hover
                            },
                            // If you want the button itself to be red, uncomment below and adjust imports for red color if needed
                            // backgroundColor: theme.palette.error.main,
                            // color: theme.palette.error.contrastText,
                            // '&:hover': {
                            //     backgroundColor: theme.palette.error.dark,
                            // }
                        }}
                    >
                        Logout
                    </Button>
                </>
            </Toolbar>
        </AppBar>
    );
};

export default Navbar; // Renamed Header to Navbar