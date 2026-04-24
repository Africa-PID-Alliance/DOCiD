"use client";

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Modal,
  TextField,
  Paper,
  CircularProgress,
  Alert,
  List,
  ListItem,
  IconButton,
  Grid,
  Divider,
  Tabs,
  Tab,
  useTheme
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Work as ProjectIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const ProjectForm = ({ formData, updateFormData }) => {
  const theme = useTheme();
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [raidId, setRaidId] = useState('');
  const [currentProject, setCurrentProject] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const [manualProject, setManualProject] = useState({
    title: '',
    description: '',
    institution: '',
    startDate: '',
    endDate: ''
  });

  const handleModalOpen = () => {
    setOpen(true);
    setRaidId('');
    setCurrentProject(null);
    setError('');
  };

  const handleModalClose = () => {
    setOpen(false);
    setRaidId('');
    setCurrentProject(null);
    setError('');
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    setRaidId('');
    setCurrentProject(null);
    setError('');
  };

  const handleRaidIdChange = (event) => {
    setRaidId(event.target.value);
    setError('');
  };

  const handleFindProject = async () => {
    setIsSearching(true);
    setError('');

    if (!raidId.trim()) {
      setError(t('assign_docid.projects_form.errors.raid_id_required'));
      setIsSearching(false);
      return;
    }

    try {
      const response = await axios.get(
        `/api/raid/get-raid?raid_url=${encodeURIComponent(raidId)}`,
        {
          headers: {
            'Accept': 'application/json',
          },
        }
      );

      const data = response.data;
      
      if (response.status !== 200) {
        // If the API returned an error message, use it
        if (data && data.error) {
          throw new Error(data.error);
        }
        throw new Error(t('assign_docid.projects_form.errors.failed_to_fetch'));
      }
      
      setCurrentProject({
        title: data.title[0].text,
        description: data.description[0].text,
        raidId: raidId
      });
    } catch (error) {
      console.error('Error fetching project:', error);
      // Show the specific error message from the API or a generic one
      setError(error.message || t('assign_docid.projects_form.errors.failed_retrieve_data'));
    } finally {
      setIsSearching(false);
    }
  };

  const handleManualProjectChange = (field) => (event) => {
    setManualProject({
      ...manualProject,
      [field]: event.target.value
    });
  };

  const handleAddManualProject = () => {
    if (manualProject.title && manualProject.institution) {
      const newProjects = [...(formData.projects || []), manualProject];
      updateFormData({ ...formData, projects: newProjects });
      handleModalClose();
    }
  };

  const handleAddProject = () => {
    if (currentProject) {
      const newProjects = [...(formData.projects || []), currentProject];
      updateFormData({ ...formData, projects: newProjects });
      handleModalClose();
    }
  };

  const handleRemoveProject = (index) => {
    const newProjects = [...formData.projects];
    newProjects.splice(index, 1);
    updateFormData({ ...formData, projects: newProjects });
  };

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
          {t('assign_docid.projects_form.title')}
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleModalOpen}
          sx={{
            bgcolor: theme.palette.mode === 'dark' ? '#2e7d32' : '#4caf50',
            color: theme.palette.common.white,
            '&:hover': { 
              bgcolor: theme.palette.mode === 'dark' ? '#1b5e20' : '#388e3c' 
            }
          }}
        >
          {t('assign_docid.projects_form.add')}
        </Button>
      </Box>

      <Divider sx={{ mb: 3 }} />

      {formData.projects && formData.projects.length > 0 ? (
        <Box sx={{ width: '100%' }}>
          {formData.projects.map((project, index) => (
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
                  {t('assign_docid.projects_form.project_number', { number: index + 1 })}
                </Typography>
                <IconButton 
                  onClick={() => handleRemoveProject(index)}
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
                    label={t('assign_docid.projects_form.project_title')}
                    value={project.title}
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
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label={t('assign_docid.projects_form.project_description')}
                    value={project.description || 'N/A'}
                    multiline
                    rows={4}
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
          {t('assign_docid.projects_form.no_projects')}
        </Typography>
      )}

      <Modal
        open={open}
        onClose={handleModalClose}
        aria-labelledby="modal-title"
      >
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '100%',
          maxWidth: 800,
          bgcolor: theme.palette.background.paper,
          borderRadius: 1,
          boxShadow: 24,
          maxHeight: '90vh',
          overflow: 'auto'
        }}>
          <Box sx={{
            bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.main,
            color: theme.palette.common.white,
            p: 2,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <Typography variant="h6" component="h2">
              {t('assign_docid.projects_form.add_project')}
            </Typography>
            <IconButton 
              onClick={handleModalClose}
              sx={{ color: theme.palette.common.white }}
            >
              <CloseIcon />
            </IconButton>
          </Box>

          <Box sx={{ 
            p: 3,
            '& .MuiTextField-root': {
              '& .MuiOutlinedInput-root': {
                '& fieldset': {
                  borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : theme.palette.divider
                },
                '&:hover fieldset': {
                  borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.2)' : theme.palette.primary.main
                },
                '&.Mui-focused fieldset': {
                  borderColor: theme.palette.primary.main
                }
              },
              '& .MuiInputLabel-root': {
                color: theme.palette.text.secondary,
                '&.Mui-focused': {
                  color: theme.palette.primary.main
                }
              },
              '& .MuiInputBase-input': {
                color: theme.palette.text.primary
              }
            }
          }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <TextField
                    sx={{ flex: 1 }}
                    label={t('assign_docid.projects_form.raid_url')}
                    value={raidId}
                    onChange={handleRaidIdChange}
                    placeholder="e.g., https://app.demo.raid.org.au/raids/10.80368/b1adfb3a"
                    error={Boolean(error)}
                    helperText={error || "Enter the full RAID URL"}
                  />
                  <Button
                    variant="contained"
                    startIcon={isSearching ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                    onClick={handleFindProject}
                    disabled={isSearching || !raidId.trim()}
                    sx={{ 
                      minWidth: '150px',
                      bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.main,
                      color: theme.palette.common.white,
                      '&:hover': {
                        bgcolor: theme.palette.mode === 'dark' ? '#1c2552' : theme.palette.primary.dark
                      }
                    }}
                  >
                    {isSearching ? t('assign_docid.projects_form.searching') : t('assign_docid.projects_form.find_project')}
                  </Button>
                </Box>
              </Grid>

              {currentProject && (
                <Grid item xs={12}>
                  <Alert 
                    severity="success" 
                    sx={{ 
                      mb: 2,
                      bgcolor: theme.palette.mode === 'dark' ? 'rgba(40, 167, 69, 0.1)' : undefined
                    }}
                  >
                    {t('assign_docid.projects_form.project_found')}
                  </Alert>
                  <Paper 
                    sx={{ 
                      p: 2,
                      bgcolor: theme.palette.background.paper,
                      border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : theme.palette.divider}`
                    }}
                  >
                    <TextField
                      fullWidth
                      label={t('assign_docid.projects_form.title')}
                      value={currentProject.title}
                      InputProps={{ 
                        readOnly: true,
                        sx: { 
                          bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
                        }
                      }}
                      sx={{ mb: 2 }}
                    />
                    <TextField
                      fullWidth
                      label={t('assign_docid.projects_form.description')}
                      value={currentProject.description}
                      InputProps={{ 
                        readOnly: true,
                        sx: { 
                          bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
                        }
                      }}
                      multiline
                      rows={4}
                    />
                  </Paper>
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 2 }}>
                    <Button
                      variant="contained"
                      onClick={handleAddProject}
                      sx={{
                        bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.main,
                        color: theme.palette.common.white,
                        '&:hover': {
                          bgcolor: theme.palette.mode === 'dark' ? '#1c2552' : theme.palette.primary.dark
                        }
                      }}
                    >
                      {t('assign_docid.projects_form.add_project')}
                    </Button>
                  </Box>
                </Grid>
              )}

              <Grid item xs={12}>
                <Divider sx={{ 
                  my: 2,
                  borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : theme.palette.divider
                }} />
                <Button
                  variant="outlined"
                  startIcon={<SearchIcon />}
                  onClick={() => window.open('https://raid.org/', '_blank')}
                  fullWidth
                  sx={{ 
                    height: '56px',
                    borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : theme.palette.divider,
                    color: theme.palette.text.primary,
                    '&:hover': {
                      borderColor: theme.palette.primary.main,
                      bgcolor: theme.palette.action.hover
                    }
                  }}
                >
                  {t('assign_docid.projects_form.get_raid_id')}
                </Button>
              </Grid>
            </Grid>
          </Box>
        </Box>
      </Modal>
    </Box>
  );
};

export default ProjectForm; 