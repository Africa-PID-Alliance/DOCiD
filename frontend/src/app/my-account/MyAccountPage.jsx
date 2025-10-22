"use client";

import React, { useEffect, useState, useMemo, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,
  Avatar,
  Button,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  IconButton,
  Pagination,
  useTheme,
  alpha,
  Chip,
  Modal,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  Lock as LockIcon,
  Folder as FolderIcon,
  Star as StarIcon,
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon,
  Edit as EditIcon,
  ContentCopy as ContentCopyIcon,
  Visibility as VisibilityIcon,
  Delete as DeleteIcon,
  VerifiedUser as VerifiedUserIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { useRouter } from 'next/navigation';
import { allCountries, faculties } from '@/data/locationData';
import { useTranslation } from 'react-i18next';
import axios from 'axios'; // Added axios import

const MyAccountPage = () => {
  const router = useRouter();
  const { t } = useTranslation();
  const { user, isAuthenticated } = useSelector((state) => state.auth);
  const [expanded, setExpanded] = useState(false);
  const theme = useTheme();
  const [openEditModal, setOpenEditModal] = useState(false);
  const [loadingOrcid, setLoadingOrcid] = useState(false);
  const [orcidData, setOrcidData] = useState(null);
  const [orcidError, setOrcidError] = useState(null);
  const [userPublications, setUserPublications] = useState([]);
  const [publicationsLoading, setPublicationsLoading] = useState(false);
  const [userStatistics, setUserStatistics] = useState(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [publicationToDelete, setPublicationToDelete] = useState(null);
  const [editFormData, setEditFormData] = useState({
    fullName: user?.name || '',
    email: user?.email || '',
    format: '',
    faculty: '',
    role: '',
    country: '',
    city: '',
    location: '',
    orcid_id: '',
    ror_id: '',
    linkedin_profile_link: '',
    facebook_profile_link: '',
    x_profile_link: '',
    instagram_profile_link: '',
    github_profile_link: '',
    profileImage: null
  });

  // Function to extract ORCID ID from email
  const extractOrcidFromEmail = (email) => {
    if (!email) return null;
    
    // Check if email ends with @orcid.org and extract the ORCID ID part
    const orcidPattern = /^(\d{4}-\d{4}-\d{4}-\d{4})@orcid\.org$/i;
    const match = email.match(orcidPattern);
    
    return match ? match[1] : null;
  };

  // Function to get ORCID ID from various sources
  const getOrcidId = () => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      const userData = JSON.parse(storedUser);
      
      // First try to get direct ORCID ID
      if (userData.orcid) {
        return userData.orcid;
      }
      
      // If no direct ORCID ID, try to extract from email
      if (userData.email) {
        const extractedOrcid = extractOrcidFromEmail(userData.email);
        if (extractedOrcid) {
          return extractedOrcid;
        }
      }
    }
    
    // Also try from Redux user state
    if (user?.orcid) {
      return user.orcid;
    }
    
    if (user?.email) {
      const extractedOrcid = extractOrcidFromEmail(user.email);
      if (extractedOrcid) {
        return extractedOrcid;
      }
    }
    
    return null;
  };

  const handleEditModalOpen = () => setOpenEditModal(true);
  const handleEditModalClose = () => setOpenEditModal(false);

  const handleEditFormChange = (event) => {
    const { name, value } = event.target;
    setEditFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setEditFormData(prev => ({
      ...prev,
      profileImage: file
    }));
  };

  const handleUpdateProfile = async (e) => {
    // Prevent default form submission if event is passed
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    if (!user?.id) return;

    try {
      const updatePayload = {
        full_name: editFormData.fullName,
        email: editFormData.email,
        affiliation: editFormData.faculty,
        role: editFormData.role,
        country: editFormData.country,
        city: editFormData.city,
        location: editFormData.location,
        orcid_id: editFormData.orcid_id,
        ror_id: editFormData.ror_id,
        linkedin_profile_link: editFormData.linkedin_profile_link,
        facebook_profile_link: editFormData.facebook_profile_link,
        x_profile_link: editFormData.x_profile_link,
        instagram_profile_link: editFormData.instagram_profile_link,
        github_profile_link: editFormData.github_profile_link,
      };

      const response = await axios.put(
        `/api/user-profile/${user.id}`,
        updatePayload
      );

      if (response.data.message === 'User profile updated successfully') {
        console.log('Profile updated successfully:', response.data);
        // Refetch user data
        fetchUserStatistics();
        handleEditModalClose();
        // Show success message
        alert('Profile updated successfully!');
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Failed to update profile. Please try again.');
    }
  };

  // Function to fetch user's publications using new API endpoint
  const fetchUserPublications = async () => {
    if (!user?.id) return;

    try {
      setPublicationsLoading(true);

      // Use the new user-profile publications endpoint
      const response = await axios.get(`/api/user-profile/${user.id}/publications`, {
        params: {
          page: 1,
          page_size: 10,
          sort: 'published',
          order: 'desc'
        }
      });

      // The new API returns publications directly
      setUserPublications(response.data.publications || []);

      console.log('User publications:', response.data);
    } catch (error) {
      console.error('Error fetching user publications:', error);

      // Fallback to old API if new one fails
      try {
        const fallbackResponse = await axios.get('/api/publications/get-publications');
        const userPubs = fallbackResponse.data.data.filter(pub => pub.user_id === user.id);
        setUserPublications(userPubs);
      } catch (fallbackError) {
        console.error('Fallback also failed:', fallbackError);
        setUserPublications([]);
      }
    } finally {
      setPublicationsLoading(false);
    }
  };

  // Function to fetch ORCID data
  const fetchOrcidData = async (orcidId, accessToken) => {
    if (!orcidId) {
      console.log('No ORCID ID provided, skipping ORCID data fetch');
      return;
    }
    
    console.log('Attempting to fetch ORCID data for:', orcidId);
    console.log('Access token available:', !!accessToken);
    
    setLoadingOrcid(true);
    setOrcidError(null);
    try {
      const apiUrl = `/api/orcid?orcidId=${orcidId}&accessToken=${accessToken || ''}`;
      console.log('Fetching from:', apiUrl);
      
      const response = await fetch(apiUrl);
      
      console.log('ORCID API response status:', response.status);
      console.log('ORCID API response headers:', Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('ORCID API error response:', errorText);
        throw new Error(`Failed to fetch ORCID data: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('ORCID data received:', data);
      setOrcidData(data);
      
      // Update form data with ORCID information (with safe access)
      if (data.name) {
        setEditFormData(prev => ({
          ...prev,
          fullName: (data.name['given-names']?.value || '') + ' ' + (data.name['family-name']?.value || ''),
          faculty: data.employments?.['employment-summary']?.[0]?.department || '',
          country: data.addresses?.['address']?.[0]?.country || ''
        }));
      }

    } catch (error) {
      console.error('Error fetching ORCID data:', error);
      console.error('Error details:', error.message);
      
      // Check if it's a network error or API not found
      if (error.message.includes('404')) {
        setOrcidError('ORCID API endpoint not available. ORCID features disabled.');
        console.warn('ORCID API endpoint not found - continuing without ORCID data');
      } else if (error.message.includes('Failed to fetch')) {
        setOrcidError('Network error while fetching ORCID data.');
        console.warn('Network error fetching ORCID data - continuing without ORCID data');
      } else {
        setOrcidError('Failed to fetch ORCID data. ORCID features may be limited.');
      }
    } finally {
      setLoadingOrcid(false);
    }
  };

  // Fetch ORCID data when component mounts (optional)
  useEffect(() => {
    const orcidId = getOrcidId();
    console.log("Orcid ID", orcidId);
    if (orcidId) {
      const storedUser = localStorage.getItem('user');
      const userData = storedUser ? JSON.parse(storedUser) : {};
      
      // Only fetch ORCID data if we have both ID and access token
      if (userData.accessToken) {
        console.log('Both ORCID ID and access token available, fetching ORCID data');
        // Make ORCID fetch optional - don't block page if it fails
        fetchOrcidData(orcidId, userData.accessToken).catch(error => {
          console.warn('ORCID fetch failed, continuing without ORCID data:', error);
        });
      } else {
        console.log('No ORCID access token available, skipping ORCID data fetch');
        console.log('Page will work with basic user data only');
      }
    } else {
      console.log('No ORCID ID found, page will work without ORCID data');
    }
  }, []);

  // Function to fetch user statistics
  const fetchUserStatistics = async () => {
    if (!user?.id) return;

    try {
      const response = await axios.get(`/api/user-profile/${user.id}/statistics`);
      setUserStatistics(response.data);
      console.log('User statistics:', response.data);
    } catch (error) {
      console.error('Error fetching user statistics:', error);
    }
  };

  // Fetch user publications and statistics when user is available
  useEffect(() => {
    if (user?.id) {
      fetchUserPublications();
      fetchUserStatistics();
    }
  }, [user?.id]);

  // Redirect if not authenticated (only once on mount)
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const categories = [
    { title: t('my_account.categories.total_docids'), count: userStatistics?.total_publications || user?.total_docids || 0, icon: DescriptionIcon },
    { title: t('my_account.categories.indigenous_knowledge'), count: user?.indigenous_knowledge_count || 0, icon: FolderIcon },
    { title: t('my_account.categories.panfest'), count: user?.panfest_count || 0, icon: FolderIcon },
    { title: t('my_account.categories.cultural_heritage'), count: user?.cultural_heritage_count || 0, icon: FolderIcon },
    { title: t('my_account.categories.project'), count: user?.project_count || 0, icon: FolderIcon },
    { title: t('my_account.categories.funder'), count: user?.funder_count || 0, icon: FolderIcon },
    { title: t('my_account.categories.dmp'), count: user?.dmp_count || 0, icon: FolderIcon },
    { title: t('my_account.categories.favorite_docids'), count: user?.favorite_docids_count || 0, icon: StarIcon },
  ];

  // Update basicInfoFields with ORCID data
  const basicInfoFields = [
    { 
      label: t('my_account.fields.full_name'), 
      value: orcidData?.name ? 
        `${orcidData.name['given-names']?.value || ''} ${orcidData.name['family-name']?.value || ''}`.trim() : 
        user?.name || t('my_account.common.n_a'),
      loading: loadingOrcid
    },
    { 
      label: t('my_account.fields.email'), 
      value: orcidData?.emails?.email?.[0]?.email?.value || user?.email || t('my_account.common.n_a'),
      loading: loadingOrcid 
    },
    { 
      label: t('my_account.fields.affiliation'), 
      value: orcidData?.employments?.['employment-summary']?.[0]?.organization?.name?.value || user?.affiliation || t('my_account.common.n_a'),
      loading: loadingOrcid
    },
    { 
      label: t('my_account.fields.role'), 
      value: orcidData?.employments?.['employment-summary']?.[0]?.role?.value || user?.role || t('my_account.common.n_a'),
      loading: loadingOrcid
    },
    { 
      label: t('my_account.fields.orcid_id'), 
      value: getOrcidId() || t('my_account.common.n_a'),
      loading: false
    },
    { 
      label: t('my_account.fields.ror_id'), 
      value: orcidData?.employments?.['employment-summary']?.[0]?.organization?.['disambiguated-organization']?.['disambiguated-organization-identifier']?.value || user?.ror_id || t('my_account.common.n_a'),
      loading: loadingOrcid
    },
    { 
      label: t('my_account.fields.location'), 
      value: orcidData?.addresses?.['address']?.[0]?.country?.value || user?.location || t('my_account.common.n_a'),
      loading: loadingOrcid
    },
  ];

  // Update professionalFields with ORCID data
  const professionalFields = [
    { 
      label: t('my_account.fields.research_field'), 
      value: t('my_account.common.no_data_available')
    },
    { 
      label: t('my_account.fields.years_experience'), 
      value: t('my_account.common.no_data_available')
    },
    { 
      label: t('my_account.fields.languages'), 
      value: t('my_account.common.no_data_available')
    },
  ];

  const researchFields = [
    { 
      label: t('my_account.fields.active_projects'), 
      value: user?.active_projects || ''
    },
    { 
      label: t('my_account.fields.data_management_plan'), 
      value: user?.data_management_plan || ''
    },
    { 
      label: t('my_account.fields.pid_for_projects'), 
      value: user?.pid_for_projects || ''
    },
  ];

  // Update publicationFields with ORCID data
  const publicationFields = [
    { 
      label: t('my_account.fields.recent_publications'), 
      value: t('my_account.common.no_data_available')
    },
    { 
      label: t('my_account.fields.preprints'), 
      value: t('my_account.common.no_data_available')
    },
    { 
      label: t('my_account.fields.other_research_outputs'), 
      value: t('my_account.common.no_data_available')
    },
  ];

  // Update fundingFields with ORCID data
  const fundingFields = [
    { 
      label: t('my_account.fields.funder_information'), 
      value: t('my_account.common.no_data_available')
    },
    { 
      label: t('my_account.fields.grants'), 
      value: t('my_account.common.no_data_available')
    },
  ];

  // Update collaborationFields with ORCID data
  const collaborationFields = [
    { 
      label: t('my_account.fields.coauthors_collaborators'), 
      value: t('my_account.common.no_data_available')
    },
    { 
      label: t('my_account.fields.institutional_affiliations'), 
      value: t('my_account.common.no_data_available')
    },
  ];

  // Update externalIdentifierFields with ORCID data
  const externalIdentifierFields = [
    { 
      label: t('my_account.fields.orcid'), 
      value: t('my_account.common.no_data_available')
    },
    { 
      label: t('my_account.fields.researcher_id'), 
      value: t('my_account.common.no_data_available')
    },
    { 
      label: t('my_account.fields.scopus_author_id'), 
      value: t('my_account.common.no_data_available')
    },
    { 
      label: t('my_account.fields.google_scholar_profile'), 
      value: t('my_account.common.no_data_available')
    },
  ];

  // Update licensingFields with ORCID data
  const licensingFields = [
    { 
      label: t('my_account.fields.preferred_licensing'), 
      value: t('my_account.common.no_data_available')
    },
    { 
      label: t('my_account.fields.data_sharing_preferences'), 
      value: t('my_account.common.no_data_available')
    },
  ];

  // Update contactFields with ORCID data
  const contactFields = [
    { 
      label: t('my_account.fields.primary_contact'), 
      value: t('my_account.common.no_data_available')
    },
    { 
      label: t('my_account.fields.public_profile_link'), 
      value: t('my_account.common.no_data_available')
    },
  ];

  const handleAccordionChange = (panel) => (event, isExpanded) => {
    setExpanded(isExpanded ? panel : false);
  };

  // Handle delete publication
  const handleDeleteClick = (publication) => {
    setPublicationToDelete(publication);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!publicationToDelete) return;

    try {
      // Try to delete using the publication ID
      const docid = publicationToDelete.document_docid || publicationToDelete.docid;

      // Get JWT token from user state or localStorage
      const accessToken = user?.accessToken;

      // Note: This assumes there's a delete endpoint - if not, we show a warning
      const response = await axios.delete(`/api/publications/${publicationToDelete.id}`, {
        headers: accessToken ? {
          'Authorization': `Bearer ${accessToken}`
        } : {}
      });

      if (response.status === 200) {
        // Remove from local state
        setUserPublications(prev =>
          prev.filter(pub => pub.id !== publicationToDelete.id)
        );

        // Refetch statistics
        fetchUserStatistics();

        alert('Publication deleted successfully!');
      }
    } catch (error) {
      console.error('Error deleting publication:', error);

      // Get error message from response if available
      const errorMessage = error.response?.data?.error || error.message;

      // Show appropriate error message
      if (error.response?.status === 401) {
        alert('Authentication required. Please log in again.');
      } else if (error.response?.status === 403) {
        alert(errorMessage || 'You do not have permission to delete this publication.');
      } else if (error.response?.status === 404) {
        alert(errorMessage || 'Publication not found.');
      } else {
        alert(errorMessage || 'Failed to delete publication. Please try again.');
      }
    } finally {
      setDeleteConfirmOpen(false);
      setPublicationToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirmOpen(false);
    setPublicationToDelete(null);
  };

  const accordionSections = [
    { 
      id: 'basic', 
      title: t('my_account.sections.basic_information'),
      content: (
        <Box sx={{ p: 2, backgroundColor: 'background.paper', borderRadius: 2 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 2
          }}>
            <Typography 
              variant="subtitle1" 
              sx={{ 
                color: 'primary.main',
                fontWeight: 500
              }}
            >
              {t('my_account.sections.basic_information')}
            </Typography>
            <Button 
              onClick={handleEditModalOpen}
              sx={{ 
                minWidth: 'auto', 
                p: 1,
                color: theme.palette.mode === 'dark' ? theme.palette.common.white : '#1565c0',
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? alpha(theme.palette.common.white, 0.1) 
                    : alpha('#1565c0', 0.1)
                }
              }}
            >
              <EditIcon fontSize="small" />
            </Button>
          </Box>
          {basicInfoFields.map((field, index) => (
            <Box 
              key={index} 
              sx={{ 
                display: 'flex',
                mb: index !== basicInfoFields.length - 1 ? 2 : 0
              }}
            >
              <Typography 
                sx={{ 
                  color: 'primary.main',
                  width: '120px',
                  flexShrink: 0
                }}
              >
                {field.label}
              </Typography>
              {field.loading ? (
                <CircularProgress size={20} sx={{ ml: 2 }} />
              ) : (
                <Typography sx={{ color: 'text.primary' }}>
                  {field.value}
                </Typography>
              )}
            </Box>
          ))}
        </Box>
      )
    },
    { 
      id: 'professional', 
      title: t('my_account.sections.professional_background'),
      content: (
        <Box sx={{ p: 2, backgroundColor: 'background.paper', borderRadius: 2 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 2
          }}>
            <Typography 
              variant="subtitle1" 
              sx={{ 
                color: 'primary.main',
                fontWeight: 500
              }}
            >
              {t('my_account.sections.professional_background')}
            </Typography>
            <Button 
              sx={{ 
                minWidth: 'auto', 
                p: 1,
                color: theme.palette.mode === 'dark' ? theme.palette.common.white : '#1565c0',
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? alpha(theme.palette.common.white, 0.1) 
                    : alpha('#1565c0', 0.1)
                }
              }}
            >
              <EditIcon fontSize="small" />
            </Button>
          </Box>

          <Typography 
            sx={{ 
              color: 'text.primary', 
              mb: 3,
              lineHeight: 1.6
            }}
          >
            {user?.professional_description || 
              ""}
          </Typography>

          {professionalFields.map((field, index) => (
            <Box 
              key={index} 
              sx={{ 
                display: 'flex',
                mb: index !== professionalFields.length - 1 ? 2 : 0
              }}
            >
              <Typography 
                sx={{ 
                  color: 'primary.main',
                  width: '160px',
                  flexShrink: 0
                }}
              >
                {field.label}
              </Typography>
              <Typography sx={{ color: 'text.primary' }}>
                {field.value}
              </Typography>
            </Box>
          ))}
        </Box>
      )
    },
    { 
      id: 'research', 
      title: t('my_account.sections.research_projects'),
      content: (
        <Box sx={{ p: 2, backgroundColor: 'background.paper', borderRadius: 2 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 2
          }}>
            <Typography 
              variant="subtitle1" 
              sx={{ 
                color: 'primary.main',
                fontWeight: 500
              }}
            >
              {t('my_account.sections.research_projects')}
            </Typography>
            <Button 
              sx={{ 
                minWidth: 'auto', 
                p: 1,
                color: theme.palette.mode === 'dark' ? theme.palette.common.white : '#1565c0',
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? alpha(theme.palette.common.white, 0.1) 
                    : alpha('#1565c0', 0.1)
                }
              }}
            >
              <EditIcon fontSize="small" />
            </Button>
          </Box>

          {researchFields.map((field, index) => (
            <Box 
              key={index} 
              sx={{ 
                display: 'flex',
                mb: index !== researchFields.length - 1 ? 2 : 0
              }}
            >
              <Typography 
                sx={{ 
                  color: 'primary.main',
                  width: '180px',
                  flexShrink: 0
                }}
              >
                {field.label}
              </Typography>
              <Typography sx={{ color: 'text.primary' }}>
                {field.value}
              </Typography>
            </Box>
          ))}
        </Box>
      )
    },
    { 
      id: 'publications', 
      title: t('my_account.sections.publications_outputs'),
      content: (
        <Box sx={{ p: 2, backgroundColor: 'background.paper', borderRadius: 2 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 2
          }}>
            <Typography 
              variant="subtitle1" 
              sx={{ 
                color: 'primary.main',
                fontWeight: 500
              }}
            >
              {t('my_account.sections.publications_outputs')}
            </Typography>
            <Button 
              sx={{ 
                minWidth: 'auto', 
                p: 1,
                color: theme.palette.mode === 'dark' ? theme.palette.common.white : '#1565c0',
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? alpha(theme.palette.common.white, 0.1) 
                    : alpha('#1565c0', 0.1)
                }
              }}
            >
              <EditIcon fontSize="small" />
            </Button>
          </Box>

          {publicationFields.map((field, index) => (
            <Box 
              key={index} 
              sx={{ 
                display: 'flex',
                mb: index !== publicationFields.length - 1 ? 2 : 0
              }}
            >
              <Typography 
                sx={{ 
                  color: 'primary.main',
                  width: '180px',
                  flexShrink: 0
                }}
              >
                {field.label}
              </Typography>
              <Typography sx={{ color: 'text.primary' }}>
                {field.value}
              </Typography>
            </Box>
          ))}
        </Box>
      )
    },
    { 
      id: 'funding', 
      title: t('my_account.sections.funding'),
      content: (
        <Box sx={{ p: 2, backgroundColor: 'background.paper', borderRadius: 2 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 2
          }}>
            <Typography 
              variant="subtitle1" 
              sx={{ 
                color: 'primary.main',
                fontWeight: 500
              }}
            >
              {t('my_account.sections.funding')}
            </Typography>
            <Button 
              sx={{ 
                minWidth: 'auto', 
                p: 1,
                color: theme.palette.mode === 'dark' ? theme.palette.common.white : '#1565c0',
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? alpha(theme.palette.common.white, 0.1) 
                    : alpha('#1565c0', 0.1)
                }
              }}
            >
              <EditIcon fontSize="small" />
            </Button>
          </Box>

          {fundingFields.map((field, index) => (
            <Box 
              key={index} 
              sx={{ 
                display: 'flex',
                mb: index !== fundingFields.length - 1 ? 2 : 0
              }}
            >
              <Typography 
                sx={{ 
                  color: 'primary.main',
                  width: '180px',
                  flexShrink: 0
                }}
              >
                {field.label}
              </Typography>
              <Typography sx={{ color: 'text.primary' }}>
                {field.value}
              </Typography>
            </Box>
          ))}
        </Box>
      )
    },
    { 
      id: 'collaboration', 
      title: t('my_account.sections.collaboration'),
      content: (
        <Box sx={{ p: 2, backgroundColor: 'background.paper', borderRadius: 2 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 2
          }}>
            <Typography 
              variant="subtitle1" 
              sx={{ 
                color: 'primary.main',
                fontWeight: 500
              }}
            >
              {t('my_account.sections.collaboration')}
            </Typography>
            <Button 
              sx={{ 
                minWidth: 'auto', 
                p: 1,
                color: theme.palette.mode === 'dark' ? theme.palette.common.white : '#1565c0',
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? alpha(theme.palette.common.white, 0.1) 
                    : alpha('#1565c0', 0.1)
                }
              }}
            >
              <EditIcon fontSize="small" />
            </Button>
          </Box>

          {collaborationFields.map((field, index) => (
            <Box 
              key={index} 
              sx={{ 
                display: 'flex',
                mb: index !== collaborationFields.length - 1 ? 2 : 0
              }}
            >
              <Typography 
                sx={{ 
                  color: 'primary.main',
                  width: '180px',
                  flexShrink: 0
                }}
              >
                {field.label}
              </Typography>
              <Typography sx={{ color: 'text.primary' }}>
                {field.value}
              </Typography>
            </Box>
          ))}
        </Box>
      )
    },
    { 
      id: 'external', 
      title: t('my_account.sections.external_identifiers'),
      content: (
        <Box sx={{ p: 2, backgroundColor: 'background.paper', borderRadius: 2 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 2
          }}>
            <Typography 
              variant="subtitle1" 
              sx={{ 
                color: 'primary.main',
                fontWeight: 500
              }}
            >
              {t('my_account.sections.external_identifiers')}
            </Typography>
            <Button 
              sx={{ 
                minWidth: 'auto', 
                p: 1,
                color: theme.palette.mode === 'dark' ? theme.palette.common.white : '#1565c0',
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? alpha(theme.palette.common.white, 0.1) 
                    : alpha('#1565c0', 0.1)
                }
              }}
            >
              <EditIcon fontSize="small" />
            </Button>
          </Box>

          {externalIdentifierFields.map((field, index) => (
            <Box 
              key={index} 
              sx={{ 
                display: 'flex',
                mb: index !== externalIdentifierFields.length - 1 ? 2 : 0
              }}
            >
              <Typography 
                sx={{ 
                  color: 'primary.main',
                  width: '180px',
                  flexShrink: 0
                }}
              >
                {field.label}
              </Typography>
              <Typography sx={{ color: 'text.primary' }}>
                {field.value}
              </Typography>
            </Box>
          ))}
        </Box>
      )
    },
    { 
      id: 'licensing', 
      title: t('my_account.sections.licensing_data_sharing'),
      content: (
        <Box sx={{ p: 2, backgroundColor: 'background.paper', borderRadius: 2 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 2
          }}>
            <Typography 
              variant="subtitle1" 
              sx={{ 
                color: 'primary.main',
                fontWeight: 500
              }}
            >
              {t('my_account.sections.licensing_data_sharing')}
            </Typography>
            <Button 
              sx={{ 
                minWidth: 'auto', 
                p: 1,
                color: theme.palette.mode === 'dark' ? theme.palette.common.white : '#1565c0',
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? alpha(theme.palette.common.white, 0.1) 
                    : alpha('#1565c0', 0.1)
                }
              }}
            >
              <EditIcon fontSize="small" />
            </Button>
          </Box>

          {licensingFields.map((field, index) => (
            <Box 
              key={index} 
              sx={{ 
                display: 'flex',
                mb: index !== licensingFields.length - 1 ? 2 : 0
              }}
            >
              <Typography 
                sx={{ 
                  color: 'primary.main',
                  width: '280px',
                  flexShrink: 0
                }}
              >
                {field.label}
              </Typography>
              <Typography sx={{ color: 'text.primary' }}>
                {field.value}
              </Typography>
            </Box>
          ))}
        </Box>
      )
    },
    { 
      id: 'contact', 
      title: t('my_account.sections.contact_information'),
      content: (
        <Box sx={{ p: 2, backgroundColor: 'background.paper', borderRadius: 2 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 2
          }}>
            <Typography 
              variant="subtitle1" 
              sx={{ 
                color: 'primary.main',
                fontWeight: 500
              }}
            >
              {t('my_account.sections.contact_information')}
            </Typography>
            <Button 
              sx={{ 
                minWidth: 'auto', 
                p: 1,
                color: theme.palette.mode === 'dark' ? theme.palette.common.white : '#1565c0',
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? alpha(theme.palette.common.white, 0.1) 
                    : alpha('#1565c0', 0.1)
                }
              }}
            >
              <EditIcon fontSize="small" />
            </Button>
          </Box>

          {contactFields.map((field, index) => (
            <Box 
              key={index} 
              sx={{ 
                display: 'flex',
                mb: index !== contactFields.length - 1 ? 2 : 0
              }}
            >
              <Typography 
                sx={{ 
                  color: 'primary.main',
                  width: '180px',
                  flexShrink: 0
                }}
              >
                {field.label}
              </Typography>
              <Typography sx={{ color: 'text.primary' }}>
                {field.value}
              </Typography>
            </Box>
          ))}
        </Box>
      )
    },
  ];

  // Memoize modal BEFORE any conditional returns (Rules of Hooks)
  const EditProfileModal = useMemo(() => (
    <Modal
      open={openEditModal}
      onClose={handleEditModalClose}
      aria-labelledby="edit-profile-modal"
      aria-describedby="edit-profile-form"
    >
      <Box
        component="form"
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          return false;
        }}
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: { xs: '90%', sm: '80%', md: '60%', lg: '50%' },
          maxWidth: '600px',
          bgcolor: 'background.paper',
          borderRadius: 2,
          boxShadow: 24,
          p: 4,
          outline: 'none',
        }}
      >
        <Box sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 3
        }}>
          <Typography variant="h6" component="h2" sx={{ color: 'text.primary', mb: 2 }}>
            {t('my_account.edit_profile')}
          </Typography>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Box sx={{ 
              width: 150, 
              height: 150, 
              borderRadius: '50%',
              border: `2px dashed ${theme.palette.mode === 'dark' ? '#ffffff40' : '#00000040'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'hidden',
              position: 'relative',
              backgroundColor: theme.palette.mode === 'dark' ? '#ffffff08' : '#00000008',
            }}>
              {editFormData.profileImage ? (
                <img 
                  src={URL.createObjectURL(editFormData.profileImage)} 
                  alt="Profile Preview"
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <Typography color="text.secondary">{t('my_account.form.no_file_chosen')}</Typography>
              )}
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  opacity: 0,
                  cursor: 'pointer'
                }}
              />
            </Box>

            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                name="fullName"
                label={t('my_account.fields.full_name').replace(':', '')}
                value={editFormData.fullName}
                onChange={handleEditFormChange}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                    '& input': {
                      color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                    }
                  },
                  '& .MuiInputLabel-root': {
                    color: theme.palette.mode === 'dark' ? '#aaaaaa' : '#666666',
                  }
                }}
              />
              <TextField
                fullWidth
                name="email"
                label="Email"
                type="email"
                value={editFormData.email}
                onChange={handleEditFormChange}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                    '& input': {
                      color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                    }
                  },
                  '& .MuiInputLabel-root': {
                    color: theme.palette.mode === 'dark' ? '#aaaaaa' : '#666666',
                  }
                }}
              />
            </Box>
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="role"
                label="Role/Position"
                value={editFormData.role}
                onChange={handleEditFormChange}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                    '& input': {
                      color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                    }
                  },
                  '& .MuiInputLabel-root': {
                    color: theme.palette.mode === 'dark' ? '#aaaaaa' : '#666666',
                  }
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>{t('my_account.form.select_faculty')}</InputLabel>
                <Select
                  name="faculty"
                  value={editFormData.faculty}
                  onChange={handleEditFormChange}
                  label={t('my_account.form.select_faculty')}
                  sx={{
                    backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                    color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                  }}
                >
                  {faculties.map((faculty) => (
                    <MenuItem key={faculty} value={faculty}>
                      {faculty}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>{t('my_account.form.select_country')}</InputLabel>
                <Select
                  name="country"
                  value={editFormData.country}
                  onChange={handleEditFormChange}
                  label={t('my_account.form.select_country')}
                  sx={{
                    backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                    color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                  }}
                >
                  {allCountries.map((country) => (
                    <MenuItem key={country} value={country}>
                      {country}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="city"
                label="City"
                value={editFormData.city}
                onChange={handleEditFormChange}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                    '& input': {
                      color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                    }
                  },
                  '& .MuiInputLabel-root': {
                    color: theme.palette.mode === 'dark' ? '#aaaaaa' : '#666666',
                  }
                }}
              />
            </Grid>
          </Grid>

          <TextField
            fullWidth
            name="location"
            label="Location (Custom)"
            value={editFormData.location}
            onChange={handleEditFormChange}
            variant="outlined"
            sx={{
              '& .MuiOutlinedInput-root': {
                backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                '& input': {
                  color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                }
              },
              '& .MuiInputLabel-root': {
                color: theme.palette.mode === 'dark' ? '#aaaaaa' : '#666666',
              }
            }}
          />

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="orcid_id"
                label="ORCID iD"
                placeholder="0000-0000-0000-0000"
                value={editFormData.orcid_id}
                onChange={handleEditFormChange}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                    '& input': {
                      color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                    }
                  },
                  '& .MuiInputLabel-root': {
                    color: theme.palette.mode === 'dark' ? '#aaaaaa' : '#666666',
                  }
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="ror_id"
                label="ROR ID"
                value={editFormData.ror_id}
                onChange={handleEditFormChange}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                    '& input': {
                      color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                    }
                  },
                  '& .MuiInputLabel-root': {
                    color: theme.palette.mode === 'dark' ? '#aaaaaa' : '#666666',
                  }
                }}
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
            Social Media Links
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="linkedin_profile_link"
                label="LinkedIn"
                placeholder="https://linkedin.com/in/username"
                value={editFormData.linkedin_profile_link}
                onChange={handleEditFormChange}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                    '& input': {
                      color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                    }
                  },
                  '& .MuiInputLabel-root': {
                    color: theme.palette.mode === 'dark' ? '#aaaaaa' : '#666666',
                  }
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="github_profile_link"
                label="GitHub"
                placeholder="https://github.com/username"
                value={editFormData.github_profile_link}
                onChange={handleEditFormChange}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                    '& input': {
                      color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                    }
                  },
                  '& .MuiInputLabel-root': {
                    color: theme.palette.mode === 'dark' ? '#aaaaaa' : '#666666',
                  }
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="x_profile_link"
                label="X (Twitter)"
                placeholder="https://x.com/username"
                value={editFormData.x_profile_link}
                onChange={handleEditFormChange}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                    '& input': {
                      color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                    }
                  },
                  '& .MuiInputLabel-root': {
                    color: theme.palette.mode === 'dark' ? '#aaaaaa' : '#666666',
                  }
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="facebook_profile_link"
                label="Facebook"
                placeholder="https://facebook.com/username"
                value={editFormData.facebook_profile_link}
                onChange={handleEditFormChange}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                    '& input': {
                      color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                    }
                  },
                  '& .MuiInputLabel-root': {
                    color: theme.palette.mode === 'dark' ? '#aaaaaa' : '#666666',
                  }
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="instagram_profile_link"
                label="Instagram"
                placeholder="https://instagram.com/username"
                value={editFormData.instagram_profile_link}
                onChange={handleEditFormChange}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#ffffff',
                    '& input': {
                      color: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                    }
                  },
                  '& .MuiInputLabel-root': {
                    color: theme.palette.mode === 'dark' ? '#aaaaaa' : '#666666',
                  }
                }}
              />
            </Grid>
          </Grid>

          <Button
            fullWidth
            variant="contained"
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleUpdateProfile(e);
            }}
            sx={{
              mt: 2,
              backgroundColor: theme.palette.mode === 'dark' ? '#141a3b' : '#1565c0',
              color: theme.palette.common.white,
              '&:hover': {
                backgroundColor: theme.palette.mode === 'dark'
                  ? alpha('#141a3b', 0.8)
                  : alpha('#1565c0', 0.8),
              }
            }}
          >
            {t('my_account.update_profile_btn')}
          </Button>
        </Box>
      </Box>
    </Modal>
  ), [openEditModal, editFormData, theme, t, handleEditModalClose, handleEditFormChange, handleFileChange, handleUpdateProfile]);

  // Show loading state while checking authentication
  if (!isAuthenticated) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'background.default'
        }}
      >
        <Typography>{t('my_account.loading')}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', pt: 4, pb: 4, backgroundColor: 'background.content' }}>
      <Container maxWidth="xl">
        {/* Top Profile Section */}
        <Grid container spacing={3}>
          {/* Left Profile Column */}
          <Grid item xs={12} md={3}>
            <Paper 
              elevation={0} 
              sx={{ 
                p: 3, 
                borderRadius: 2,
                backgroundColor: 'background.paper',
                boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
              }}
            >
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
                <Avatar
                  src={user?.picture || '/default-avatar.png'}
                  alt={user?.name || 'User'}
                  sx={{ width: 100, height: 100, mb: 2 }}
                />
                <Typography variant="h6" fontWeight={600}>
                  {user?.name }
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {user?.email}
                </Typography>
                <Chip
                  icon={<VerifiedUserIcon />}
                  label={t('my_account.verified_account')}
                  color="success"
                  variant="outlined"
                  sx={{ mb: 1 }}
                />
              </Box>
            </Paper>
          </Grid>

          {/* Right Statistics Grid */}
          <Grid item xs={12} md={9}>
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h5" fontWeight={600}>
                {t('my_account.greeting')}, {user?.name}
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                sx={{
                  backgroundColor: '#1565c0',
                  '&:hover': {
                    backgroundColor: alpha('#1565c0', 0.8)
                  }
                }}
                onClick={() => router.push('/assign-docid')}
              >
                {t('my_account.assign_docid_btn')}
              </Button>
            </Box>

            <Grid container spacing={2}>
              {[
                { title: 'Total DOCiDs', count: userStatistics?.total_publications || 0, icon: DescriptionIcon },
                { title: 'This Year', count: userStatistics?.publications_this_year || 0, icon: FolderIcon },
                { title: 'This Month', count: userStatistics?.publications_this_month || 0, icon: FolderIcon },
                { title: 'Cultural Heritage', count: 0, icon: FolderIcon },
                { title: 'Project', count: 0, icon: FolderIcon },
                { title: 'Funder', count: 0, icon: FolderIcon },
                { title: 'DMP', count: 0, icon: FolderIcon },
                { title: 'Favorite DOCiDs', count: 0, icon: StarIcon },
              ].map((category, index) => (
                <Grid item xs={12} sm={6} md={3} key={index}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      backgroundColor: 'background.paper',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Box
                        sx={{
                          width: 40,
                          height: 40,
                          borderRadius: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          backgroundColor: '#1565c0',
                          color: 'white',
                          mr: 2,
                        }}
                      >
                        <category.icon />
                      </Box>
                      <Typography variant="h4" fontWeight={600} color="primary">
                        {category.count}
                      </Typography>
                    </Box>
                    <Typography variant="body1" fontWeight={500}>
                      {category.title}
                    </Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Grid>
        </Grid>

        {/* Two Column Layout for Accordion and Table */}
        <Grid container spacing={3} sx={{ mt: 3 }}>
          {/* Left Column - Accordion */}
          <Grid item xs={12} md={6}>
            <Box>
              {accordionSections.map((section) => (
                <Accordion
                  key={section.id}
                  expanded={expanded === section.id}
                  onChange={handleAccordionChange(section.id)}
                  sx={{
                    mb: 1,
                    backgroundColor: 'background.paper',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                    '&:before': {
                      display: 'none',
                    },
                    borderRadius: '8px !important',
                    overflow: 'hidden',
                  }}
                >
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    sx={{
                      backgroundColor: expanded === section.id ? '#1565c0' : 'background.paper',
                      color: expanded === section.id ? 'white' : 'text.primary',
                      '& .MuiAccordionSummary-expandIconWrapper': {
                        color: expanded === section.id ? 'white' : '#1565c0',
                      },
                      '&:hover': {
                        backgroundColor: expanded === section.id ? alpha('#1565c0', 0.8) : '#e3f2fd',
                      },
                    }}
                  >
                    <Typography variant="subtitle1" fontWeight={500}>
                      {section.title}
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    {section.content}
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          </Grid>

          {/* Right Column - Table */}
          <Grid item xs={12} md={6}>
            <Paper
              elevation={0}
              sx={{
                p: 2,
                borderRadius: 2,
                backgroundColor: 'background.paper',
                boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="subtitle1" fontWeight={600}>
                  {t('my_account.table.my_publications')} ({userPublications.length})
                </Typography>
              </Box>
              <Box sx={{ 
                width: '100%',
                backgroundColor: theme.palette.background.default,
                borderRadius: 1,
                overflow: 'auto'
              }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell 
                        sx={{ 
                          fontWeight: 600, 
                          backgroundColor: '#1565c0', 
                          color: 'white', 
                          width: '200px',
                          borderBottom: `1px solid ${theme.palette.divider}`
                        }}
                      >
                        {t('my_account.table.docid')}
                      </TableCell>
                      <TableCell 
                        sx={{ 
                          fontWeight: 600, 
                          backgroundColor: '#1565c0', 
                          color: 'white', 
                          width: '60%',
                          borderBottom: `1px solid ${theme.palette.divider}`
                        }}
                      >
                        {t('my_account.table.title')}
                      </TableCell>
                      <TableCell 
                        align="right" 
                        sx={{ 
                          fontWeight: 600, 
                          backgroundColor: '#1565c0', 
                          color: 'white', 
                          width: '100px',
                          borderBottom: `1px solid ${theme.palette.divider}`
                        }}
                      >
                        {t('my_account.table.action')}
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {publicationsLoading ? (
                      <TableRow>
                        <TableCell 
                          colSpan={3} 
                          align="center"
                          sx={{ py: 4 }}
                        >
                          <CircularProgress size={30} />
                        </TableCell>
                      </TableRow>
                    ) : userPublications.length === 0 ? (
                      <TableRow>
                        <TableCell 
                          colSpan={3} 
                          align="center"
                          sx={{ 
                            py: 4,
                            color: 'text.secondary',
                            fontStyle: 'italic'
                          }}
                        >
                          {t('my_account.table.no_publications_found')}
                        </TableCell>
                      </TableRow>
                    ) : (
                      userPublications.map((publication, index) => (
                      <TableRow 
                          key={publication.id} 
                        sx={{ 
                          '&:nth-of-type(odd)': { 
                            backgroundColor: theme.palette.mode === 'dark' 
                              ? alpha(theme.palette.background.paper, 0.05)
                              : alpha(theme.palette.background.paper, 0.9)
                          }, 
                          '&:nth-of-type(even)': { 
                            backgroundColor: theme.palette.background.paper 
                          }, 
                          '&:hover': { 
                            backgroundColor: theme.palette.action.hover 
                          },
                          '& .MuiTableCell-root': {
                            borderBottom: `1px solid ${theme.palette.divider}`,
                            color: theme.palette.text.primary
                          }
                        }}
                      >
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {publication.document_docid || publication.docid}
                            <IconButton
                              size="small"
                                onClick={() => navigator.clipboard.writeText(publication.document_docid || publication.docid)}
                              sx={{
                                color: '#1565c0',
                                '&:hover': {
                                  backgroundColor: alpha('#1565c0', 0.1)
                                }
                              }}
                            >
                              <ContentCopyIcon fontSize="small" />
                            </IconButton>
                          </Box>
                        </TableCell>
                          <TableCell>
                            <Typography
                              sx={{
                                display: '-webkit-box',
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden',
                                lineHeight: 1.4
                              }}
                            >
                              {publication.document_title || publication.title}
                            </Typography>
                          </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                              onClick={() => router.push(`/docid/${encodeURIComponent(publication.document_docid || publication.docid)}`)}
                            sx={{
                              color: '#1565c0',
                              '&:hover': {
                                backgroundColor: alpha('#1565c0', 0.1)
                              }
                            }}
                          >
                            <VisibilityIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteClick(publication)}
                            sx={{
                              color: theme.palette.error.main,
                              '&:hover': {
                                backgroundColor: alpha(theme.palette.error.main, 0.1)
                              }
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'center', 
                  p: 2,
                  backgroundColor: theme.palette.background.paper
                }}>
                  <Pagination 
                    count={2} 
                    color="primary" 
                    size="small"
                    sx={{
                      '& .MuiPaginationItem-root': {
                        color: theme.palette.text.primary,
                      },
                      '& .Mui-selected': {
                        backgroundColor: '#1565c0',
                        color: 'white',
                        '&:hover': {
                          backgroundColor: alpha('#1565c0', 0.8),
                        }
                      }
                    }} 
                  />
                </Box>
              </Box>
            </Paper>
          </Grid>
        </Grid>
        {EditProfileModal}

        {/* Delete Confirmation Modal */}
        <Modal
          open={deleteConfirmOpen}
          onClose={handleDeleteCancel}
          aria-labelledby="delete-confirmation-modal"
        >
          <Box sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: { xs: '90%', sm: '400px' },
            bgcolor: 'background.paper',
            borderRadius: 2,
            boxShadow: 24,
            p: 4,
            outline: 'none',
          }}>
            <Typography variant="h6" component="h2" sx={{ mb: 2, color: 'text.primary' }}>
              Delete Publication?
            </Typography>
            <Typography sx={{ mb: 3, color: 'text.secondary' }}>
              Are you sure you want to delete "<strong>{publicationToDelete?.document_title || publicationToDelete?.title}</strong>"?
              {' '}This action cannot be undone.
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button
                onClick={handleDeleteCancel}
                variant="outlined"
                sx={{
                  color: theme.palette.text.primary,
                  borderColor: theme.palette.divider
                }}
              >
                Cancel
              </Button>
              <Button
                onClick={handleDeleteConfirm}
                variant="contained"
                color="error"
                sx={{
                  backgroundColor: theme.palette.error.main,
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.error.main, 0.8),
                  }
                }}
              >
                Delete
              </Button>
            </Box>
          </Box>
        </Modal>
      </Container>
    </Box>
  );
};

export default MyAccountPage; 