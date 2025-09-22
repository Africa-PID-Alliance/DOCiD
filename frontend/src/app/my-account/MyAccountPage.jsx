"use client";

import React, { useEffect, useState } from 'react';
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
import axios from 'axios'; // Added axios import

const MyAccountPage = () => {
  const router = useRouter();
  const { user, isAuthenticated } = useSelector((state) => state.auth);
  const [expanded, setExpanded] = useState(false);
  const theme = useTheme();
  const [openEditModal, setOpenEditModal] = useState(false);
  const [loadingOrcid, setLoadingOrcid] = useState(false);
  const [orcidData, setOrcidData] = useState(null);
  const [orcidError, setOrcidError] = useState(null);
  const [userPublications, setUserPublications] = useState([]);
  const [publicationsLoading, setPublicationsLoading] = useState(false);
  const [editFormData, setEditFormData] = useState({
    fullName: user?.name || '',
    format: '',
    faculty: '',
    country: '',
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

  const handleUpdateProfile = () => {
    // Handle profile update logic here
    console.log('Updated profile data:', editFormData);
    handleEditModalClose();
  };

  // Function to fetch user's publications
  const fetchUserPublications = async () => {
    if (!user?.id) return;
    
    try {
      setPublicationsLoading(true);
      const response = await axios.get('/api/publications/get-publications');
      
      // Filter publications by current user's ID
      const userPubs = response.data.data.filter(pub => pub.user_id === user.id);
      setUserPublications(userPubs);
      
      console.log('User publications:', userPubs);
    } catch (error) {
      console.error('Error fetching user publications:', error);
      setUserPublications([]);
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

  // Fetch user publications when user is available
  useEffect(() => {
    if (user?.id) {
      fetchUserPublications();
    }
  }, [user?.id]);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  const categories = [
    { title: 'Total DOCiDs', count: user?.total_docids || 0, icon: DescriptionIcon },
    { title: 'Indigenous Knowledge', count: user?.indigenous_knowledge_count || 0, icon: FolderIcon },
    { title: 'Panfest', count: user?.panfest_count || 0, icon: FolderIcon },
    { title: 'Cultural Heritage', count: user?.cultural_heritage_count || 0, icon: FolderIcon },
    { title: 'Project', count: user?.project_count || 0, icon: FolderIcon },
    { title: 'Funder', count: user?.funder_count || 0, icon: FolderIcon },
    { title: 'DMP', count: user?.dmp_count || 0, icon: FolderIcon },
    { title: 'Favorite DOCiDs', count: user?.favorite_docids_count || 0, icon: StarIcon },
  ];

  // Update basicInfoFields with ORCID data
  const basicInfoFields = [
    { 
      label: 'Full Name:', 
      value: orcidData?.name ? 
        `${orcidData.name['given-names']?.value || ''} ${orcidData.name['family-name']?.value || ''}`.trim() : 
        user?.name || 'N/A',
      loading: loadingOrcid
    },
    { 
      label: 'Email:', 
      value: orcidData?.emails?.email?.[0]?.email?.value || user?.email || 'N/A',
      loading: loadingOrcid 
    },
    { 
      label: 'Affiliation:', 
      value: orcidData?.employments?.['employment-summary']?.[0]?.organization?.name?.value || user?.affiliation || 'N/A',
      loading: loadingOrcid
    },
    { 
      label: 'Role:', 
      value: orcidData?.employments?.['employment-summary']?.[0]?.role?.value || user?.role || 'N/A',
      loading: loadingOrcid
    },
    { 
      label: 'ORCID ID:', 
      value: getOrcidId() || 'N/A',
      loading: false
    },
    { 
      label: 'ROR ID:', 
      value: orcidData?.employments?.['employment-summary']?.[0]?.organization?.['disambiguated-organization']?.['disambiguated-organization-identifier']?.value || user?.ror_id || 'N/A',
      loading: loadingOrcid
    },
    { 
      label: 'Location:', 
      value: orcidData?.addresses?.['address']?.[0]?.country?.value || user?.location || 'N/A',
      loading: loadingOrcid
    },
  ];

  // Update professionalFields with ORCID data
  const professionalFields = [
    { 
      label: 'Research Field:', 
      value: 'No data available'
    },
    { 
      label: 'Years Of Experience:', 
      value: 'No data available'
    },
    { 
      label: 'Languages:', 
      value: 'No data available'
    },
  ];

  const researchFields = [
    { 
      label: 'Active Projects:', 
      value: user?.active_projects || ''
    },
    { 
      label: 'Data Management Plan:', 
      value: user?.data_management_plan || ''
    },
    { 
      label: 'PID For Projects:', 
      value: user?.pid_for_projects || ''
    },
  ];

  // Update publicationFields with ORCID data
  const publicationFields = [
    { 
      label: 'Recent Publications:', 
      value: 'No data available'
    },
    { 
      label: 'Preprints:', 
      value: 'No data available'
    },
    { 
      label: 'Other Research Outputs:', 
      value: 'No data available'
    },
  ];

  // Update fundingFields with ORCID data
  const fundingFields = [
    { 
      label: 'Funder Information:', 
      value: 'No data available'
    },
    { 
      label: 'Grants:', 
      value: 'No data available'
    },
  ];

  // Update collaborationFields with ORCID data
  const collaborationFields = [
    { 
      label: 'Co-Authors/Collaborators:', 
      value: 'No data available'
    },
    { 
      label: 'Institutional Affiliations:', 
      value: 'No data available'
    },
  ];

  // Update externalIdentifierFields with ORCID data
  const externalIdentifierFields = [
    { 
      label: 'ORCID:', 
      value: 'No data available'
    },
    { 
      label: 'Researcher ID:', 
      value: 'No data available'
    },
    { 
      label: 'Scopus Author ID:', 
      value: 'No data available'
    },
    { 
      label: 'Google Scholar Profile:', 
      value: 'No data available'
    },
  ];

  // Update licensingFields with ORCID data
  const licensingFields = [
    { 
      label: 'Preferred Licensing For Research Outputs:', 
      value: 'No data available'
    },
    { 
      label: 'Data Sharing Preferences:', 
      value: 'No data available'
    },
  ];

  // Update contactFields with ORCID data
  const contactFields = [
    { 
      label: 'Primary Contact:', 
      value: 'No data available'
    },
    { 
      label: 'Public Profile Link:', 
      value: 'No data available'
    },
  ];

  const handleAccordionChange = (panel) => (event, isExpanded) => {
    setExpanded(isExpanded ? panel : false);
  };

  const accordionSections = [
    { 
      id: 'basic', 
      title: 'Basic Information',
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
              Basic Information
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
      title: 'Professional Background',
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
              Professional Background
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
      title: 'Research Projects',
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
              Research Projects
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
      title: 'Publications and Outputs',
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
              Publications And Outputs
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
      title: 'Funding',
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
              Funding
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
      title: 'Collaboration',
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
              Collaboration
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
      title: 'External Identifiers',
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
              External Identifiers
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
      title: 'Licensing and Data Sharing Preferences',
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
              Licensing And Data Sharing Preferences
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
      title: 'Contact Information',
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
              Contact Information
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
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  const EditProfileModal = () => (
    <Modal
      open={openEditModal}
      onClose={handleEditModalClose}
      aria-labelledby="edit-profile-modal"
      aria-describedby="edit-profile-form"
    >
      <Box sx={{
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
      }}>
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          gap: 3
        }}>
          <Typography variant="h6" component="h2" sx={{ color: 'text.primary', mb: 2 }}>
            Edit Profile
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
                <Typography color="text.secondary">No file chosen</Typography>
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
                label="Full Name"
                value={editFormData.fullName}
                onChange={handleEditFormChange}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#ffffff08' : '#00000008',
                  }
                }}
              />
              <TextField
                fullWidth
                name="format"
                label="Phone"
                placeholder="+2547..."
                value={editFormData.format}
                onChange={handleEditFormChange}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#ffffff08' : '#00000008',
                  }
                }}
              />
            </Box>
          </Box>

          <FormControl fullWidth>
            <InputLabel>Select Faculty</InputLabel>
            <Select
              name="faculty"
              value={editFormData.faculty}
              onChange={handleEditFormChange}
              label="Select Faculty"
              sx={{
                backgroundColor: theme.palette.mode === 'dark' ? '#ffffff08' : '#00000008',
              }}
            >
              {faculties.map((faculty) => (
                <MenuItem key={faculty} value={faculty}>
                  {faculty}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Select Country</InputLabel>
            <Select
              name="country"
              value={editFormData.country}
              onChange={handleEditFormChange}
              label="Select Country"
              sx={{
                backgroundColor: theme.palette.mode === 'dark' ? '#ffffff08' : '#00000008',
              }}
            >
              {allCountries.map((country) => (
                <MenuItem key={country} value={country}>
                  {country}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            fullWidth
            variant="contained"
            onClick={handleUpdateProfile}
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
            UPDATE PROFILE
          </Button>
        </Box>
      </Box>
    </Modal>
  );

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
                  label="Verified Account"
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
                Good Evening, {user?.name}
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
                ASSIGN DOCiD
              </Button>
            </Box>

            <Grid container spacing={2}>
              {[
                { title: 'Total DOCiDs', count: 0, icon: DescriptionIcon },
                { title: 'Indigenous Knowledge', count: 0, icon: FolderIcon },
                { title: 'Panfest', count: 0, icon: FolderIcon },
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
                  My Publications ({userPublications.length})
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
                        DOCID
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
                        TITLE
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
                        ACTION
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
                          No publications found
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
                              {publication.docid}
                            <IconButton 
                              size="small" 
                                onClick={() => navigator.clipboard.writeText(publication.docid)}
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
                              {publication.title}
                            </Typography>
                          </TableCell>
                        <TableCell align="right">
                          <IconButton 
                            size="small" 
                              onClick={() => router.push(`/docid/${encodeURIComponent(publication.docid)}`)}
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
                            onClick={() => {/* Handle delete */}}
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
        <EditProfileModal />
      </Container>
    </Box>
  );
};

export default MyAccountPage; 