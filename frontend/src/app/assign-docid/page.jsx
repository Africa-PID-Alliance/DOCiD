"use client";

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useSelector } from 'react-redux';
import {
  Container,
  Box,
  Stepper,
  Step,
  StepLabel,
  Button,
  Typography,
  Paper,
  StepIcon,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  CircularProgress
} from '@mui/material';
import {
  Fingerprint,
  LibraryBooks,
  Description,
  Person,
  Business,
  AttachMoney,
  Folder,
  Warning as WarningIcon
} from '@mui/icons-material';
import { Divider } from '@mui/material';
import CustomStepIcon from './components/CustomStepIcon';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { useTheme } from '@mui/material/styles';

// Step components will be imported here
import DocIDForm from './components/DocIDForm';
import PublicationsForm from './components/PublicationsForm';
import DocumentsForm from './components/DocumentsForm';
import CreatorsForm from './components/CreatorsForm';
import OrganizationsForm from './components/OrganizationsForm';
import FundersForm from './components/FundersForm';
import ProjectForm from './components/ProjectForm';

const AssignDocID = () => {
  const { t } = useTranslation();
  const { user } = useSelector((state) => state.auth);
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
  const [formData, setFormData] = useState({
    docId: {
      title: '',
      resourceType: '',
      description: '',
      generatedId: ''
    },
    publications: {
      publicationType: '',
      files: []
    },
    documents: {
      documentType: '',
      files: []
    },
    creators: { creators: [] },
    organizationsOrcid: { organizations: [] },
    organizationsIsni: { organizations: [] },
    funders: { funders: [] },
    project: {
      projects: []
    }
  });
  const [openConfirmModal, setOpenConfirmModal] = useState(false);
  
  // Draft functionality state
  const [draftStatus, setDraftStatus] = useState('idle'); // 'idle', 'saving', 'saved', 'error'
  const [lastSaved, setLastSaved] = useState(null);
  const [showDraftNotification, setShowDraftNotification] = useState(false);
  const [draftLoaded, setDraftLoaded] = useState(false);
  const autoSaveIntervalRef = useRef(null);
  const isFormDirty = useRef(false);
  const formDataRef = useRef(formData); // Use ref to store current formData

  const theme = useTheme();

  // Define steps using translations
  const steps = [
    t('assign_docid.steps.docid'),
    t('assign_docid.steps.publications'),
    t('assign_docid.steps.documents'),
    t('assign_docid.steps.creators'),
    t('assign_docid.steps.organizations'),
    t('assign_docid.steps.funders'),
    t('assign_docid.steps.projects')
  ];

  // Add console.log to debug
  console.log('Current formData:', formData);

  const handleNext = () => {
    // Check specifically for the generatedId property
    if (activeStep === 0 && !formData.docId?.generatedId) {
      alert(t('assign_docid.notifications.generate_first'));
      return;
    }
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const updateFormData = (section, newData) => {
    console.log('Updating form data:', section, newData); // Debug log

    // Special handling for publications section to preserve file objects
    if (section === 'publications' && newData.files) {
      setFormData(prevData => ({
        ...prevData,
        [section]: {
          ...prevData[section],
          publicationType: newData.publicationType,
          files: newData.files.map(file => ({
            ...file,
            // Preserve the actual File object
            file: file.file instanceof File ? file.file : file.file,
            // Keep other properties
            name: file.name,
            size: file.size,
            type: file.type,
            lastModified: file.lastModified,
            url: file.url,
            metadata: file.metadata
          }))
        }
      }));
    } else {
      // Handle other sections normally
      setFormData(prevData => ({
        ...prevData,
        [section]: {
          ...prevData[section],
          ...newData
        }
      }));
    }
  };

  // Auto-save function (now called saveDraft)
  const saveDraft = useCallback(async () => {
    if (!user?.email || !isFormDirty.current) return;
    
    console.log('Auto-saving draft at:', new Date().toLocaleTimeString());
    setDraftStatus('saving');
    
    try {
      const response = await axios.post('/api/publications/draft', {
        email: user.email,
        formData: formDataRef.current // Use ref to get current form data
      });
      
      if (response.data.saved) {
        setDraftStatus('saved');
        setLastSaved(new Date());
        setShowDraftNotification(true);
        isFormDirty.current = false;
        
        // Hide notification after 3 seconds
        setTimeout(() => setShowDraftNotification(false), 3000);
      }
    } catch (error) {
      console.error('Draft save failed:', error);
      setDraftStatus('error');
      setTimeout(() => setDraftStatus('idle'), 3000);
    }
  }, [user?.email]); // Only depend on user.email, not formData

  // Load saved draft data on component mount
  const loadSavedDraft = useCallback(async () => {
    if (!user?.email) return;
    
    try {
      const response = await axios.get(`/api/publications/draft/${user.email}`);
      
      if (response.data.hasDraft) {
        const savedFormData = response.data.formData;
        setFormData(savedFormData);
        setLastSaved(new Date(response.data.lastSaved));
        setDraftLoaded(true);
        
        // Show notification about loaded draft
        setNotification({
          open: true,
          message: `Draft restored from ${new Date(response.data.lastSaved).toLocaleString()}`,
          severity: 'info'
        });
        
        console.log('Draft loaded successfully:', savedFormData);
      }
    } catch (error) {
      console.error('Failed to load draft:', error);
    }
  }, [user?.email]);

  // Load saved draft only on component mount
  useEffect(() => {
    if (user?.email) {
      loadSavedDraft();
    }
  }, [user?.email]); // Only depend on user email, run once when user is available

  // Set up auto-save interval (separate effect to avoid re-running)
  useEffect(() => {
    if (user?.email) {
      console.log('Setting up auto-save interval for user:', user.email);
      // Set up auto-save every 10 seconds
      autoSaveIntervalRef.current = setInterval(() => {
        saveDraft();
      }, 10000);
      
      // Cleanup interval on unmount
      return () => {
        if (autoSaveIntervalRef.current) {
          clearInterval(autoSaveIntervalRef.current);
        }
      };
    }
  }, [user?.email]); // Only depend on user email, not on saveDraft function

  // Update formDataRef and mark form as dirty when data changes
  useEffect(() => {
    formDataRef.current = formData;
    isFormDirty.current = true;
  }, [formData]);

  // Manual save draft button (optional)
  const handleManualSave = async () => {
    await saveDraft();
  };

  // Discard draft function
  const handleDiscardDraft = async () => {
    if (!user?.email) return;

    const confirmDiscard = window.confirm(
      'Are you sure you want to discard your saved draft? This action cannot be undone.'
    );

    if (!confirmDiscard) return;

    try {
      await axios.delete(`/api/publications/draft/${user.email}`);

      // Reset form data to initial state
      setFormData({
        docId: {
          title: '',
          resourceType: '',
          description: '',
          generatedId: ''
        },
        publications: {
          publicationType: '',
          files: []
        },
        documents: {
          documentType: '',
          files: []
        },
        creators: { creators: [] },
        organizationsOrcid: { organizations: [] },
        organizationsIsni: { organizations: [] },
        funders: { funders: [] },
        project: {
          projects: []
        }
      });

      // Reset draft-related state
      setDraftLoaded(false);
      setLastSaved(null);
      setDraftStatus('idle');
      isFormDirty.current = false;

      // Reset to first step
      setActiveStep(0);

      // Show success notification
      setNotification({
        open: true,
        message: 'Draft discarded successfully',
        severity: 'success'
      });

      console.log('Draft discarded successfully');
    } catch (error) {
      console.error('Failed to discard draft:', error);
      setNotification({
        open: true,
        message: 'Failed to discard draft',
        severity: 'error'
      });
    }
  };

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <DocIDForm
            formData={formData.docId}
            updateFormData={(data) => updateFormData('docId', data)}
          />
        );
      case 1:
        return (
          <PublicationsForm
            formData={formData.publications}
            updateFormData={(data) => updateFormData('publications', data)}
          />
        );
      case 2:
        return (
          <DocumentsForm
            formData={formData.documents}
            updateFormData={(data) => updateFormData('documents', data)}
          />
        );
      case 3:
        return (
          <CreatorsForm
            formData={formData.creators}
            updateFormData={(data) => updateFormData('creators', data)}
          />
        );
      case 4:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <Paper
              elevation={2}
              sx={{
                p: 3,
                borderRadius: 2,
                border: `1px solid ${theme.palette.divider}`,
                bgcolor: theme.palette.background.paper
              }}
            >
              <OrganizationsForm
                formData={formData.organizationsOrcid || { organizations: [] }}
                updateFormData={(data) => updateFormData('organizationsOrcid', data)}
                type="orcid"
                label="ORCID"
              />
            </Paper>
            <Paper
              elevation={2}
              sx={{
                p: 3,
                borderRadius: 2,
                border: `1px solid ${theme.palette.divider}`,
                bgcolor: theme.palette.background.paper
              }}
            >
              <OrganizationsForm
                formData={formData.organizationsIsni || { organizations: [] }}
                updateFormData={(data) => updateFormData('organizationsIsni', data)}
                type="isni"
                label="ISNI"
              />
            </Paper>
          </Box>
        );
      case 5:
        return (
          <FundersForm
            formData={formData.funders}
            updateFormData={(data) => updateFormData('funders', data)}
          />
        );
      case 6:
        return (
          <ProjectForm
            formData={formData.project}
            updateFormData={(data) => updateFormData('project', data)}
          />
        );
      default:
        return null;
    }
  };

  const handleStepClick = (step) => {
    setActiveStep(step);
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  const handleSubmitClick = () => {
    setOpenConfirmModal(true);
  };

  const handleCloseConfirmModal = () => {
    setOpenConfirmModal(false);
  };

  const handleConfirmSubmit = async () => {
    setOpenConfirmModal(false);
    
    try {
      await handleSubmit();
      
      // Delete draft data after successful submission
      if (user?.email) {
        await axios.delete(`/api/publications/draft/${user.email}`);
        console.log('Draft deleted after successful submission');
      }
    } catch (error) {
      console.error('Submission failed:', error);
    }
  };

  const handleSubmit = async () => {
    const isValidFiles = (files) =>
      files.every(
        (file) =>
          file.metadata.title &&
          file.metadata.description &&
          file.metadata.identifier &&
          file.metadata.generated_identifier
      );

    // Validation checks
    if (!formData.docId.resourceType) {
      setActiveStep(0);
      setNotification({ open: true, message: "Resource type is required!", severity: 'error' });
      return;
    } else if (!formData.docId.generatedId) {
      setActiveStep(0);
      setNotification({ open: true, message: "DOCiD is required!", severity: 'error' });
      return;
    } else if (!formData.docId.title) {
      setActiveStep(0);
      setNotification({ open: true, message: "Document title is required!", severity: 'error' });
      return;
    } else if (!formData.docId.description) {
      setActiveStep(0);
      setNotification({ open: true, message: "Document description is required!", severity: 'error' });
      return;
    } else if (!formData.creators?.creators || formData.creators.creators.length === 0) {
      setActiveStep(3);
      setNotification({ open: true, message: "Creator(s) are required!", severity: 'error' });
      return;
    }

    setLoading(true);
    const submitData = new FormData();

    try {
      // Debug user information
      console.log('User data:', user);

      if (!user?.id) {
        throw new Error('User ID is required but not available');
      }

      // 1. Basic document details
      submitData.append("publicationPoster", formData.docId.thumbnail || '');
      submitData.append("documentDocid", formData.docId.generatedId);
      submitData.append("documentTitle", formData.docId.title);
      submitData.append("documentDescription", formData.docId.description);
      submitData.append("resourceType", formData.docId.resourceType);
      submitData.append("user_id", Number(parseInt(user.id))); // Changed to snake_case and ensure it's a string
      submitData.append("owner", String(user?.name || user?.username || ''));
      submitData.append("avatar",String(user?.picture));
      submitData.append("doi", formData.docId.generatedId);


      // 2. Publications Files
      if (formData.publications?.files?.length > 0) {
        
        formData.publications.files.forEach((file, index) => {

         
        submitData.append(`filesPublications_${index}_file`, file.file);
        submitData.append(`filesPublications[${index}][file_type]`, file.type);
        submitData.append(`filesPublications[${index}][title]`, file.metadata.title);
        submitData.append(`filesPublications[${index}][description]`, file.metadata.description);
        submitData.append(`filesPublications[${index}][identifier]`, file.metadata.identifier);
        submitData.append(`filesPublications[${index}][publication_type]`, formData.publications.publicationType);
        submitData.append(`filesPublications[${index}][generated_identifier]`, file.metadata.generated_identifier);
          
        });
      }

      // 3. Documents
      if (formData.documents?.files?.length > 0) {
        console.log('Documents data being submitted:', formData.documents);
        
        formData.documents.files.forEach((file, index) => {
          console.log(`Document ${index} metadata:`, {
            title: file.metadata.title,
            description: file.metadata.description,
            identifier: file.metadata.identifier,
            identifierType: file.metadata.identifierType,
            generated_identifier: file.metadata.generated_identifier
          });
          
          submitData.append(`filesDocuments[${index}][title]`, file.metadata.title);
          submitData.append(`filesDocuments[${index}][description]`, file.metadata.description);
          submitData.append(`filesDocuments[${index}][identifier]`, file.metadata.identifier);
          submitData.append(`filesDocuments[${index}][publication_type]`, formData.documents.documentType);
          submitData.append(`filesDocuments[${index}][generated_identifier]`, file.metadata.generated_identifier);
          submitData.append(`filesDocuments_${index}_file`, file.file);
        });
      }

      // 4. Creators
      if (formData.creators?.creators?.length > 0) {
        formData.creators.creators.forEach((creator, index) => {
          submitData.append(`creators[${index}][family_name]`, creator.familyName);
          submitData.append(`creators[${index}][given_name]`, creator.givenName);
          submitData.append(`creators[${index}][identifier]`, creator.identifier_type);
          submitData.append(`creators[${index}][role]`, creator.role);
          submitData.append(`creators[${index}][orcid_id]`, creator.orcidId || '');
        });
      }

      // 5. Organizations (ORCID)
      if (formData.organizationsOrcid?.organizations?.length > 0) {
        formData.organizationsOrcid.organizations.forEach((organization, index) => {
          submitData.append(`organizationOrcid[${index}][name]`, organization.name);
          submitData.append(`organizationOrcid[${index}][other_name]`, organization.otherName);
          submitData.append(`organizationOrcid[${index}][type]`, organization.type);
          submitData.append(`organizationOrcid[${index}][country]`, organization.country);
          submitData.append(`organizationOrcid[${index}][ror_id]`, organization.rorId || '');
        });
      }

      // 5b. Organizations (ISNI)
      if (formData.organizationsIsni?.organizations?.length > 0) {
        formData.organizationsIsni.organizations.forEach((organization, index) => {
          submitData.append(`organizationIsni[${index}][name]`, organization.name);
          submitData.append(`organizationIsni[${index}][other_name]`, organization.otherName);
          submitData.append(`organizationIsni[${index}][type]`, organization.type);
          submitData.append(`organizationIsni[${index}][country]`, organization.country);
          submitData.append(`organizationIsni[${index}][ror_id]`, organization.rorId || '');
        });
      }

      // 6. Funders
      if (formData.funders?.funders?.length > 0) {
        console.log("Funders files",formData.funders);
        formData.funders.funders.forEach((funder, index) => {
          submitData.append(`funders[${index}][name]`, funder.name);
          submitData.append(`funders[${index}][other_name]`, funder.otherName);
          submitData.append(`funders[${index}][type]`, 1);
          submitData.append(`funders[${index}][country]`, funder.country);
          submitData.append(`funders[${index}][ror_id]`, funder.rorId || '');
        });
      }

      // 7. Projects
      if (formData.project?.projects?.length > 0) {
        console.log("Projects files",formData.project);
        formData.project.projects.forEach((project, index) => {
          submitData.append(`projects[${index}][title]`, project.title);
          submitData.append(`projects[${index}][raid_id]`, project.raidId);
          submitData.append(`projects[${index}][description]`, project.type);
        });
      }

      // Log the final FormData for debugging
      console.log('Final FormData entries:');
      for (let pair of submitData.entries()) {
        if (pair[1] instanceof File || pair[1] instanceof Blob) {
          console.log(`${pair[0]}: [File object], size: ${pair[1].size}, type: ${pair[1].type}`);
        } else {
          try {
            // Try to parse JSON strings for better debugging
            const parsed = JSON.parse(pair[1]);
            console.log(`${pair[0]}:`, parsed);
          } catch {
            console.log(`${pair[0]}: ${pair[1]}`);
          }
        }
      }

      // Make the API call
      try {
        const response = await axios.post(
          '/api/publications/publish',
          submitData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
              'Accept': 'application/json',
            },
            onUploadProgress: (progressEvent) => {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              console.log('Upload Progress:', percentCompleted);
            }
          }
        );

        if (response.status === 200 || response.status === 201) {
          setNotification({
            open: true,
            message: t('assign_docid.notifications.success_assigned'),
            severity: 'success'
          });
          // Set flag in sessionStorage before redirecting
          sessionStorage.setItem('fromAssignDocId', 'true');
          // Move to completion step
          setActiveStep(steps.length);
          // Redirect to list-docids with success parameter
          window.location.href = '/list-docids?success=true';
        } else {
          throw new Error(t('assign_docid.notifications.failed_to_assign'));
        }
      } catch (error) {
        console.error("Error details:", {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          message: error.message
        });

        let errorMessage = "Error in submission: ";
        if (error.response?.data?.message) {
          errorMessage += error.response.data.message;
        } else if (error.response?.data?.error) {
          errorMessage += error.response.data.error;
        } else if (error.response?.data) {
          errorMessage += JSON.stringify(error.response.data);
        } else {
          errorMessage += error.message;
        }

        console.log("Error message:", error);

        setNotification({
          open: true,
          message: errorMessage,
          severity: 'error'
        });
      }
    } catch (error) {
      console.error("Error in form preparation:", error);
      setNotification({
        open: true,
        message: "Error preparing form data: " + error.message,
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ width: '100%', py: 4,bgcolor: theme.palette.background.content, minHeight: '100vh'}}>

      {/* Draft status indicator */}
      <Box sx={{ width: '100%', px: 4, mb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          {/* Left side - Draft loaded indicator */}
          {draftLoaded && (
            <Box sx={{ display: 'flex', alignItems: 'center', color: 'info.main' }}>
              <Typography variant="caption">
                📄 Draft loaded from previous session
              </Typography>
            </Box>
          )}
          
          {/* Right side - Save status */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {/* Discard draft button */}
            {(draftLoaded || lastSaved) && (
              <Button
                variant="outlined"
                size="small"
                color="error"
                onClick={handleDiscardDraft}
                disabled={draftStatus === 'saving'}
                sx={{ minWidth: 'auto', px: 2 }}
              >
                Discard Draft
              </Button>
            )}

            {/* Manual save button (optional) */}
            <Button
              variant="outlined"
              size="small"
              onClick={handleManualSave}
              disabled={draftStatus === 'saving'}
              sx={{ minWidth: 'auto', px: 2 }}
            >
              {t('assign_docid.buttons.save_draft')}
            </Button>
            
            {/* Auto-save status */}
            {draftStatus === 'saving' && (
              <Box sx={{ display: 'flex', alignItems: 'center', color: 'text.secondary' }}>
                <CircularProgress size={16} sx={{ mr: 1 }} />
                <Typography variant="caption">Saving...</Typography>
              </Box>
            )}
            
            {draftStatus === 'saved' && lastSaved && (
              <Box sx={{ display: 'flex', alignItems: 'center', color: 'success.main' }}>
                <Typography variant="caption">
                  ✅ {t('assign_docid.buttons.save_draft')} {lastSaved.toLocaleTimeString()}
                </Typography>
              </Box>
            )}
            
            {draftStatus === 'error' && (
              <Box sx={{ display: 'flex', alignItems: 'center', color: 'error.main' }}>
                <Typography variant="caption">❌ {t('assign_docid.buttons.save_draft')} failed</Typography>
              </Box>
            )}
          </Box>
        </Box>
      </Box>

      {/* Full width stepper */}
      <Box sx={{ width: '100%', px: 4, mb: 3 }}>
        <Stepper
          activeStep={activeStep}
          alternativeLabel
          nonLinear
          sx={{
            '& .MuiStepLabel-label': {
              mt: 1,
              fontSize: '0.9rem',
              fontWeight: 600,
              color: theme.palette.mode === 'dark' ? '#fff' : '#141a3b',
              cursor: 'pointer'
            },
            '& .MuiStepLabel-label.Mui-active': {
              color: theme.palette.mode === 'dark' ? '#1976d2' : '#0d47a1'
            },
            '& .MuiStepLabel-iconContainer': {
              cursor: 'pointer',
              '& .MuiSvgIcon-root': {
                width: '2rem',
                height: '2rem',
                color: theme.palette.mode === 'dark' ? '#fff' : '#141a3b'
              }
            },
            '& .MuiStepConnector-root': {
              top: '20px',
              left: 'calc(-50% + 20px)',
              right: 'calc(50% + 20px)',
            },
            '& .MuiStepConnector-line': {
              height: '2px',
              border: 0,
              backgroundColor: 'transparent',
              backgroundImage: theme.palette.mode === 'dark'
                ? 'linear-gradient(90deg, #141a3b 0%, #1e2756 50%, #2a3275 100%)'
                : 'linear-gradient(90deg, #1565c0 0%, #1976d2 50%, #2196f3 100%)',
            }
          }}
        >
          {steps.map((step, index) => (
            <Step key={step} completed={activeStep > index}>
              <StepLabel
                StepIconComponent={CustomStepIcon}
                onClick={() => handleStepClick(index)}
              >
                {step}
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </Box>

      {/* Navigation buttons below stepper */}
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mb: 4, px: 4 }}>
        <Button
          disabled={activeStep === 0}
          onClick={handleBack}
          sx={{
            fontSize: '1rem',
            fontWeight: 500
          }}
        >
          {t('assign_docid.buttons.back')}
        </Button>
        <Button
          variant="contained"
          onClick={activeStep === steps.length - 1 ? handleSubmitClick : handleNext}
          disabled={loading}
          sx={{
            bgcolor: '#1565c0',
            fontSize: '1rem',
            fontWeight: 500,
            '&:hover': {
              bgcolor: '#1976d2'
            }
          }}
        >
          {activeStep === steps.length - 1 ? t('assign_docid.buttons.submit') : t('assign_docid.buttons.next')}
        </Button>
      </Box>

      {/* Confirmation Modal */}
      <Dialog
        open={openConfirmModal}
        onClose={handleCloseConfirmModal}
        aria-labelledby="confirm-dialog-title"
        PaperProps={{
          sx: {
            borderRadius: 2,
            minWidth: '400px'
          }
        }}
      >
        <DialogTitle id="confirm-dialog-title" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon sx={{ color: '#ff9800', fontSize: 28 }} />
          {t('assign_docid.confirm_modal.title')}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            {t('assign_docid.confirm_modal.message')}
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3, gap: 2 }}>
          <Button
            onClick={handleCloseConfirmModal}
            variant="outlined"
            sx={{
              borderColor: '#1565c0',
              color: '#1565c0',
              '&:hover': {
                borderColor: '#0d47a1',
                bgcolor: 'rgba(21, 101, 192, 0.04)'
              }
            }}
          >
            {t('assign_docid.buttons.cancel')}
          </Button>
          <Button
            onClick={handleConfirmSubmit}
            variant="contained"
            sx={{
              bgcolor: '#1565c0',
              '&:hover': {
                bgcolor: '#1976d2'
              }
            }}
          >
            {t('assign_docid.confirm_modal.confirm')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseNotification}
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>

      {/* Draft notification snackbar */}
      <Snackbar
        open={showDraftNotification}
        autoHideDuration={3000}
        onClose={() => setShowDraftNotification(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setShowDraftNotification(false)}
          severity="success"
          sx={{ width: '100%' }}
        >
          {t('assign_docid.notifications.draft_saved')}
        </Alert>
      </Snackbar>

      {/* Reduced width form container */}
      <Container sx={{ px: 4, maxWidth: 90 }}>
        <Paper
          elevation={0}
          sx={{
            p: 4,
            bgcolor: 'white',
            borderRadius: 2,
            bgcolor: 'background.paper'
          }}
        >
          {activeStep === steps.length ? (
            <Box sx={{ textAlign: 'center' }}>
              <Button
                onClick={() => {
                  // Redirect to list-docids page
                  window.location.href = '/list-docids';
                }}
                variant="contained"
                sx={{
                  mt: 2,
                  bgcolor: '#1565c0',
                  color: 'white',
                  '&:hover': {
                    bgcolor: '#1976d2'
                  }
                }}
              >
                {t('assign_docid.buttons.view_all_docids')}
              </Button>
            </Box>
          ) : (
            <Box>
              {getStepContent(activeStep)}
            </Box>
          )}
        </Paper>
      </Container>
    </Box>
  );
};

export default AssignDocID; 