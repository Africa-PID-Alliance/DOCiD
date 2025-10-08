"use client";

import React, { useState, useEffect } from 'react';
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
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import SearchIcon from '@mui/icons-material/Search';
import CloseIcon from '@mui/icons-material/Close';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

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

const GetOrcidButton = () => {
  const { t } = useTranslation();
  return (
    <Box sx={{ mt: 4, textAlign: 'center' }}>
      <Divider sx={{ mb: 3 }} />
      <Button
        variant="outlined"
        onClick={() => window.open('https://orcid.org/register', '_blank')}
        fullWidth
        sx={{
          borderWidth: 2,
          transition: 'all 0.3s ease-in-out',
          '&:hover': {
            borderWidth: 2,
            transform: 'translateY(-2px)',
            boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
            bgcolor: 'rgba(21, 101, 192, 0.04)'
          },
          display: 'flex',
          gap: 1,
          alignItems: 'center',
          justifyContent: 'center',
          py: 1.5
        }}
      >
        <Box
          component="img"
          src="https://info.orcid.org/wp-content/uploads/2019/11/orcid_16x16.png"
          sx={{
            width: 20,
            height: 20,
            transition: 'transform 0.3s ease-in-out',
            '.MuiButton-root:hover &': {
              transform: 'scale(1.1)'
            }
          }}
        />
        {t('assign_docid.creators_form.modal.get_orcid')}
      </Button>
    </Box>
  );
};

