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
  Business as BusinessIcon,
  Close as CloseIcon
} from '@mui/icons-material';

const organizationRoles = [
  'Lead Institution',
  'Partner Institution',
  'Funding Institution',
  'Research Center',
  'Department'
];

const TabPanel = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    {...other}
  >
    {value === index && (
      <Box sx={{ p: 3 }}>
        {children}
      </Box>
    )}
  </div>
);

const OrganizationsForm = ({ formData, updateFormData }) => {
  const theme = useTheme();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [organizations, setOrganizations] = useState(formData?.organizations || []);
  const [newOrganization, setNewOrganization] = useState({
    name: '',
    otherName: '',
    type: '',
    country: '',
    department: '',
    role: '',
    rorId: '',
    city: '',
    website: ''
  });
  const [isLoadingRor, setIsLoadingRor] = useState(false);
  const [showRorForm, setShowRorForm] = useState(false);
  const [rorError, setRorError] = useState('');

  const handleModalOpen = () => {
    setIsModalOpen(true);
    // Reset tab to "ROR ID" (index 0) for better UX
    setActiveTab(0);
    // Reset any form state and errors
    setNewOrganization({
      name: '',
      otherName: '',
      type: '',
      country: '',
      department: '',
      role: '',
      rorId: '',
      city: '',
      website: ''
    });
    setRorError('');
    setShowRorForm(false);
    setIsLoadingRor(false);
  };
  const handleModalClose = () => {
    setIsModalOpen(false);
    setNewOrganization({
      name: '',
      otherName: '',
      type: '',
      country: '',
      department: '',
      role: '',
      rorId: '',
      city: '',
      website: ''
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
    setNewOrganization({
      ...newOrganization,
      [field]: event.target.value
    });
  };

  const handleAddOrganization = () => {
    const updatedOrganizations = [...organizations, newOrganization];
    setOrganizations(updatedOrganizations);
    updateFormData({
      ...formData,
      organizations: updatedOrganizations
    });
    handleModalClose();
  };

  const handleRemoveOrganization = (index) => {
    const updatedOrganizations = organizations.filter((_, i) => i !== index);
    setOrganizations(updatedOrganizations);
    updateFormData({
      ...formData,
      organizations: updatedOrganizations
    });
  };

  const handleSearchRor = async () => {
    // Different validation and search logic based on active tab
    if (activeTab === 0) { // ROR ID tab
      if (!newOrganization.rorId) {
        setRorError('ROR ID is required');
        return;
      }
      
      setIsLoadingRor(true);
      setRorError('');

      try {
        const response = await fetch(`/api/ror/get-ror-by-id/${encodeURIComponent(newOrganization.rorId)}`);

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

          setNewOrganization(prev => ({
            ...prev,
            name: orgName,
            country: country,
            type: orgType,
            otherName: otherName,
            rorId: newOrganization.rorId
          }));
          
          setShowRorForm(true);
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
      if (!newOrganization.name || !newOrganization.country) {
        setRorError('Both Organization Name and Country are required');
        return;
      }
      
      setIsLoadingRor(true);
      setRorError('');

      try {
        // Trim and validate input values
        const orgName = newOrganization.name.trim();
        const countryName = newOrganization.country.trim();

        // Use separate parameters for name and country to leverage ROR's advanced query
        const searchUrl = `/api/ror/search-organization?name=${encodeURIComponent(orgName)}&country=${encodeURIComponent(countryName)}&page=1`;

        // Log search parameters
        console.log('Search Parameters:', {
          organizationName: orgName,
          country: countryName,
          fullUrl: searchUrl
        });

        const response = await fetch(searchUrl);

        if (!response.ok) {
          throw new Error('Failed to fetch ROR');
        }

        const data = await response.json();

        // Log the full response data
        console.log('ROR Search Response:', {
          totalResults: data.length,
          fullData: data
        });

        if (data && data.length > 0) {
          // Backend now handles country filtering via advanced query
          const matchingOrg = data[0];
          console.log('Found matching organization:', matchingOrg);

          const { id, name: orgName, country, status, wikipedia_url } = matchingOrg;

          setNewOrganization(prev => ({
            ...prev,
            name: orgName || '',
            country: country || '',
            type: '',
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
    setNewOrganization({
      name: '',
      otherName: '',
      type: '',
      country: '',
      department: '',
      role: '',
      rorId: '',
      city: '',
      website: ''
    });
  };

  const renderOrganizationForm = () => (
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
            value={newOrganization.name}
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
            value={newOrganization.rorId}
            InputProps={{
              readOnly: true,
            }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Country"
            value={newOrganization.country}
            onChange={handleInputChange('country')}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Organization Type"
            value={newOrganization.type}
            onChange={handleInputChange('type')}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Other Organization Name"
            value={newOrganization.otherName}
            onChange={handleInputChange('otherName')}
          />
        </Grid>
      </Grid>
      <Box sx={{ mt: 3 }}>
        <Button
          variant="contained"
          onClick={handleAddOrganization}
          fullWidth
        >
          Add Organization
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
        borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider,
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
          Organizations
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

      <Divider sx={{ mb: 3, bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider }} />

      {/* Organizations List */}
      {formData.organizations && formData.organizations.length > 0 ? (
        <Box sx={{ width: '100%' }}>
          {formData.organizations.map((organization, index) => (
            <Paper
              key={index}
              elevation={1}
              sx={{ 
                mb: 2, 
                borderRadius: 1,
                p: 3,
                position: 'relative',
                bgcolor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider}`
              }}
            >
              <Box sx={{ 
                mb: 3,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <Typography variant="h6" sx={{ color: theme.palette.primary.main }}>
                  Organization {index + 1}
                </Typography>
                <IconButton 
                  onClick={() => handleRemoveOrganization(index)}
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
                    value={organization.name}
                    InputProps={{
                      readOnly: true,
                      sx: { 
                        bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
                      }
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider
                        }
                      }
                    }}
                  />
                </Grid>
                {organization.rorId && (
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="ROR ID"
                      value={organization.rorId}
                      InputProps={{
                        readOnly: true,
                        sx: { 
                          bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
                        }
                      }}
                    />
                  </Grid>
                )}
                <Grid item xs={12} sm={organization.rorId ? 6 : 12}>
                  <TextField
                    fullWidth
                    label="Organization Type"
                    value={organization.type || 'N/A'}
                    InputProps={{
                      readOnly: true,
                      sx: { 
                        bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
                      }
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Country"
                    value={organization.country || 'N/A'}
                    InputProps={{
                      readOnly: true,
                      sx: { 
                        bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
                      }
                    }}
                  />
                </Grid>
                {organization.otherName && (
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Other Name"
                      value={organization.otherName}
                      InputProps={{
                        readOnly: true,
                        sx: { 
                          bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
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
          No organizations added yet
        </Typography>
      )}

      {/* Add Organization Modal */}
      <Modal
        open={isModalOpen}
        onClose={handleModalClose}
        aria-labelledby="add-organization-modal"
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
            color: '#fff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <Typography variant="h6" component="h2">
              Add Organization
            </Typography>
            <IconButton 
              onClick={handleModalClose}
              sx={{ color: '#fff' }}
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

            {/* ROR ID Tab */}
            <TabPanel value={activeTab} index={0}>
              {!showRorForm ? (
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField
                      sx={{ flex: 1 }}
                      label="Enter ROR ID"
                      value={newOrganization.rorId}
                      onChange={handleInputChange('rorId')}
                      placeholder="ROR ID"
                        error={Boolean(rorError)}
                        helperText={rorError}
                    />
                    <Button
                      variant="contained"
                        startIcon={isLoadingRor ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                        onClick={handleSearchRor}
                        disabled={isLoadingRor || !newOrganization.rorId}
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
                renderOrganizationForm()
              )}
            </TabPanel>

            {/* ROR Details Tab */}
            <TabPanel value={activeTab} index={1}>
              {!showRorForm ? (
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      fullWidth
                      label="Organization Name"
                      value={newOrganization.name}
                      onChange={handleInputChange('name')}
                      error={Boolean(rorError)}
                      helperText={rorError}
                      required
                    />
                    <TextField
                      fullWidth
                      label="Country"
                      value={newOrganization.country}
                      onChange={handleInputChange('country')}
                      placeholder="e.g., Kenya, South Africa, United States"
                      helperText="Enter the full country name (e.g., Kenya, South Africa)"
                      required
                    />
                    <Button
                      variant="contained"
                      startIcon={isLoadingRor ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                      onClick={handleSearchRor}
                      disabled={isLoadingRor || !newOrganization.name || !newOrganization.country}
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
                renderOrganizationForm()
              )}
            </TabPanel>
          </Box>
        </Box>
      </Modal>
    </Box>
  );
};

export default OrganizationsForm; 