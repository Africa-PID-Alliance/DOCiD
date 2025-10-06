"use client";

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Modal,
  Tabs,
  Tab,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Paper,
  Grid,
  Divider,
  CircularProgress,
  useTheme
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  AccountBalance as FunderIcon,
  Close as CloseIcon
} from '@mui/icons-material';



const TabPanel = ({ children, value, index, ...other }) => (
  <div role="tabpanel" hidden={value !== index} {...other}>
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const FundersForm = ({ formData, updateFormData }) => {
  const theme = useTheme();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [funders, setFunders] = useState(formData?.funders || []);
  const [newFunder, setNewFunder] = useState({
    name: '',
    otherName: '',
    type: '',
    country: '',
    rorId: '',
    
  });
  const [isLoadingRor, setIsLoadingRor] = useState(false);
  const [showRorForm, setShowRorForm] = useState(false);
  const [rorError, setRorError] = useState('');

  const handleModalOpen = () => {
    setIsModalOpen(true);
    // Reset tab to "ROR ID" (index 0) for better UX
    setActiveTab(0);
    // Reset any form state and errors
    setNewFunder({
      name: '',
      otherName: '',
      type: '',
      country: '',
      rorId: '',
    });
    setRorError('');
    setShowRorForm(false);
    setIsLoadingRor(false);
  };
  const handleModalClose = () => {
    setIsModalOpen(false);
    setNewFunder({
      name: '',
      otherName: '',
      type: 'Funder',
      country: '',
      rorId: '',
      
    });
    setActiveTab(0);
    setRorError('');
    setShowRorForm(false);
    setIsLoadingRor(false);
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleInputChange = (field) => (event) => {
    setNewFunder({
      ...newFunder,
      [field]: event.target.value
    });
  };

  const handleAddFunder = () => {
    const updatedFunders = [...funders, newFunder];
    setFunders(updatedFunders);
    updateFormData({
      ...formData,
      funders: updatedFunders
    });
    handleModalClose();
  };

  const handleRemoveFunder = (index) => {
    const updatedFunders = funders.filter((_, i) => i !== index);
    setFunders(updatedFunders);
    updateFormData({
      ...formData,
      funders: updatedFunders
    });
  };

  const handleSearchRor = async () => {
    // Different validation and search logic based on active tab
    if (activeTab === 0) { // ROR ID tab
      if (!newFunder.rorId) {
        setRorError('ROR ID is required');
        return;
      }
      
      setIsLoadingRor(true);
      setRorError('');

      try {
        const response = await fetch(`/api/ror/get-ror-by-id/${encodeURIComponent(newFunder.rorId)}`);

        if (!response.ok) {
          throw new Error(`Failed to fetch ROR data: ${response.status}`);
        }

        const rorData = await response.json();
        
        if (rorData) {
          // Extract organization name (prefer ror_display, fallback to label)
          const orgName = rorData.names?.find(name => name.types?.includes('ror_display'))?.value || 
                         rorData.names?.find(name => name.types?.includes('label'))?.value || '';
          
          // Extract country from locations
          const country = rorData.locations?.[0]?.geonames_details?.country_name || '';
          
          // Extract organization type (first type)
          const orgType = rorData.types?.[0] || '';
          
          // Extract aliases
          const aliases = rorData.names?.filter(name => name.types?.includes('alias')).map(alias => alias.value) || [];
          const otherName = aliases.length > 0 ? aliases[0] : '';

          // Update the funder with ROR data
          setNewFunder(prev => ({
            ...prev,
            name: orgName,
            country: country,
            type: orgType,
            otherName: otherName
          }));
          
          setShowRorForm(true);
          setRorError('');
        } else {
          setRorError('No ROR record found for the provided ID');
        }
      } catch (error) {
        console.error('Error fetching ROR data:', error);
        setRorError(`Failed to fetch organization data: ${error.message}`);
      } finally {
        setIsLoadingRor(false);
      }
    } else { // ROR Details tab (index 1)
      if (!newFunder.name || !newFunder.country) {
        setRorError('Both Organization Name and Country are required');
        return;
      }
      
      setIsLoadingRor(true);
      setRorError('');

      try {
        // Trim and validate input values
        const orgName = newFunder.name.trim();
        const countryName = newFunder.country.trim();

        // Use separate parameters for name and country to leverage ROR's advanced query
        const response = await fetch(
          `/api/ror/search-organization?name=${encodeURIComponent(orgName)}&country=${encodeURIComponent(countryName)}&page=1`
        );

        if (!response.ok) {
          throw new Error('Failed to fetch ROR');
        }

        const data = await response.json();

        if (data && data.length > 0) {
          // Backend now handles country filtering via advanced query
          const { id, name: orgName, country, status, wikipedia_url } = data[0];

          setNewFunder(prev => ({
            ...prev,
            name: orgName || '',
            country: country || '',
            type: 'Funder',
            otherName: '',
            rorId: id || ''
          }));

          setShowRorForm(true);
        } else {
          setRorError('No ROR records found for the provided organization name and country');
        }
      } catch (error) {
        console.error('Error searching ROR data:', error);
        setRorError('Failed to retrieve ROR information. Please try again.');
      } finally {
        setIsLoadingRor(false);
      }
    }
  };

  const handleCancelRorForm = () => {
    setShowRorForm(false);
    setNewFunder({
      name: '',
      otherName: '',
      type: '',
      country: '',
      rorId: '',
      
    });
  };

  const renderFunderForm = () => (
    <Box>
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'flex-end', 
        mb: 2 
      }}>
        <IconButton
          onClick={handleCancelRorForm}
          sx={{ color: '#ef5350' }}
        >
          <CloseIcon />
        </IconButton>
      </Box>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Organization Name"
            value={newFunder.name}
            onChange={handleInputChange('name')}
            InputProps={{
              readOnly: true,
            }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="ROR ID"
            value={newFunder.rorId}
            InputProps={{
              readOnly: true,
            }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Country"
            value={newFunder.country}
            onChange={handleInputChange('country')}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Organization Type"
            value="Funder"
            InputProps={{
              readOnly: true,
            }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Other Organization Name"
            value={newFunder.otherName}
            onChange={handleInputChange('otherName')}
          />
        </Grid>
      </Grid>
      <Box sx={{ mt: 3 }}>
        <Button
          variant="contained"
          onClick={handleAddFunder}
          fullWidth
        >
          Add Funder
        </Button>
      </Box>
    </Box>
  );

  const GetRorButton = () => (
    <Button
      variant="outlined"
      onClick={() => window.open('https://ror.org/', '_blank')}
      fullWidth
      sx={{ 
        mt: 2,
        borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : theme.palette.divider,
        color: theme.palette.text.primary,
        '&:hover': {
          borderColor: theme.palette.primary.main,
          bgcolor: theme.palette.action.hover
        }
      }}
    >
      Get ROR ID
    </Button>
  );

  return (
    <Box>
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        mb: 2
      }}>
        <Typography 
          variant="h6" 
          sx={{ 
            color: theme.palette.text.primary,
            fontWeight: 600,
            fontSize: '1.25rem'
          }}
        >
          Funders
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleModalOpen}
          sx={{
            bgcolor: theme.palette.mode === 'dark' ? '#2e7d32' : '#4caf50',
            color: '#fff',
            '&:hover': { 
              bgcolor: theme.palette.mode === 'dark' ? '#1b5e20' : '#388e3c' 
            }
          }}
        >
          Add
        </Button>
      </Box>

      <Divider sx={{ mb: 3 }} />

      {formData.funders && formData.funders.length > 0 ? (
        <Box sx={{ width: '100%' }}>
          {formData.funders.map((funder, index) => (
            <Paper
              key={index}
              elevation={1}
              sx={{ 
                mb: 2, 
                borderRadius: 1,
                p: 3,
                position: 'relative',
                bgcolor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : theme.palette.divider}`
              }}
            >
              <Box sx={{ 
                mb: 3,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <Typography variant="h6" sx={{ color: theme.palette.primary.main }}>
                  Funder {index + 1}
                      </Typography>
                <IconButton 
                  onClick={() => handleRemoveFunder(index)}
                  sx={{ 
                    color: theme.palette.error.main,
                    '&:hover': {
                      bgcolor: theme.palette.action.hover
                    }
                  }}
                >
                  <DeleteIcon />
                </IconButton>
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Organization Name"
                    value={funder.name}
                    InputProps={{
                      readOnly: true,
                      sx: { 
                        bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
                      }
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : theme.palette.divider
                        }
                      }
                    }}
                  />
                </Grid>
                {funder.rorId && (
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="ROR ID"
                      value={funder.rorId}
                      InputProps={{
                        readOnly: true,
                        sx: { 
                          bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
                        }
                      }}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          '& fieldset': {
                            borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : theme.palette.divider
                          }
                        }
                      }}
                    />
                  </Grid>
                )}
                <Grid item xs={12} sm={funder.rorId ? 6 : 12}>
                  <TextField
                    fullWidth
                    label="Organization Type"
                    value={funder.type || 'N/A'}
                    InputProps={{
                      readOnly: true,
                      sx: { 
                        bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
                      }
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : theme.palette.divider
                        }
                      }
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Country"
                    value={funder.country || 'N/A'}
                    InputProps={{
                      readOnly: true,
                      sx: { 
                        bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
                      }
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : theme.palette.divider
                        }
                      }
                    }}
                  />
                </Grid>
                {funder.otherName && (
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Other Name"
                      value={funder.otherName}
                      InputProps={{
                        readOnly: true,
                        sx: { 
                          bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
                        }
                      }}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          '& fieldset': {
                            borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : theme.palette.divider
                          }
                        }
                      }}
                    />
                  </Grid>
                )}
              </Grid>
            </Paper>
          ))}
        </Box>
      ) : (
        <Typography variant="body2" sx={{ 
          textAlign: 'center', 
          py: 4,
          color: theme.palette.text.secondary 
        }}>
          No funders added yet
        </Typography>
      )}

      <Modal
        open={isModalOpen}
        onClose={handleModalClose}
      >
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '90%',
          maxWidth: 800,
          bgcolor: theme.palette.background.paper,
          borderRadius: 1,
          boxShadow: 24,
          overflow: 'hidden'
        }}>
          <Box sx={{ 
            bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.main,
            p: 2,
            color: theme.palette.common.white,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <Typography variant="h6" component="h2">
              Add Funder
            </Typography>
            <IconButton 
              onClick={handleModalClose}
              sx={{ color: theme.palette.common.white }}
            >
              <CloseIcon />
            </IconButton>
          </Box>

          <Box sx={{ p: 3 }}>
            <Tabs 
              value={activeTab} 
              onChange={handleTabChange} 
              sx={{ 
                mb: 3,
                '& .MuiTabs-flexContainer': {
                  display: 'flex',
                  justifyContent: 'space-between'
                }
              }}
              variant="fullWidth"
            >
              <Tab label="ROR ID" />
              <Tab label="ROR Details" />
            </Tabs>

            <TabPanel value={activeTab} index={0}>
              {!showRorForm ? (
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <TextField
                        sx={{ flex: 1 }}
                        label="Enter ROR ID"
                        value={newFunder.rorId}
                        onChange={handleInputChange('rorId')}
                        placeholder="https://ror.org/..."
                        error={Boolean(rorError)}
                        helperText={rorError}
                      />
                      <Button
                        variant="contained"
                        startIcon={isLoadingRor ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                        onClick={handleSearchRor}
                        disabled={isLoadingRor || !newFunder.rorId}
                        sx={{ minWidth: '150px' }}
                      >
                        {isLoadingRor ? 'Searching...' : 'Search ROR'}
                      </Button>
                    </Box>
                  </Grid>
                  <Grid item xs={12}>
                    <GetRorButton />
                  </Grid>
                </Grid>
              ) : (
                renderFunderForm()
              )}
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              {!showRorForm ? (
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <TextField
                        fullWidth
                        label="Organization Name"
                        value={newFunder.name}
                        onChange={handleInputChange('name')}
                        error={Boolean(rorError)}
                        helperText={rorError}
                        required
                      />
                      <TextField
                        fullWidth
                        label="Country"
                        value={newFunder.country}
                        onChange={handleInputChange('country')}
                        required
                      />
                      <Button
                        variant="contained"
                        startIcon={isLoadingRor ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                        onClick={handleSearchRor}
                        disabled={isLoadingRor || !newFunder.name || !newFunder.country}
                        sx={{ minWidth: '150px' }}
                      >
                        {isLoadingRor ? 'Searching...' : 'Search ROR'}
                      </Button>
                    </Box>
                  </Grid>
                  <Grid item xs={12}>
                    <GetRorButton />
                  </Grid>
                </Grid>
              ) : (
                renderFunderForm()
              )}
            </TabPanel>
          </Box>
        </Box>
      </Modal>
    </Box>
  );
};

export default FundersForm; 