const CreatorsForm = ({ formData, updateFormData }) => {
  const theme = useTheme();
  const { t } = useTranslation();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [creators, setCreators] = useState(formData?.creators || []);
  const [creatorRoles, setCreatorRoles] = useState([]);
  const [isLoadingRoles, setIsLoadingRoles] = useState(true);
  const [roleError, setRoleError] = useState('');
  const [newCreator, setNewCreator] = useState({
    givenName: '',
    familyName: '',
    affiliation: '',
    role: '',
    role_name: '',
    orcidId: '',
    otherName: ''
  });
  const [isLoadingOrcid, setIsLoadingOrcid] = useState(false);
  const [showOrcidForm, setShowOrcidForm] = useState(false);
  const [orcidError, setOrcidError] = useState('');
  const [identifierTypes] = useState([
    { id: 'orcid', name: 'ORCID' },
    { id: 'researcher', name: 'Researcher ID' },
    { id: 'scopus', name: 'Scopus ID' },
    { id: 'openalex', name: 'Open Alex Author ID' }
  ]);

  // Fetch creator roles
  useEffect(() => {
    const fetchCreatorRoles = async () => {
      try {
        const response = await axios.get('/api/publications/get-list-creators-roles');
        
        setCreatorRoles(response.data);
      } catch (error) {
        console.error('Error fetching creator roles:', error);
      } finally {
        setIsLoadingRoles(false);
      }
    };
    fetchCreatorRoles();
  }, []);

  const handleModalOpen = () => {
    setIsModalOpen(true);
    // Reset tab to "ORCID ID" (index 0) for better UX
    setActiveTab(0);
    // Reset any form state and errors
    setNewCreator({
      givenName: '',
      familyName: '',
      affiliation: '',
      role: '',
      role_name: '',
      orcidId: '',
      otherName: ''
    });
    setOrcidError('');
    setRoleError('');
    setShowOrcidForm(false);
    setIsLoadingOrcid(false);
  };
  const handleModalClose = () => {
    setIsModalOpen(false);
    setNewCreator({
      givenName: '',
      familyName: '',
      affiliation: '',
      role: '',
      role_name: '',
      orcidId: '',
      otherName: ''
    });
    setActiveTab(0);
    setOrcidError('');
    setRoleError('');
    setShowOrcidForm(false);
    setIsLoadingOrcid(false);
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleInputChange = (field) => (event) => {
    if (field === 'role') {
      const selectedRole = creatorRoles.find(role => role.role_id === event.target.value);
      setNewCreator({
        ...newCreator,
        role: event.target.value,
        role_name: selectedRole ? selectedRole.role_name : ''
      });
      setRoleError('');
    } else {
      setNewCreator({
        ...newCreator,
        [field]: event.target.value
      });
    }
  };

  const handleAddCreator = () => {
    if (!newCreator.role) {
      setRoleError(t('assign_docid.creators_form.modal.errors.role_required'));
      return;
    }
    setRoleError('');
    const updatedCreators = [...creators, newCreator];
    setCreators(updatedCreators);
    updateFormData({
      ...formData,
      creators: updatedCreators
    });
    handleModalClose();
  };

  const handleRemoveCreator = (index) => {
    const updatedCreators = creators.filter((_, i) => i !== index);
    setCreators(updatedCreators);
    updateFormData({
      ...formData,
      creators: updatedCreators
    });
  };

  const handleSearchOrcid = async () => {
    // Different validation and search logic based on active tab
    if (activeTab === 0) { // ORCID ID tab
      if (!newCreator.orcidId) {
        setOrcidError(t('assign_docid.creators_form.modal.errors.orcid_required'));
        return;
      }
    
    setIsLoadingOrcid(true);
    setOrcidError('');

    try {
        const response = await fetch(`/api/orcid/get-orcid/${encodeURIComponent(newCreator.orcidId)}`);

        if (!response.ok) {
          throw new Error('Failed to fetch ORCID');
        }

        const data = await response.json();
        
        if (data) {
      setNewCreator(prev => ({
        ...prev,
            givenName: data.name?.['given-names']?.value || '',
            familyName: data.name?.['family-name']?.value || '',
            affiliation: data.institution?.[0] || 'No institution found',
        orcidId: newCreator.orcidId,
        identifier_type: 'orcid'
      }));
      
      setShowOrcidForm(true);
        } else {
          setOrcidError(t('assign_docid.creators_form.modal.errors.no_orcid_found'));
        }
    } catch (error) {
      console.error('Error fetching ORCID data:', error);
        setOrcidError(t('assign_docid.creators_form.modal.errors.failed_fetch_orcid'));
      } finally {
        setIsLoadingOrcid(false);
      }
    } else { // ORCID Details tab (index 1)
      if (!newCreator.givenName) {
        setOrcidError(t('assign_docid.creators_form.modal.errors.first_name_required'));
        return;
      }
      if (!newCreator.familyName) {
        setOrcidError(t('assign_docid.creators_form.modal.errors.family_name_required'));
        return;
      }
      
      setIsLoadingOrcid(true);
      setOrcidError('');

      try {
        // Construct the base URL with required parameters
        let url = `/api/orcid/search-orcid?first_name=${encodeURIComponent(
          newCreator.givenName
        )}&last_name=${encodeURIComponent(newCreator.familyName)}`;

        // Add affiliation if provided
        if (newCreator.affiliation) {
          url += `&affiliations=${encodeURIComponent(newCreator.affiliation)}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
          throw new Error('Failed to fetch ORCID');
        }

        const data = await response.json();
        const { "expanded-result": results } = data;

        if (results && results.length > 0) {
          const {
            "given-names": givenNames,
            "family-names": familyNames,
            "institution-name": institutionName,
            "orcid-id": orcidId,
          } = results[0];

          setNewCreator(prev => ({
            ...prev,
            givenName: givenNames,
            familyName: familyNames,
            affiliation: institutionName?.[0] || prev.affiliation || 'No institution found',
            orcidId: orcidId,
            identifier_type: 'orcid'
          }));

          setShowOrcidForm(true);
        } else {
          setOrcidError(t('assign_docid.creators_form.modal.errors.no_orcid_records'));
        }
      } catch (error) {
        console.error('Error searching ORCID data:', error);
        setOrcidError(t('assign_docid.creators_form.modal.errors.failed_fetch_orcid'));
    } finally {
      setIsLoadingOrcid(false);
      }
    }
  };

  const handleCancelOrcidForm = () => {
    setShowOrcidForm(false);
    setNewCreator({
      givenName: '',
      familyName: '',
      affiliation: '',
      role: '',
      role_name: '',
      orcidId: '',
      otherName: ''
    });
  };

  const renderCreatorForm = () => (
    <Box>
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'flex-end', 
        mb: 2 
      }}>
        <IconButton
          onClick={handleCancelOrcidForm}
          sx={{ color: '#ef5350' }}
        >
          <CloseIcon />
        </IconButton>
      </Box>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label={t('assign_docid.creators_form.full_name')}
            value={`${newCreator.givenName} ${newCreator.familyName}`}
            InputProps={{
              readOnly: true,
            }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label={t('assign_docid.creators_form.modal.family_name')}
            value={newCreator.familyName}
            onChange={handleInputChange('familyName')}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label={t('assign_docid.creators_form.modal.given_name')}
            value={newCreator.givenName}
            onChange={handleInputChange('givenName')}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="ORCID"
            value={newCreator.orcidId}
            InputProps={{
              readOnly: true,
            }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <FormControl fullWidth>
            <InputLabel>{t('assign_docid.creators_form.identifier_type')}</InputLabel>
            <Select
              value="orcid"
              label={t('assign_docid.creators_form.identifier_type')}
              disabled
            >
              {identifierTypes.map((type) => (
                <MenuItem key={type.id} value={type.id}>
                  {type.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Affiliation"
            value={newCreator.affiliation}
            onChange={handleInputChange('affiliation')}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <FormControl fullWidth error={!!roleError}>
            <InputLabel>{t('assign_docid.creators_form.role_required')}</InputLabel>
            <Select
              value={newCreator.role}
              onChange={handleInputChange('role')}
              label={t('assign_docid.creators_form.role_required')}
              disabled={isLoadingRoles}
            >
              {isLoadingRoles ? (
                <MenuItem disabled>
                  <CircularProgress size={20} sx={{ mr: 1 }} />
                  {t('assign_docid.creators_form.modal.loading_roles')}
                </MenuItem>
              ) : (
                creatorRoles.map((role) => (
                  <MenuItem key={role.role_id} value={role.role_id}>
                    {role.role_name}
                  </MenuItem>
                ))
              )}
            </Select>
            {roleError && (
              <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                {roleError}
              </Typography>
            )}
          </FormControl>
        </Grid>
      </Grid>
      <Box sx={{ mt: 3 }}>
        <Button
          variant="contained"
          onClick={handleAddCreator}
          fullWidth
          disabled={!newCreator.role}
        >
          {t('assign_docid.creators_form.modal.add_creator_title')}
        </Button>
      </Box>
    </Box>
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
          {t('assign_docid.creators_form.title')}
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
          {t('assign_docid.creators_form.add')}
        </Button>
      </Box>

      <Divider sx={{ mb: 3 }} />

      {/* Creators List */}
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
                  {t('assign_docid.creators_form.creator_number', { number: index + 1 })}
                </Typography>
                <IconButton 
                  onClick={() => handleRemoveCreator(index)}
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
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label={t('assign_docid.creators_form.modal.given_name')}
                    value={creator.givenName}
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
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label={t('assign_docid.creators_form.modal.family_name')}
                    value={creator.familyName}
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
                {creator.orcidId && (
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="ORCID ID"
                      value={creator.orcidId}
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
                )}
                <Grid item xs={12} sm={creator.orcidId ? 6 : 12}>
                  <TextField
                    fullWidth
                    label={t('assign_docid.creators_form.modal.affiliation')}
                    value={creator.affiliation || 'N/A'}
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
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <TextField
                      label={t('assign_docid.creators_form.modal.role')}
                      value={creator.role_name}
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
                  </FormControl>
                </Grid>
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
          {t('assign_docid.creators_form.no_creators')}
        </Typography>
      )}

      {/* Add Creator Modal */}
      <Modal
        open={isModalOpen}
        onClose={handleModalClose}
        aria-labelledby="add-creator-modal"
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
              {t('assign_docid.creators_form.modal.add_creator_title')}
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
              <Tab label={t('assign_docid.creators_form.orcid_id_tab')} />
              <Tab label={t('assign_docid.creators_form.orcid_details_tab')} />
            </Tabs>

            {/* ORCID ID Tab */}
            <TabPanel value={activeTab} index={0}>
              {!showOrcidForm ? (
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <TextField
                        sx={{ flex: 1 }}
                        label={t('assign_docid.creators_form.enter_orcid_id')}
                        value={newCreator.orcidId}
                        onChange={handleInputChange('orcidId')}
                        placeholder="0000-0000-0000-0000"
                        error={Boolean(orcidError)}
                        helperText={orcidError}
                      />
                      <Button
                        variant="contained"
                        startIcon={isLoadingOrcid ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                        onClick={handleSearchOrcid}
                        disabled={isLoadingOrcid || !newCreator.orcidId}
                        sx={{ minWidth: '150px' }}
                      >
                        {isLoadingOrcid ? t('assign_docid.creators_form.modal.searching') : t('assign_docid.creators_form.modal.search_orcid')}
                      </Button>
                    </Box>
                  </Grid>
                  <Grid item xs={12}>
                    <GetOrcidButton />
                  </Grid>
                </Grid>
              ) : (
                renderCreatorForm()
              )}
            </TabPanel>

            {/* ORCID Details Tab */}
            <TabPanel value={activeTab} index={1}>
              {!showOrcidForm ? (
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label={t('assign_docid.creators_form.modal.given_name')}
                      value={newCreator.givenName}
                      onChange={handleInputChange('givenName')}
                      required
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label={t('assign_docid.creators_form.modal.family_name')}
                      value={newCreator.familyName}
                      onChange={handleInputChange('familyName')}
                      required
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label={t('assign_docid.creators_form.modal.affiliation')}
                      value={newCreator.affiliation}
                      onChange={handleInputChange('affiliation')}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label={t('assign_docid.creators_form.other_name')}
                      value={newCreator.otherName}
                      onChange={handleInputChange('otherName')}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Button
                      variant="contained"
                      startIcon={isLoadingOrcid ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                      onClick={handleSearchOrcid}
                      disabled={isLoadingOrcid || (!newCreator.givenName && !newCreator.familyName)}
                      fullWidth
                    >
                      {isLoadingOrcid ? t('assign_docid.creators_form.modal.searching') : t('assign_docid.creators_form.modal.search_orcid')}
                    </Button>
                    {orcidError && (
                      <Typography color="error" variant="caption" sx={{ mt: 1, display: 'block' }}>
                        {orcidError}
                    </Typography>
                    )}
                  </Grid>
                </Grid>
              ) : (
                <Box>
                  <Box sx={{ 
                    display: 'flex', 
                    justifyContent: 'flex-end', 
                    mb: 2 
                  }}>
                    <IconButton
                      onClick={handleCancelOrcidForm}
                      sx={{ color: '#ef5350' }}
                    >
                      <CloseIcon />
                    </IconButton>
                  </Box>
                  <Grid container spacing={3}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label={t('assign_docid.creators_form.full_name')}
                        value={`${newCreator.givenName} ${newCreator.familyName}`}
                        InputProps={{
                          readOnly: true,
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label={t('assign_docid.creators_form.modal.family_name')}
                        value={newCreator.familyName}
                        InputProps={{
                          readOnly: true,
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label={t('assign_docid.creators_form.modal.given_name')}
                        value={newCreator.givenName}
                        InputProps={{
                          readOnly: true,
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="ORCID"
                        value={newCreator.orcidId}
                        InputProps={{
                          readOnly: true,
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>{t('assign_docid.creators_form.identifier_type')}</InputLabel>
                        <Select
                          value="orcid"
                          label={t('assign_docid.creators_form.identifier_type')}
                          disabled
                        >
                          {identifierTypes.map((type) => (
                            <MenuItem key={type.id} value={type.id}>
                              {type.name}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label={t('assign_docid.creators_form.modal.affiliation')}
                        value={newCreator.affiliation}
                        onChange={handleInputChange('affiliation')}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth error={!!roleError}>
                        <InputLabel>{t('assign_docid.creators_form.role_required')}</InputLabel>
                        <Select
                          value={newCreator.role}
                          onChange={handleInputChange('role')}
                          label={t('assign_docid.creators_form.role_required')}
                          disabled={isLoadingRoles}
                        >
                          {isLoadingRoles ? (
                            <MenuItem disabled>
                              <CircularProgress size={20} sx={{ mr: 1 }} />
                              {t('assign_docid.creators_form.modal.loading_roles')}
                            </MenuItem>
                          ) : (
                            creatorRoles.map((role) => (
                              <MenuItem key={role.role_id} value={role.role_id}>
                                {role.role_name}
                              </MenuItem>
                            ))
                          )}
                        </Select>
                        {roleError && (
                          <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                            {roleError}
                          </Typography>
                        )}
                      </FormControl>
                    </Grid>
                  </Grid>
                  <Box sx={{ mt: 3 }}>
                    <Button
                      variant="contained"
                      onClick={handleAddCreator}
                      fullWidth
                      disabled={!newCreator.role}
                    >
                      {t('assign_docid.creators_form.modal.add_creator_title')}
                    </Button>
                  </Box>
                </Box>
              )}
              {!showOrcidForm && <GetOrcidButton />}
            </TabPanel>
          </Box>
        </Box>
      </Modal>
    </Box>
  );
};

export default CreatorsForm; 