"use client";

import React, { useState, useEffect, useCallback, useRef, Suspense } from 'react';
import { useSelector } from 'react-redux';
import { useSearchParams } from 'next/navigation';
import {
  Container,
  Box,
  Stepper,
  Step,
  StepLabel,
  Button,
  Typography,
  Paper,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress
} from '@mui/material';
import {
  Warning as WarningIcon
} from '@mui/icons-material';
import VersionStepIcon from './components/VersionStepIcon';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

// Reuse form components from assign-docid
import DocIDForm from '../assign-docid/components/DocIDForm';
import PublicationsForm from '../assign-docid/components/PublicationsForm';
import DocumentsForm from '../assign-docid/components/DocumentsForm';
import CreatorsForm from '../assign-docid/components/CreatorsForm';
import OrganizationsForm from '../assign-docid/components/OrganizationsForm';
import FundersForm from '../assign-docid/components/FundersForm';
import ProjectForm from '../assign-docid/components/ProjectForm';
import RridForm from '../assign-docid/components/RridForm';
import ParentDocidSelector from './components/ParentDocidSelector';

const VersionDocIDInner = () => {
  const { t } = useTranslation();
  const { user } = useSelector((state) => state.auth);
  const searchParams = useSearchParams();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [parentLoading, setParentLoading] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
  const [selectedParent, setSelectedParent] = useState(null);
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
    organizationsRor: { organizations: [] },
    organizationsIsni: { organizations: [] },
    researchResources: { resources: [] },
    funders: { funders: [] },
    project: {
      projects: []
    }
  });
  const [openConfirmModal, setOpenConfirmModal] = useState(false);

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Steps: Step 0 is "Select Parent", then the same 7 steps as assign-docid
  const steps = [
    'Select Parent DOCiD',
    t('assign_docid.steps.docid'),
    t('assign_docid.steps.publications'),
    t('assign_docid.steps.documents'),
    t('assign_docid.steps.creators'),
    t('assign_docid.steps.organizations'),
    t('assign_docid.steps.funders'),
    t('assign_docid.steps.projects')
  ];

  // Auto-select parent from URL param (e.g. /version-docid?parentId=123)
  const parentIdFromUrl = searchParams.get('parentId');
  const autoSelectAttempted = useRef(false);

  useEffect(() => {
    if (parentIdFromUrl && !autoSelectAttempted.current && !selectedParent) {
      autoSelectAttempted.current = true;
      const fetchParentFromUrl = async () => {
        setParentLoading(true);
        try {
          const response = await axios.get(`/api/publications/get-publication/${parentIdFromUrl}`);
          const parentData = response.data;
          const parentDocid = {
            id: parentData.id,
            document_docid: parentData.document_docid,
            document_title: parentData.document_title,
            version_number: parentData.version_number || null,
            published: parentData.published
          };
          // This triggers handleSelectParent which pre-fills form + advances step
          handleSelectParent(parentDocid);
          setActiveStep(1);
        } catch (error) {
          console.error('Failed to auto-select parent from URL:', error);
          setNotification({
            open: true,
            message: 'Could not load the selected DOCiD. Please select manually.',
            severity: 'warning'
          });
        } finally {
          setParentLoading(false);
        }
      };
      fetchParentFromUrl();
    }
  }, [parentIdFromUrl, selectedParent]);

  // When parent is selected, pre-fill form from parent data
  const handleSelectParent = useCallback(async (parentDocid) => {
    setSelectedParent(parentDocid);

    if (!parentDocid) return;

    setParentLoading(true);
    try {
      const response = await axios.get(`/api/publications/get-publication/${parentDocid.id}`);
      const parentData = response.data;

      // Pre-fill form fields from parent (user can modify before submitting)
      setFormData((previousFormData) => ({
        ...previousFormData,
        docId: {
          ...previousFormData.docId,
          title: parentData.document_title || '',
          resourceType: parentData.resource_type_id || '',
          description: parentData.document_description || '',
          generatedId: '' // Must generate a new DOCiD
        },
        creators: {
          creators: (parentData.creators || []).map((creator) => ({
            familyName: creator.family_name || '',
            givenName: creator.given_name || '',
            identifier_type: creator.identifier_type || '',
            role: creator.role_id || '',
            orcidId: creator.identifier || ''
          }))
        },
        organizationsRor: {
          organizations: (parentData.organizations || [])
            .filter((org) => org.identifier_type === 'ror')
            .map((org) => ({
              name: org.name || '',
              otherName: org.other_name || '',
              type: org.type || '',
              country: org.country || '',
              rorId: org.identifier || ''
            }))
        },
        organizationsIsni: {
          organizations: (parentData.organizations || [])
            .filter((org) => org.identifier_type === 'isni')
            .map((org) => ({
              name: org.name || '',
              otherName: org.other_name || '',
              type: org.type || '',
              country: org.country || '',
              rorId: org.identifier || ''
            }))
        },
        funders: {
          funders: (parentData.funders || []).map((funder) => ({
            name: funder.name || '',
            otherName: funder.other_name || '',
            type: funder.type || '',
            country: funder.country || '',
            rorId: funder.identifier || ''
          }))
        },
        project: {
          projects: (parentData.projects || []).map((project) => ({
            title: project.title || '',
            raidId: project.raid_id || project.identifier || '',
            type: project.description || ''
          }))
        }
      }));

      setNotification({
        open: true,
        message: 'Form pre-filled from parent DOCiD. Generate a new DOCiD and modify fields as needed.',
        severity: 'info'
      });
    } catch (error) {
      console.error('Failed to fetch parent data:', error);
      setNotification({
        open: true,
        message: 'Failed to load parent DOCiD data for pre-fill.',
        severity: 'warning'
      });
    } finally {
      setParentLoading(false);
    }
  }, []);

  const handleNext = () => {
    // Step 0: must select a parent
    if (activeStep === 0 && !selectedParent) {
      setNotification({ open: true, message: 'Please select a parent DOCiD first.', severity: 'error' });
      return;
    }
    // Step 1 (DocID): must generate a new DOCiD
    if (activeStep === 1 && !formData.docId?.generatedId) {
      alert(t('assign_docid.notifications.generate_first'));
      return;
    }
    setActiveStep((previousStep) => previousStep + 1);
  };

  const handleBack = () => {
    setActiveStep((previousStep) => previousStep - 1);
  };

  const updateFormData = (section, newData) => {
    if (section === 'publications' && newData.files) {
      setFormData(previousData => ({
        ...previousData,
        [section]: {
          ...previousData[section],
          publicationType: newData.publicationType,
          files: newData.files.map(file => ({
            ...file,
            file: file.file instanceof File ? file.file : file.file,
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
      setFormData(previousData => ({
        ...previousData,
        [section]: {
          ...previousData[section],
          ...newData
        }
      }));
    }
  };

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <ParentDocidSelector
            userId={user?.id}
            selectedParent={selectedParent}
            onSelectParent={handleSelectParent}
          />
        );
      case 1:
        return (
          <DocIDForm
            formData={formData.docId}
            updateFormData={(data) => updateFormData('docId', data)}
          />
        );
      case 2:
        return (
          <PublicationsForm
            formData={formData.publications}
            updateFormData={(data) => updateFormData('publications', data)}
          />
        );
      case 3:
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
              <DocumentsForm
                formData={formData.documents}
                updateFormData={(data) => updateFormData('documents', data)}
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
              <RridForm
                formData={formData.researchResources || { resources: [] }}
                updateFormData={(data) => updateFormData('researchResources', data)}
                allowedResourceTypes={['software', 'antibody', 'cell_line']}
              />
            </Paper>
          </Box>
        );
      case 4:
        return (
          <CreatorsForm
            formData={formData.creators}
            updateFormData={(data) => updateFormData('creators', data)}
          />
        );
      case 5:
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
                formData={formData.organizationsRor || { organizations: [] }}
                updateFormData={(data) => updateFormData('organizationsRor', data)}
                type="ror"
                label="ROR"
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
                formData={formData.organizationsRinggold || { organizations: [] }}
                updateFormData={(data) => updateFormData('organizationsRinggold', data)}
                type="ringgold"
                label="Ringgold"
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
              <RridForm
                formData={formData.researchResources || { resources: [] }}
                updateFormData={(data) => updateFormData('researchResources', data)}
                allowedResourceTypes={['core_facility']}
              />
            </Paper>
          </Box>
        );
      case 6:
        return (
          <FundersForm
            formData={formData.funders}
            updateFormData={(data) => updateFormData('funders', data)}
          />
        );
      case 7:
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
    // Don't allow skipping past step 0 without selecting parent
    if (step > 0 && !selectedParent) {
      setNotification({ open: true, message: 'Please select a parent DOCiD first.', severity: 'error' });
      return;
    }
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
    await handleSubmit();
  };

  const handleSubmit = async () => {
    // Validation
    if (!selectedParent) {
      setActiveStep(0);
      setNotification({ open: true, message: 'Please select a parent DOCiD.', severity: 'error' });
      return;
    }
    if (!formData.docId.resourceType) {
      setActiveStep(1);
      setNotification({ open: true, message: 'Resource type is required!', severity: 'error' });
      return;
    }
    if (!formData.docId.generatedId) {
      setActiveStep(1);
      setNotification({ open: true, message: 'DOCiD is required!', severity: 'error' });
      return;
    }
    if (!formData.docId.title) {
      setActiveStep(1);
      setNotification({ open: true, message: 'Document title is required!', severity: 'error' });
      return;
    }
    if (!formData.docId.description) {
      setActiveStep(1);
      setNotification({ open: true, message: 'Document description is required!', severity: 'error' });
      return;
    }
    if (!formData.creators?.creators || formData.creators.creators.length === 0) {
      setActiveStep(4);
      setNotification({ open: true, message: 'Creator(s) are required!', severity: 'error' });
      return;
    }

    setLoading(true);
    const submitData = new FormData();

    try {
      if (!user?.id) {
        throw new Error('User ID is required but not available');
      }

      // Parent ID (the key difference from assign-docid)
      submitData.append("parentId", selectedParent.id);

      // Basic document details
      submitData.append("publicationPoster", formData.docId.thumbnail || '');
      submitData.append("documentDocid", formData.docId.generatedId);
      submitData.append("documentTitle", formData.docId.title);
      submitData.append("documentDescription", formData.docId.description);
      submitData.append("resourceType", formData.docId.resourceType);
      submitData.append("user_id", Number(parseInt(user.id)));
      submitData.append("owner", String(user?.name || user?.username || ''));
      submitData.append("avatar", String(user?.picture));
      // doi intentionally omitted — new versions don't have a DOI until independently assigned

      // Publications Files
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

      // Documents
      if (formData.documents?.files?.length > 0) {
        formData.documents.files.forEach((file, index) => {
          submitData.append(`filesDocuments[${index}][title]`, file.metadata.title);
          submitData.append(`filesDocuments[${index}][description]`, file.metadata.description);
          submitData.append(`filesDocuments[${index}][identifier]`, file.metadata.identifier);
          submitData.append(`filesDocuments[${index}][publication_type]`, formData.documents.documentType);
          submitData.append(`filesDocuments[${index}][generated_identifier]`, file.metadata.generated_identifier);
          submitData.append(`filesDocuments_${index}_file`, file.file);
        });
      }

      // Creators
      if (formData.creators?.creators?.length > 0) {
        formData.creators.creators.forEach((creator, index) => {
          submitData.append(`creators[${index}][family_name]`, creator.familyName);
          submitData.append(`creators[${index}][given_name]`, creator.givenName);
          submitData.append(`creators[${index}][identifier]`, creator.identifier_type);
          submitData.append(`creators[${index}][role]`, creator.role);
          submitData.append(`creators[${index}][orcid_id]`, creator.orcidId || '');
        });
      }

      // Organizations (ROR)
      if (formData.organizationsRor?.organizations?.length > 0) {
        formData.organizationsRor.organizations.forEach((organization, index) => {
          submitData.append(`organizationRor[${index}][name]`, organization.name);
          submitData.append(`organizationRor[${index}][other_name]`, organization.otherName);
          submitData.append(`organizationRor[${index}][type]`, organization.type);
          submitData.append(`organizationRor[${index}][country]`, organization.country);
          submitData.append(`organizationRor[${index}][ror_id]`, organization.rorId || '');
        });
      }

      // Organizations (ISNI)
      if (formData.organizationsIsni?.organizations?.length > 0) {
        formData.organizationsIsni.organizations.forEach((organization, index) => {
          submitData.append(`organizationIsni[${index}][name]`, organization.name);
          submitData.append(`organizationIsni[${index}][other_name]`, organization.otherName);
          submitData.append(`organizationIsni[${index}][type]`, organization.type);
          submitData.append(`organizationIsni[${index}][country]`, organization.country);
          submitData.append(`organizationIsni[${index}][ror_id]`, organization.rorId || '');
        });
      }

      // Organizations (Ringgold)
      if (formData.organizationsRinggold?.organizations?.length > 0) {
        formData.organizationsRinggold.organizations.forEach((organization, index) => {
          submitData.append(`organizationRinggold[${index}][name]`, organization.name);
          submitData.append(`organizationRinggold[${index}][other_name]`, organization.otherName);
          submitData.append(`organizationRinggold[${index}][type]`, organization.type);
          submitData.append(`organizationRinggold[${index}][country]`, organization.country);
          submitData.append(`organizationRinggold[${index}][ringgold_id]`, organization.rorId || '');
        });
      }

      // Funders
      if (formData.funders?.funders?.length > 0) {
        formData.funders.funders.forEach((funder, index) => {
          submitData.append(`funders[${index}][name]`, funder.name);
          submitData.append(`funders[${index}][other_name]`, funder.otherName);
          submitData.append(`funders[${index}][type]`, 1);
          submitData.append(`funders[${index}][country]`, funder.country);
          submitData.append(`funders[${index}][ror_id]`, funder.rorId || '');
        });
      }

      // Projects
      if (formData.project?.projects?.length > 0) {
        formData.project.projects.forEach((project, index) => {
          submitData.append(`projects[${index}][title]`, project.title);
          submitData.append(`projects[${index}][raid_id]`, project.raidId);
          submitData.append(`projects[${index}][description]`, project.type);
        });
      }

      // Research Resources (RRIDs)
      if (formData.researchResources?.resources?.length > 0) {
        formData.researchResources.resources.forEach((resource, index) => {
          submitData.append(`researchResources[${index}][rrid]`, resource.rrid);
          submitData.append(`researchResources[${index}][rrid_name]`, resource.rridName || '');
          submitData.append(`researchResources[${index}][rrid_description]`, resource.rridDescription || '');
          submitData.append(`researchResources[${index}][rrid_resource_type]`, resource.rridResourceType || '');
          submitData.append(`researchResources[${index}][rrid_url]`, resource.rridUrl || '');
          submitData.append(`researchResources[${index}][resolved_json]`, JSON.stringify(resource.resolvedJson || {}));
        });
      }

      // Submit to version endpoint (not publish)
      const response = await axios.post(
        '/api/publications/version',
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
          message: `Version ${response.data.version_number} created successfully!`,
          severity: 'success'
        });
        setActiveStep(steps.length);
        window.location.href = '/list-docids?success=true';
      } else {
        throw new Error('Failed to create version');
      }
    } catch (error) {
      console.error("Error details:", error.response?.data || error.message);

      let errorMessage = "Error creating version: ";
      if (error.response?.data?.message) {
        errorMessage += error.response.data.message;
      } else if (error.response?.data?.error) {
        errorMessage += error.response.data.error;
      } else {
        errorMessage += error.message;
      }

      setNotification({
        open: true,
        message: errorMessage,
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{
      width: '100%',
      py: { xs: 2, sm: 3, md: 4 },
      bgcolor: theme.palette.background.content,
      minHeight: '100vh'
    }}>

      {/* Version info banner */}
      <Box sx={{ width: '100%', px: { xs: 2, sm: 3, md: 4 }, mb: 2 }}>
        <Alert severity="info" sx={{ mb: 1 }}>
          <Typography variant="subtitle2">
            Create New Version
          </Typography>
          <Typography variant="body2">
            Select a parent DOCiD, then fill in the form to create a new version.
            Fields will be pre-filled from the parent. You must generate a new DOCiD for this version.
          </Typography>
        </Alert>
      </Box>

      {/* Full width stepper */}
      <Box sx={{
        width: '100%',
        px: { xs: 1, sm: 2, md: 4 },
        mb: { xs: 2, sm: 3 },
        overflowX: { xs: 'auto', md: 'visible' }
      }}>
        <Stepper
          activeStep={activeStep}
          alternativeLabel={!isMobile}
          orientation={isMobile ? 'vertical' : 'horizontal'}
          nonLinear
          sx={{
            '& .MuiStepLabel-label': {
              mt: { xs: 0.5, sm: 1 },
              fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' },
              fontWeight: 600,
              color: theme.palette.mode === 'dark' ? '#fff' : '#141a3b',
              cursor: 'pointer'
            },
            '& .MuiStepLabel-label.Mui-active': {
              color: theme.palette.mode === 'dark' ? '#1976d2' : '#0d47a1'
            },
            '& .MuiStepIconContainer': {
              cursor: 'pointer',
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
                StepIconComponent={VersionStepIcon}
                onClick={() => handleStepClick(index)}
              >
                {step}
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </Box>

      {/* Navigation buttons below stepper */}
      <Box sx={{
        display: 'flex',
        flexDirection: { xs: 'column', sm: 'row' },
        justifyContent: 'center',
        gap: { xs: 1.5, sm: 2 },
        mb: { xs: 2, sm: 3, md: 4 },
        px: { xs: 2, sm: 3, md: 4 }
      }}>
        <Button
          disabled={activeStep === 0}
          onClick={handleBack}
          size={isMobile ? 'large' : 'medium'}
          fullWidth={isMobile}
          sx={{
            fontSize: { xs: '0.9rem', sm: '1rem' },
            fontWeight: 500,
            py: { xs: 1.5, sm: 1 }
          }}
        >
          {t('assign_docid.buttons.back')}
        </Button>
        <Button
          variant="contained"
          onClick={activeStep === steps.length - 1 ? handleSubmitClick : handleNext}
          disabled={loading || parentLoading}
          size={isMobile ? 'large' : 'medium'}
          fullWidth={isMobile}
          sx={{
            bgcolor: '#1565c0',
            fontSize: { xs: '0.9rem', sm: '1rem' },
            fontWeight: 500,
            py: { xs: 1.5, sm: 1 },
            '&:hover': {
              bgcolor: '#1976d2'
            }
          }}
        >
          {loading ? (
            <CircularProgress size={24} color="inherit" />
          ) : activeStep === steps.length - 1 ? (
            'Create Version'
          ) : (
            t('assign_docid.buttons.next')
          )}
        </Button>
      </Box>

      {/* Confirmation Modal */}
      <Dialog
        open={openConfirmModal}
        onClose={handleCloseConfirmModal}
        PaperProps={{
          sx: {
            borderRadius: 2,
            minWidth: { xs: '90vw', sm: '400px' },
            maxWidth: { xs: '95vw', sm: '600px' },
            m: { xs: 2, sm: 3 }
          }
        }}
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon sx={{ color: '#ff9800', fontSize: 28 }} />
          Confirm Version Creation
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            You are about to create a new version of &quot;{selectedParent?.document_title}&quot;.
            This will generate a new DOCiD linked to the parent. Continue?
          </Typography>
        </DialogContent>
        <DialogActions sx={{
          px: { xs: 2, sm: 3 },
          pb: { xs: 2, sm: 3 },
          gap: { xs: 1, sm: 2 },
          flexDirection: { xs: 'column', sm: 'row' }
        }}>
          <Button
            onClick={handleCloseConfirmModal}
            variant="outlined"
            fullWidth={isMobile}
            sx={{
              borderColor: '#1565c0',
              color: '#1565c0',
              order: { xs: 2, sm: 1 },
            }}
          >
            {t('assign_docid.buttons.cancel')}
          </Button>
          <Button
            onClick={handleConfirmSubmit}
            variant="contained"
            fullWidth={isMobile}
            sx={{
              bgcolor: '#1565c0',
              order: { xs: 1, sm: 2 },
              '&:hover': { bgcolor: '#1976d2' }
            }}
          >
            Create Version
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

      {/* Form container */}
      <Container
        maxWidth={false}
        sx={{
          px: { xs: 1, sm: 2, md: 4 },
          maxWidth: { xs: '100%', sm: '600px', md: '900px', lg: '1200px', xl: '1400px' }
        }}>
        <Paper
          elevation={0}
          sx={{
            p: { xs: 2, sm: 3, md: 4 },
            borderRadius: { xs: 1, sm: 2 },
            bgcolor: 'background.paper'
          }}
        >
          {parentLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
              <Typography sx={{ ml: 2 }}>Loading parent data...</Typography>
            </Box>
          ) : activeStep === steps.length ? (
            <Box sx={{ textAlign: 'center' }}>
              <Button
                onClick={() => { window.location.href = '/list-docids'; }}
                variant="contained"
                size={isMobile ? 'large' : 'medium'}
                fullWidth={isMobile}
                sx={{
                  mt: 2,
                  bgcolor: '#1565c0',
                  color: 'white',
                  py: { xs: 1.5, sm: 1 },
                  '&:hover': { bgcolor: '#1976d2' }
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

const VersionDocID = () => {
  return (
    <Suspense fallback={<Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>}>
      <VersionDocIDInner />
    </Suspense>
  );
};

export default VersionDocID;
