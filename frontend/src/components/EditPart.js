import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../services/AuthContext';
import {
    Container, Typography, TextField, Button, Grid, Box, CircularProgress, Alert,
    Select, MenuItem, FormControl, InputLabel, Checkbox, FormControlLabel,
    Accordion, AccordionSummary, AccordionDetails // Added Accordion components
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'; // Added ExpandMoreIcon

// Custom styles for the Accordion to make it less prominent
const accordionSx = {
    border: 'none',
    boxShadow: 'none',
    '&::before': { // Removes the top border line from the accordion
        display: 'none',
    },
    '&.Mui-expanded': {
        margin: '0', // Reset margin when expanded
        boxShadow: 'none',
    },
    // Ensure no background color change on expansion unless explicitly set in AccordionDetails
    backgroundColor: 'transparent', 
};

const accordionSummarySx = {
    padding: '0 8px', // Reduced padding for a tighter look
    minHeight: 'auto',
    backgroundColor: 'transparent', // Ensure summary itself is transparent
    '&.Mui-focusVisible': { // Remove focus ring blue background
        backgroundColor: 'transparent',
    },
    '&:hover': {
        backgroundColor: 'rgba(0, 0, 0, 0.03)', // Very subtle hover for discoverability
    },
    '& .MuiAccordionSummary-content': {
        margin: '8px 0', // Adjust vertical spacing of the content (the Typography)
    },
    '&.Mui-expanded': {
        minHeight: 'auto', // Keep height consistent when expanded
    },
};

function EditPart() {
    const { partId } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();

    const [partData, setPartData] = useState({
        name: '',
        description: '',
        material: '',
        revision: '',
        status: 'designing',
        quantity_on_hand: 0,
        quantity_on_order: 0,
        notes: '',
        source_material: '',
        have_material: false,
        quantity_required: 0,
        cut_length: '',
        priority: 1,
        drawing_created: false,
        parent_id: null,
    });
    const [originalPartData, setOriginalPartData] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [availableParents, setAvailableParents] = useState([]);
    const [advancedFieldsOpen, setAdvancedFieldsOpen] = useState(false); // State for Accordion

    useEffect(() => {
        const fetchPartDetails = async () => {
            setIsLoading(true);
            try {
                const response = await api.get(`/parts/${partId}`);
                const fetchedPart = response.data.part;
                setPartData({
                    name: fetchedPart.name || '',
                    description: fetchedPart.description || '',
                    material: fetchedPart.material || '',
                    revision: fetchedPart.revision || '',
                    status: fetchedPart.status || 'designing',
                    quantity_on_hand: fetchedPart.quantity_on_hand || 0,
                    quantity_on_order: fetchedPart.quantity_on_order || 0,
                    notes: fetchedPart.notes || '',
                    source_material: fetchedPart.source_material || '',
                    have_material: fetchedPart.have_material || false,
                    quantity_required: fetchedPart.quantity_required || 0,
                    cut_length: fetchedPart.cut_length || '',
                    priority: fetchedPart.priority || 1,
                    drawing_created: fetchedPart.drawing_created || false,
                    parent_id: fetchedPart.parent_id || null,
                });
                setOriginalPartData(fetchedPart);

                if (fetchedPart.project_id) {
                    const parentsResponse = await api.get(`/projects/${fetchedPart.project_id}/parts`);
                    setAvailableParents(
                        parentsResponse.data.parts.filter(p => p.type === 'assembly' && p.id !== fetchedPart.id)
                    );
                }
                setError('');
            } catch (err) {
                setError('Failed to fetch part details. ' + (err.response?.data?.message || err.message));
                console.error(err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchPartDetails();
    }, [partId]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setPartData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : (type === 'number' && name !== 'cut_length' ? parseFloat(value) : value)
        }));
    };

    const handleParentChange = (e) => {
        const { value } = e.target;
        setPartData(prev => ({
            ...prev,
            parent_id: value ? parseInt(value) : null
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        const updatePayload = { ...partData };
        if (updatePayload.parent_id === '') {
            updatePayload.parent_id = null;
        } else if (updatePayload.parent_id !== null) {
            updatePayload.parent_id = parseInt(updatePayload.parent_id);
        }

        try {
            await api.put(`/parts/${partId}`, updatePayload);
            navigate(originalPartData.type === 'assembly' ? `/assemblies/${partId}` : `/parts/${partId}`);
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to update part. Please try again.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading && !originalPartData) return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
            <CircularProgress />
        </Box>
    );

    if (error && !originalPartData) return (
        <Container maxWidth="sm" sx={{ mt: 4 }}>
            <Alert severity="error">{error}</Alert>
        </Container>
    );

    if (!originalPartData) return (
        <Container maxWidth="sm" sx={{ mt: 4 }}>
            <Alert severity="warning">Part not found or could not be loaded.</Alert>
        </Container>
    );

    const canEditPart = user?.permission === 'admin' || user?.permission === 'editor';
    if (!canEditPart) {
        return (
            <Container maxWidth="sm" sx={{ mt: 4 }}>
                <Alert severity="error">You do not have permission to edit this part.</Alert>
            </Container>
        );
    }

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}> {/* Changed maxWidth to lg */}
            
                <Typography variant="h4" component="h1" gutterBottom sx={{ textAlign: 'center', mb: 3 }}>
                    Edit {originalPartData.type === 'assembly' ? 'Assembly' : 'Part'}: {originalPartData.part_number}
                </Typography>
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                
                <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
                        
                        
                                <Grid item xs={12}>
                                    <TextField
                                        label="Part Number"
                                        value={originalPartData.part_number}
                                        variant="outlined"
                                        fullWidth
                                        disabled
                                    />
                                </Grid>
                                <Grid item xs={12}>
                                    <TextField
                                        label="Type"
                                        value={originalPartData.type}
                                        variant="outlined"
                                        fullWidth
                                        disabled
                                    />
                                </Grid>
                                <Grid item xs={12}>
                                    <TextField
                                        label="Project ID"
                                        value={originalPartData.project_id}
                                        variant="outlined"
                                        fullWidth
                                        disabled
                                    />
                                </Grid>
                            

                        <Grid item xs={12}>
                            <TextField
                                required
                                fullWidth
                                id="name"
                                label="Name"
                                name="name"
                                value={partData.name}
                                onChange={handleChange}
                                autoFocus
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                id="description"
                                label="Description"
                                name="description"
                                multiline
                                rows={3}
                                value={partData.description}
                                onChange={handleChange}
                            />
                        </Grid>

                        {originalPartData.type === 'part' && (
                            <Grid item xs={12}>
                                <FormControl fullWidth>
                                    <InputLabel id="parent_id-label">Parent Assembly</InputLabel>
                                    <Select
                                        labelId="parent_id-label"
                                        id="parent_id"
                                        name="parent_id"
                                        value={partData.parent_id === null ? '' : partData.parent_id}
                                        label="Parent Assembly"
                                        onChange={handleParentChange}
                                    >
                                        <MenuItem value=""><em>None</em></MenuItem>
                                        {availableParents.map(p => (
                                            <MenuItem key={p.id} value={p.id}>{p.name} ({p.part_number})</MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>
                            </Grid>
                        )}
                        
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                id="notes"
                                label="Notes"
                                name="notes"
                                multiline
                                rows={3}
                                value={partData.notes}
                                onChange={handleChange}
                            />
                        </Grid>

                        {/* Accordion for Advanced Fields */}
                        <Grid item xs={12} sx={{ mt: 1, mb:1 }}>
                            <Accordion 
                                expanded={advancedFieldsOpen} 
                                onChange={() => setAdvancedFieldsOpen(!advancedFieldsOpen)} 
                                sx={accordionSx}
                                disableGutters // Removes default gutters for a cleaner look with custom padding
                            >
                                <AccordionSummary
                                    expandIcon={<ExpandMoreIcon />}
                                    aria-controls="advanced-fields-content"
                                    id="advanced-fields-header"
                                    sx={accordionSummarySx}
                                >
                                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>Optional Fields</Typography>
                                </AccordionSummary>
                                <AccordionDetails sx={{ pt: 0.5, pb: 1.5, backgroundColor: 'transparent' }}> 
                                    {/* backgroundColor set to transparent to avoid blue flash, content bg can be set if needed */}
                                    <Grid container spacing={2.5}>
                                        <Grid item xs={12} sm={6}>
                                            <TextField
                                                fullWidth
                                                id="material"
                                                label="Material"
                                                name="material"
                                                value={partData.material}
                                                onChange={handleChange}
                                                variant="outlined"
                                            />
                                        </Grid>
                                        <Grid item xs={12} sm={6}>
                                            <TextField
                                                fullWidth
                                                id="revision"
                                                label="Revision"
                                                name="revision"
                                                value={partData.revision}
                                                onChange={handleChange}
                                                variant="outlined"
                                            />
                                        </Grid>

                                        <Grid item xs={12} sm={6}>
                                            <FormControl fullWidth variant="outlined">
                                                <InputLabel id="status-label">Status</InputLabel>
                                                <Select
                                                    labelId="status-label"
                                                    id="status"
                                                    name="status"
                                                    value={partData.status}
                                                    label="Status"
                                                    onChange={handleChange}
                                                >
                                                    <MenuItem value="designing">Designing</MenuItem>
                                                    <MenuItem value="ordered">Ordered</MenuItem>
                                                    <MenuItem value="received">Received</MenuItem>
                                                    <MenuItem value="manufacturing">Manufacturing</MenuItem>
                                                    <MenuItem value="assembly">Assembly</MenuItem>
                                                    <MenuItem value="testing">Testing</MenuItem>
                                                    <MenuItem value="completed">Completed</MenuItem>
                                                    <MenuItem value="obsolete">Obsolete</MenuItem>
                                                </Select>
                                            </FormControl>
                                        </Grid>
                                        <Grid item xs={12} sm={6}>
                                            <TextField
                                                fullWidth
                                                type="number"
                                                id="priority"
                                                label="Priority"
                                                name="priority"
                                                value={partData.priority}
                                                onChange={handleChange}
                                                inputProps={{ min: 0 }}
                                                variant="outlined"
                                            />
                                        </Grid>

                                        <Grid item xs={12} sm={6}>
                                            <TextField
                                                fullWidth
                                                type="number"
                                                id="quantity_on_hand"
                                                label="Quantity on Hand"
                                                name="quantity_on_hand"
                                                value={partData.quantity_on_hand}
                                                onChange={handleChange}
                                                inputProps={{ min: 0 }}
                                                variant="outlined"
                                            />
                                        </Grid>
                                        <Grid item xs={12} sm={6}>
                                            <TextField
                                                fullWidth
                                                type="number"
                                                id="quantity_on_order"
                                                label="Quantity on Order"
                                                name="quantity_on_order"
                                                value={partData.quantity_on_order}
                                                onChange={handleChange}
                                                inputProps={{ min: 0 }}
                                                variant="outlined"
                                            />
                                        </Grid>

                                        <Grid item xs={12} sm={6}>
                                            <TextField
                                                fullWidth
                                                type="number"
                                                id="quantity_required"
                                                label="Quantity Required"
                                                name="quantity_required"
                                                value={partData.quantity_required}
                                                onChange={handleChange}
                                                inputProps={{ min: 0 }}
                                                variant="outlined"
                                            />
                                        </Grid>
                                        <Grid item xs={12} sm={6}>
                                            <TextField
                                                fullWidth
                                                id="cut_length"
                                                label="Cut Length"
                                                name="cut_length"
                                                value={partData.cut_length}
                                                onChange={handleChange}
                                                variant="outlined"
                                            />
                                        </Grid>
                                        
                                        <Grid item xs={12}>
                                            <TextField
                                                fullWidth
                                                id="source_material"
                                                label="Source Material (e.g. McMaster P/N)"
                                                name="source_material"
                                                value={partData.source_material}
                                                onChange={handleChange}
                                                variant="outlined"
                                            />
                                        </Grid>

                                        <Grid item xs={12} sm={6}>
                                            <FormControlLabel
                                                control={<Checkbox checked={partData.have_material} onChange={handleChange} name="have_material" />}
                                                label="Have Material?"
                                            />
                                        </Grid>
                                        <Grid item xs={12} sm={6}>
                                            <FormControlLabel
                                                control={<Checkbox checked={partData.drawing_created} onChange={handleChange} name="drawing_created" />}
                                                label="Drawing Created?"
                                            />
                                        </Grid>
                                    </Grid>
                                </AccordionDetails>
                            </Accordion>
                        </Grid>

                        <Grid item xs={12}>
                            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2, mb:1 }}>
                                <Button 
                                    onClick={() => navigate(-1)} 
                                    sx={{ 
                                        mr: 1.5, 
                                        color: 'text.secondary', 
                                        borderColor: 'rgba(0, 0, 0, 0.23)',
                                        '&:hover': {
                                            backgroundColor: 'rgba(0, 0, 0, 0.04)', 
                                            borderColor: 'rgba(0, 0, 0, 0.3)',
                                        }
                                    }} 
                                    variant="outlined"
                                >
                                    Cancel
                                </Button>
                                <Button
                                    type="submit"
                                    variant="contained"
                                    color="primary" 
                                    disabled={isLoading}
                                >
                                    {isLoading ? <CircularProgress size={24} sx={{ color: 'white' }} /> : `Update ${originalPartData.type}`}
                                </Button>
                            </Box>
                        </Grid>
                        
                </Box>
        </Container>
    );
}

export default EditPart;
