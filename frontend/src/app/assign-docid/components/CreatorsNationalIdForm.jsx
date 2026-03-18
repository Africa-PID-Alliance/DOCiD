"use client";

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Modal,
  TextField,
  IconButton,
  Paper,
  Grid,
  Divider,
  useTheme,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemButton
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';
import axios from 'axios';

const CreatorsNationalIdForm = ({ formData = { creators: [] }, updateFormData }) => {
  const theme = useTheme();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [creators, setCreators] = useState(formData?.creators || []);
  const [newCreator, setNewCreator] = useState({
    name: '',
    nationalIdNumber: '',
    country: ''
  });
  const [errors, setErrors] = useState({});

  // Search/lookup state
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [lookupId, setLookupId] = useState('');
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState('');

  const handleModalOpen = () => {
    setIsModalOpen(true);
    setNewCreator({ name: '', nationalIdNumber: '', country: '' });
    setErrors({});
    setActiveTab(0);
    setSearchQuery('');
    setSearchResults([]);
    setSearchError('');
    setLookupId('');
    setLookupError('');
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setNewCreator({ name: '', nationalIdNumber: '', country: '' });
    setErrors({});
    setSearchResults([]);
    setSearchError('');
    setLookupError('');
  };

  const handleInputChange = (field) => (event) => {
    setNewCreator((prev) => ({ ...prev, [field]: event.target.value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!newCreator.name.trim()) newErrors.name = 'Name is required';
    if (!newCreator.nationalIdNumber.trim()) newErrors.nationalIdNumber = 'National ID Number is required';
    if (!newCreator.country.trim()) newErrors.country = 'Country is required';
    return newErrors;
  };

  const handleAddCreator = () => {
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    const updatedCreators = [...creators, newCreator];
    setCreators(updatedCreators);
    updateFormData({ ...formData, creators: updatedCreators });
    handleModalClose();
  };

  const handleRemoveCreator = (index) => {
    const updatedCreators = creators.filter((_, i) => i !== index);
    setCreators(updatedCreators);
    updateFormData({ ...formData, creators: updatedCreators });
  };

  // Lookup by National ID Number
  const handleLookup = async () => {
    if (!lookupId.trim()) {
      setLookupError('Please enter a National ID or Passport Number');
      return;
    }
    setLookupLoading(true);
    setLookupError('');
    setSearchResults([]);

    try {
      const response = await axios.get(`/api/national-id/lookup/${encodeURIComponent(lookupId.trim())}`);
      const data = response.data;

      if (data.results && data.results.length > 0) {
        setSearchResults(data.results);
      } else {
        setLookupError('No researcher found with this ID. You can add them manually below.');
        setNewCreator((prev) => ({ ...prev, nationalIdNumber: lookupId.trim() }));
        setActiveTab(1);
      }
    } catch (error) {
      console.error('Lookup error:', error);
      setLookupError('Failed to lookup researcher. You can add them manually.');
    } finally {
      setLookupLoading(false);
    }
  };

  // Search by name
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchError('Please enter a search term');
      return;
    }
    setSearchLoading(true);
    setSearchError('');
    setSearchResults([]);

    try {
      const response = await axios.get(`/api/national-id/search?q=${encodeURIComponent(searchQuery.trim())}`);
      const data = response.data;

      if (data.results && data.results.length > 0) {
        setSearchResults(data.results);
      } else {
        setSearchError('No researchers found. You can add a new one manually below.');
      }
    } catch (error) {
      console.error('Search error:', error);
      setSearchError('Failed to search researchers.');
    } finally {
      setSearchLoading(false);
    }
  };

  // Select a researcher from search results
  const handleSelectResearcher = (researcher) => {
    setNewCreator({
      name: researcher.name,
      nationalIdNumber: researcher.national_id_number,
      country: researcher.country
    });
    setSearchResults([]);
    setActiveTab(1);
  };

  const readOnlyInputSx = {
    bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
  };

  const readOnlyFieldSx = {
    '& .MuiOutlinedInput-root': {
      '& fieldset': {
        borderColor:
          theme.palette.mode === 'dark'
            ? 'rgba(255, 255, 255, 0.23)'
            : theme.palette.divider
      }
    }
  };

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2
        }}
      >
        <Typography
          variant="h6"
          sx={{
            color: theme.palette.text.primary,
            fontWeight: 600,
            fontSize: '1.25rem'
          }}
        >
          Creators (National ID)
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

      {creators && creators.length > 0 ? (
        <Box sx={{ width: '100%' }}>
          {creators.map((creator, index) => (
            <Paper
              key={index}
              elevation={1}
              sx={{
                mb: 2,
                borderRadius: 1,
                p: 3,
                position: 'relative',
                bgcolor: theme.palette.background.paper,
                border: `1px solid ${
                  theme.palette.mode === 'dark'
                    ? 'rgba(255, 255, 255, 0.23)'
                    : theme.palette.divider
                }`
              }}
            >
              <Box
                sx={{
                  mb: 3,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <Typography variant="h6" sx={{ color: theme.palette.primary.main }}>
                  Creator {index + 1}
                </Typography>
                <IconButton
                  onClick={() => handleRemoveCreator(index)}
                  sx={{
                    color: theme.palette.error.main,
                    '&:hover': { bgcolor: theme.palette.action.hover }
                  }}
                >
                  <DeleteIcon />
                </IconButton>
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Name"
                    value={creator.name}
                    InputProps={{ readOnly: true, sx: readOnlyInputSx }}
                    sx={readOnlyFieldSx}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="National ID Number"
                    value={creator.nationalIdNumber}
                    InputProps={{ readOnly: true, sx: readOnlyInputSx }}
                    sx={readOnlyFieldSx}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Country"
                    value={creator.country}
                    InputProps={{ readOnly: true, sx: readOnlyInputSx }}
                    sx={readOnlyFieldSx}
                  />
                </Grid>
              </Grid>
            </Paper>
          ))}
        </Box>
      ) : (
        <Typography
          variant="body2"
          sx={{ textAlign: 'center', py: 4, color: theme.palette.text.secondary }}
        >
          No creators added yet
        </Typography>
      )}

      {/* Add Creator Modal */}
      <Modal open={isModalOpen} onClose={handleModalClose} aria-labelledby="add-national-id-creator-modal">
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '90%',
            maxWidth: 650,
            maxHeight: '90vh',
            bgcolor: theme.palette.background.paper,
            borderRadius: 1,
            boxShadow: 24,
            overflow: 'auto'
          }}
        >
          <Box
            sx={{
              bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.main,
              p: 2,
              color: '#fff',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <Typography variant="h6" component="h2">
              Add Creator (National ID)
            </Typography>
            <IconButton onClick={handleModalClose} sx={{ color: '#fff' }}>
              <CloseIcon />
            </IconButton>
          </Box>

          <Box sx={{ px: 3, pt: 2 }}>
            <Tabs
              value={activeTab}
              onChange={(event, newTabValue) => {
                setActiveTab(newTabValue);
                setSearchResults([]);
                setSearchError('');
                setLookupError('');
              }}
              sx={{ mb: 2 }}
            >
              <Tab label="Lookup by ID" />
              <Tab label="Manual Entry" />
            </Tabs>

            {/* Tab 0: Lookup by National ID */}
            {activeTab === 0 && (
              <Box>
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={12} sm={8}>
                    <TextField
                      fullWidth
                      label="National ID or Passport Number"
                      value={lookupId}
                      onChange={(event) => {
                        setLookupId(event.target.value);
                        setLookupError('');
                      }}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter') handleLookup();
                      }}
                      placeholder="Enter National ID or Passport Number"
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <Button
                      variant="contained"
                      onClick={handleLookup}
                      disabled={lookupLoading}
                      fullWidth
                      sx={{ height: '56px' }}
                      startIcon={lookupLoading ? <CircularProgress size={20} /> : <SearchIcon />}
                    >
                      {lookupLoading ? 'Looking up...' : 'Lookup'}
                    </Button>
                  </Grid>
                </Grid>

                <Divider sx={{ my: 1 }}>or search by name</Divider>

                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={12} sm={8}>
                    <TextField
                      fullWidth
                      label="Search by Name"
                      value={searchQuery}
                      onChange={(event) => {
                        setSearchQuery(event.target.value);
                        setSearchError('');
                      }}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter') handleSearch();
                      }}
                      placeholder="Enter researcher name"
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <Button
                      variant="outlined"
                      onClick={handleSearch}
                      disabled={searchLoading}
                      fullWidth
                      sx={{ height: '56px' }}
                      startIcon={searchLoading ? <CircularProgress size={20} /> : <SearchIcon />}
                    >
                      {searchLoading ? 'Searching...' : 'Search'}
                    </Button>
                  </Grid>
                </Grid>

                {lookupError && (
                  <Alert severity="info" sx={{ mb: 2 }}>{lookupError}</Alert>
                )}

                {searchError && (
                  <Alert severity="info" sx={{ mb: 2 }}>{searchError}</Alert>
                )}

                {/* Search Results */}
                {searchResults.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, color: theme.palette.text.secondary }}>
                      Select a researcher ({searchResults.length} found):
                    </Typography>
                    <Paper variant="outlined" sx={{ maxHeight: 250, overflow: 'auto' }}>
                      <List disablePadding>
                        {searchResults.map((researcher, resultIndex) => (
                          <ListItem key={researcher.id || resultIndex} disablePadding divider>
                            <ListItemButton onClick={() => handleSelectResearcher(researcher)}>
                              <ListItemText
                                primary={researcher.name}
                                secondary={`ID: ${researcher.national_id_number} | Country: ${researcher.country}`}
                              />
                            </ListItemButton>
                          </ListItem>
                        ))}
                      </List>
                    </Paper>
                  </Box>
                )}

                <Button
                  variant="text"
                  onClick={() => setActiveTab(1)}
                  sx={{ mb: 2 }}
                >
                  Not found? Add manually →
                </Button>
              </Box>
            )}

            {/* Tab 1: Manual Entry */}
            {activeTab === 1 && (
              <Box sx={{ pb: 3 }}>
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Name"
                      value={newCreator.name}
                      onChange={handleInputChange('name')}
                      required
                      error={!!errors.name}
                      helperText={errors.name}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="National ID Number"
                      value={newCreator.nationalIdNumber}
                      onChange={handleInputChange('nationalIdNumber')}
                      required
                      error={!!errors.nationalIdNumber}
                      helperText={errors.nationalIdNumber}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Country"
                      value={newCreator.country}
                      onChange={handleInputChange('country')}
                      required
                      error={!!errors.country}
                      helperText={errors.country}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Button
                      variant="contained"
                      onClick={handleAddCreator}
                      fullWidth
                      sx={{ mt: 1 }}
                    >
                      Add Creator
                    </Button>
                  </Grid>
                </Grid>
              </Box>
            )}
          </Box>
        </Box>
      </Modal>
    </Box>
  );
};

export default CreatorsNationalIdForm;
