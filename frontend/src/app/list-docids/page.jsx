"use client";

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  FormControl,
  Select,
  MenuItem,
  OutlinedInput,
  Checkbox,
  ListItemText,
  Card,
  CardContent,
  CardMedia,
  Chip,
  Avatar,
  IconButton,
  Stack,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText as MuiListItemText,
  Button,
  InputAdornment,
  TextField,
  Fade,
  useTheme,
  Skeleton,
  Pagination,
  Modal,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  ThumbUpOutlined,
  ChatBubbleOutline,
  VisibilityOutlined,
  Search as SearchIcon,
  FilterList as FilterListIcon,
  Close as CloseIcon,
  CheckCircleOutline as CheckCircleIcon
} from '@mui/icons-material';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import AddIcon from '@mui/icons-material/Add';
import { useRouter, useSearchParams } from 'next/navigation';
import docidsData from '@/data/docids.json';
import axios from 'axios';
import { useSelector } from 'react-redux';
import { getDocIdUrl } from '@/utils/docidUtils';
import { useTranslation } from 'react-i18next';

const ListDocIds = () => {
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isRehydrated, setIsRehydrated] = useState(false);
  const [publications, setPublications] = useState([]);
  const [resourceTypesList, setResourceTypesList] = useState([]);
  const [resourceTypeCounts, setResourceTypeCounts] = useState({});
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 15,
    total: 0,
    total_pages: 0
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const router = useRouter();
  const theme = useTheme();
  const { t } = useTranslation();
  const { user, isAuthenticated } = useSelector((state) => state.auth);
  const searchParams = useSearchParams();
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  const searchTimeout = useRef(null);
  const [allPublications, setAllPublications] = useState([]);

  // Wait for Redux Persist to rehydrate before checking authentication
  useEffect(() => {
    const checkRehydration = () => {
      // Check if persist has completed by checking if auth state exists
      const persistedAuth = localStorage.getItem('persist:root');
      if (persistedAuth) {
        setIsRehydrated(true);
      } else {
        // If no persisted data, mark as rehydrated (user is not logged in)
        setTimeout(() => setIsRehydrated(true), 100);
      }
    };
    checkRehydration();
  }, []);

  useEffect(() => {
    // Only check authentication after rehydration is complete
    if (isRehydrated && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isRehydrated, router]);

  useEffect(() => {
    // Check if we have a success parameter in the URL and if we came from assign-docid page
    const success = searchParams.get('success');
    const isFromAssignDocId = sessionStorage.getItem('fromAssignDocId') === 'true';
    
    if (success === 'true' && isFromAssignDocId) {
      setShowSuccessModal(true);
      // Clear the success parameter from URL without refreshing the page
      const newUrl = window.location.pathname;
      window.history.replaceState({}, '', newUrl);
      // Clear the session storage flag
      sessionStorage.removeItem('fromAssignDocId');
    }
  }, [searchParams]);

  // Fetch resource types
  useEffect(() => {
    const fetchResourceTypes = async () => {
      try {
        const response = await axios.get('/api/publications/get-list-resource-types');
        setResourceTypesList(response.data);
        console.log(response.data);
      } catch (error) {
        console.error('Error fetching resource types:', error);
      }
    };
    fetchResourceTypes();
  }, []);

  // Create stable memoized values to prevent dependency array issues
  const stableResourceTypesList = useMemo(() => resourceTypesList, [resourceTypesList.length]);
  const resourceTypesLoaded = resourceTypesList.length > 0;

  // Get resource type name by id - using a simple function without useCallback to avoid dependency issues
  const getResourceTypeName = (id) => {
    const resourceType = stableResourceTypesList.find(type => type.id === id);
    return resourceType ? resourceType.resource_type : '';
  };

  const fetchPublications = useCallback(async (page = 1) => {
    try {
      setIsLoading(true);
      const params = new URLSearchParams();
      params.append('page', page);
      params.append('page_size', pagination.page_size);

      // Only add resource_type if types are selected
      if (selectedTypes.length > 0 && resourceTypesLoaded) {
        // Get the IDs of the selected resource types
        const selectedTypeIds = stableResourceTypesList
          .filter(type => selectedTypes.includes(type.resource_type))
          .map(type => type.id);

        // Add each resource type ID as a separate parameter
        selectedTypeIds.forEach(id => {
          params.append('resource_type_id', id);
        });
      }

      const response = await axios.get(
        `/api/publications/get-publications?${params.toString()}`
      );

      const data = response.data.data;
      setAllPublications(data);
      setPublications(data);
      setPagination(response.data.pagination);
    } catch (error) {
      console.error('Error fetching publications:', error);
      setPublications([]);
      setAllPublications([]);
      setPagination({
        page: 1,
        page_size: 10,
        total: 0,
        total_pages: 0
      });
    } finally {
      setIsLoading(false);
    }
  }, [selectedTypes, pagination.page_size, resourceTypesLoaded, stableResourceTypesList]); // Use memoized version

  // Effect for initial load and when dependencies change
  useEffect(() => {
    if (resourceTypesLoaded) {
      fetchPublications(1);
    }
  }, [fetchPublications, resourceTypesLoaded]);

  // Calculate resource type counts
  useEffect(() => {
    if (allPublications.length > 0 && resourceTypesLoaded) {
      const counts = allPublications.reduce((acc, pub) => {
        const resourceType = stableResourceTypesList.find(type => type.id === pub.resource_type_id);
        const resourceTypeName = resourceType ? resourceType.resource_type : '';
        acc[resourceTypeName] = (acc[resourceTypeName] || 0) + 1;
        return acc;
      }, {});
      setResourceTypeCounts(counts);
    }
  }, [allPublications, resourceTypesLoaded, stableResourceTypesList]); // Include stable version

  // Separate effect for search filtering
  useEffect(() => {
    if (!isLoading && allPublications.length > 0) {
      const filteredData = searchQuery.trim()
        ? allPublications.filter(pub =>
          pub.title.toLowerCase().includes(searchQuery.toLowerCase().trim())
        )
        : allPublications;

      setPublications(filteredData);
    }
  }, [searchQuery, allPublications, isLoading]);

  // Update search handler
  const handleSearchChange = (event) => {
    const value = event.target.value;
    setSearchQuery(value);
  };

  // Update type change handler to immediately trigger search
  const handleTypeChange = (event) => {
    const {
      target: { value },
    } = event;
    const types = typeof value === 'string' ? value.split(',') : value;
    setSelectedTypes(types);
    // Reset to page 1 when changing filters
    setPagination(prev => ({
      ...prev,
      page: 1
    }));
  };

  // Update clear search handler
  const handleClearSearch = () => {
    setSearchQuery('');
    setPublications(allPublications);
    setPagination(prev => ({
      ...prev,
      page: 1,
      total: allPublications.length,
      total_pages: Math.ceil(allPublications.length / prev.page_size)
    }));
  };

  // Update clear filter handler
  const handleClearFilter = (valueToRemove) => {
    setSelectedTypes(prev => prev.filter(type => type !== valueToRemove));
    // Reset to page 1 when clearing a filter
    setPagination(prev => ({
      ...prev,
      page: 1
    }));
  };

  const handleLikeClick = (event) => {
    event.stopPropagation(); // Prevent card click event
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handleCloseSuccessModal = () => {
    setShowSuccessModal(false);
  };

  const renderSkeleton = () => (
    <Grid container spacing={3}>
      {[1, 2, 3, 4, 5, 6].map((item) => (
        <Grid item xs={12} sm={6} md={4} key={item}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ pb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Skeleton variant="circular" width={40} height={40} />
                <Box sx={{ ml: 2 }}>
                  <Skeleton width={120} />
                  <Skeleton width={80} />
                </Box>
              </Box>
            </CardContent>
            <Skeleton variant="rectangular" height={200} />
            <CardContent>
              <Skeleton width={80} height={24} sx={{ mb: 1 }} />
              <Skeleton variant="text" sx={{ mb: 1 }} />
              <Skeleton variant="text" sx={{ mb: 1 }} />
              <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #eee' }}>
                <Stack direction="row" spacing={3}>
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} width={40} />
                  ))}
                </Stack>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  const createMarkup = (html) => {
    return { __html: html };
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    const day = days[date.getUTCDay()];
    const month = months[date.getUTCMonth()];
    const dateNum = date.getUTCDate();
    const year = date.getUTCFullYear();

    return `${day}, ${month} ${dateNum}, ${year}`;
  };

  const handleAddDocument = async (document) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/docids`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.accessToken}`
        },
        body: JSON.stringify({
          ...document,
          user_id: user.id,
          owner: user.name
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to add document');
      }

      // ... rest of your success handling code ...
    } catch (error) {
      console.error('Error adding document:', error);
      setSnackbar({
        open: true,
        message: error.message || 'Failed to add document',
        severity: 'error'
      });
    }
  };

  // Show loading while waiting for rehydration
  if (!isRehydrated) {
    return null;
  }

  // If not authenticated after rehydration, don't render the page content
  if (!isAuthenticated) {
    return null;
  }

  return (
    <Box
      component="main"
      sx={{
        backgroundColor: theme => theme.palette.background.content,
        minHeight: '100vh',
        paddingTop: { xs: 2, md: 3 },
        paddingBottom: 6
      }}
    >
      <Container
        maxWidth={false}
        sx={{
          maxWidth: '1600px',
          paddingX: { xs: 2, sm: 3, md: 4 }
        }}
      >
        <Box>
          {/* Header Section */}
          <Box
            sx={{
              marginBottom: { xs: 3, md: 5 },
              backgroundColor: 'background.paper',
              borderRadius: 3,
              padding: { xs: 2, md: 4 },
              boxShadow: '0 2px 12px rgba(0, 0, 0, 0.03)'
            }}
          >
            <Box sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: { xs: 'flex-start', md: 'center' },
              flexDirection: { xs: 'column', md: 'row' },
              gap: { xs: 3, md: 0 },
              mb: { xs: 3, md: 4 }
            }}>
              <Box sx={{ maxWidth: 'md' }}>
                <Typography
                  variant="h4"
                  component="h1"
                  sx={{
                    color: theme.palette.primary.dark,
                    fontWeight: 800,
                    mb: 2,
                    fontSize: { xs: '1.75rem', md: '2.25rem' },
                    position: 'relative',
                    '&:after': {
                      content: '""',
                      position: 'absolute',
                      bottom: -8,
                      left: 0,
                      width: 80,
                      height: 4,
                      borderRadius: 2,
                      background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.primary.light})`
                    }
                  }}
                >
                  {t('docid.title')}
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    color: theme.palette.text.secondary,
                    maxWidth: 600,
                    lineHeight: 1.6
                  }}
                >
                {t('docid.description')}
                </Typography>
              </Box>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <Button
                  variant="outlined"
                  startIcon={<FolderOpenIcon />}
                  onClick={() => router.push('/my-drafts')}
                  sx={{
                    borderColor: theme.palette.mode === 'dark' ? '#141a3b' : '#1565c0',
                    color: theme.palette.mode === 'dark' ? '#141a3b' : '#1565c0',
                    px: { xs: 3, md: 4 },
                    py: 1.75,
                    fontSize: '1rem',
                    fontWeight: 600,
                    borderRadius: 2,
                    whiteSpace: 'nowrap',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      borderColor: theme.palette.mode === 'dark' ? '#1e2756' : '#1976d2',
                      bgcolor: theme.palette.mode === 'dark' ? 'rgba(20, 26, 59, 0.08)' : 'rgba(21, 101, 192, 0.08)',
                      transform: 'translateY(-2px)',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                    }
                  }}
                >
                  My Drafts
                </Button>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => router.push('/assign-docid')}
                  sx={{
                    bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : '#1565c0',
                    color: 'white',
                    px: { xs: 3, md: 4 },
                    py: 1.75,
                    fontSize: '1rem',
                    fontWeight: 600,
                    borderRadius: 2,
                    whiteSpace: 'nowrap',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      bgcolor: theme.palette.mode === 'dark' ? '#1e2756' : '#1976d2',
                      transform: 'translateY(-2px)',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                    }
                  }}
                >
                  {t('docid.button')}
                </Button>
              </Stack>
            </Box>

            {/* Search and Filter Section */}
            <Grid container spacing={2}>
              <Grid item xs={12} md={8}>
                <TextField
                  fullWidth
                  placeholder={t('docid.search_placeholder')}
                  value={searchQuery}
                  onChange={handleSearchChange}
                  disabled={isLoading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon color="action" />
                      </InputAdornment>
                    ),
                    endAdornment: searchQuery && (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={handleClearSearch}
                          edge="end"
                          size="small"
                        >
                          <CloseIcon />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                      bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f8f9fa',
                      '&.Mui-disabled': {
                        bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.04)'
                      },
                      '&:hover': {
                        '& > fieldset': {
                          borderColor: theme.palette.mode === 'dark' ? '#141a3b' : '#1565c0',
                        }
                      },
                      '& .MuiInputBase-input': {
                        color: theme.palette.mode === 'dark' ? 'white' : 'inherit'
                      }
                    }
                  }}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth error={resourceTypesList.length === 0}>
                  <Select
                    multiple
                    value={selectedTypes}
                    onChange={handleTypeChange}
                    input={<OutlinedInput />}
                    displayEmpty
                    disabled={isLoading || resourceTypesList.length === 0}
                    renderValue={(selected) => {
                      if (selected.length === 0) {
                        return (
                          <Box sx={{
                            display: 'flex',
                            alignItems: 'center',
                            color: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.7)' : 'text.secondary',
                            gap: 1
                          }}>
                            <FilterListIcon />
                            {resourceTypesList.length === 0 ? t('docid.loading_types') : t('docid.filter_by_res_types')}
                          </Box>
                        );
                      }
                      return (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {selected.map((value) => (
                            <Chip
                              key={value}
                              label={value}
                              size="small"
                              onDelete={(e) => {
                                e.stopPropagation();
                                handleClearFilter(value);
                              }}
                              sx={{
                                bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : '#1565c0',
                                color: 'white',
                                fontWeight: 500,
                                '& .MuiChip-deleteIcon': {
                                  color: 'white',
                                  '&:hover': {
                                    color: 'rgba(255, 255, 255, 0.7)'
                                  }
                                }
                              }}
                            />
                          ))}
                        </Box>
                      );
                    }}
                    sx={{
                      minHeight: '56px',
                      borderRadius: 2,
                      bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f8f9fa',
                      '&.Mui-disabled': {
                        bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.04)'
                      },
                      '&:hover': {
                        '& .MuiOutlinedInput-notchedOutline': {
                          borderColor: theme.palette.mode === 'dark' ? '#141a3b' : '#1565c0',
                        }
                      },
                      '& .MuiSelect-select': {
                        color: theme.palette.mode === 'dark' ? 'white' : 'inherit'
                      }
                    }}
                  >
                    {resourceTypesList.map((type) => (
                      <MenuItem key={type.id} value={type.resource_type}>
                        <Checkbox
                          checked={selectedTypes.indexOf(type.resource_type) > -1}
                          sx={{
                            color: theme.palette.primary.main,
                            '&.Mui-checked': {
                              color: theme.palette.primary.main,
                            },
                          }}
                        />
                        <ListItemText
                          primary={`${type.resource_type} (${resourceTypeCounts[type.resource_type] || 0})`}
                          sx={{
                            '& .MuiTypography-root': {
                              textTransform: 'capitalize'
                            }
                          }}
                        />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Box>

          {/* Main Content Area */}
          <Box
            sx={{
              display: 'flex',
              gap: 4,
              position: 'relative'
            }}
          >
            {/* DOCiDs Container */}
            <Box sx={{ flex: 1 }}>
              {isLoading ? renderSkeleton() : (
                <>
                  <Grid
                    container
                    spacing={3}
                    sx={{
                      '& .MuiGrid-item': {
                        display: 'flex'
                      }
                    }}
                  >
                    {publications.map((doc) => (
                      <Grid item xs={12} sm={6} lg={4} key={doc.id}>
                        <Card
                          sx={{
                            width: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            cursor: 'pointer',
                            position: 'relative',
                            transition: 'all 0.3s ease',
                              bgcolor: 'background.paper',
                            '&:hover': {
                              transform: 'translateY(-8px)',
                              boxShadow: '0 12px 24px rgba(0, 0, 0, 0.1)',
                              '& .card-media': {
                                transform: 'scale(1.05)'
                              }
                            }
                          }}
                          onClick={() => {
                            router.push(getDocIdUrl(doc.docid));
                          }}
                        >
                          {/* Creator Info Section */}
                          <CardContent sx={{ pb: 1 }}>
                            <Box sx={{
                              display: 'flex',
                              alignItems: 'center',
                              mb: 2,
                              gap: 2
                            }}>
                              <Avatar
                                src={doc.avatar || '/assets/images/Logo2.png'}
                                alt={doc.owner || 'System'}
                                sx={{
                                  width: 44,
                                  height: 44,
                                  bgcolor: theme.palette.primary.main,
                                  border: `2px solid ${theme.palette.primary.light}`,
                                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                                }}
                              >
                                {!doc.avatar && doc.owner && doc.owner[0] ? doc.owner[0].toUpperCase() : 'S'}
                              </Avatar>
                              <Box>
                                <Typography
                                  variant="subtitle1"
                                  sx={{
                                    fontWeight: 600,
                                    color: theme.palette.text.primary
                                  }}
                                >
                                  {doc.owner || 'System'}
                                </Typography>
                                <Typography
                                  variant="caption"
                                  sx={{
                                    color: theme.palette.text.secondary,
                                    display: 'block'
                                  }}
                                >
                                  {formatDate(doc.published_isoformat)}
                                </Typography>
                              </Box>
                            </Box>
                          </CardContent>

                          {/* Image Section */}
                          <Box sx={{
                            position: 'relative',
                            overflow: 'hidden',
                            bgcolor: `${theme.palette.primary.main}08`,
                            height: 240,
                            width: '100%'
                          }}>
                            <CardMedia
                              component="img"
                              image={doc.publication_poster_url ?
                                `${doc.publication_poster_url}` :
                                `/assets/images/Logo2.png`}
                              alt={doc.title || 'DOCiD Logo'}
                              className="card-media"
                              sx={{
                                width: '100%',
                                height: '100%',
                                objectFit: doc.publication_poster_url ? 'cover' : 'contain',
                                transition: 'transform 0.3s ease',
                                p: doc.publication_poster_url ? 0 : 2
                              }}
                            />
                          </Box>

                          {/* Feedback Icons Section */}
                          <Box sx={{
                            px: 3,
                            py: 2,
                            display: 'flex',
                            justifyContent: 'space-between',
                            borderBottom: `1px solid ${theme.palette.divider}`
                          }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <IconButton
                                size="medium"
                                onClick={handleLikeClick}
                                sx={{
                                  color: theme.palette.primary.main,
                                  '&:hover': {
                                    color: theme.palette.primary.dark,
                                    transform: 'scale(1.1)'
                                  }
                                }}
                              >
                                <ThumbUpOutlined sx={{ fontSize: '1.5rem' }} />
                              </IconButton>
                              <Typography variant="body2" color={theme.palette.primary.main}>0</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <IconButton
                                size="medium"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setIsModalOpen(true);
                                }}
                                sx={{
                                  color: theme.palette.primary.main,
                                  '&:hover': {
                                    color: theme.palette.primary.dark,
                                    transform: 'scale(1.1)'
                                  }
                                }}
                              >
                                <ChatBubbleOutline sx={{ fontSize: '1.5rem' }} />
                              </IconButton>
                              <Typography variant="body2" color={theme.palette.primary.main}>0</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <IconButton
                                size="medium"
                                sx={{
                                  color: theme.palette.primary.main,
                                  '&:hover': {
                                    color: theme.palette.primary.dark,
                                    transform: 'scale(1.1)'
                                  }
                                }}
                              >
                                <VisibilityOutlined sx={{ fontSize: '1.5rem' }} />
                              </IconButton>
                              <Typography variant="body2" color={theme.palette.primary.main}>0</Typography>
                            </Box>
                          </Box>

                          {/* Content Section */}
                          <CardContent sx={{ flexGrow: 1, pt: 2 }}>
                            <Box sx={{
                              mb: 2,
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'center',
                              gap: 1
                            }}>
                              <Chip
                                label={`#${getResourceTypeName(doc.resource_type_id)}`}
                                size="medium"
                                sx={{
                                  bgcolor: `${theme.palette.primary.main}12`,
                                  color: theme.palette.primary.main,
                                  fontSize: '0.975rem',
                                  fontWeight: 600,
                                  textTransform: 'capitalize',
                                  '& .MuiChip-label': {
                                    px: 2
                                  }
                                }}
                              />
                            </Box>

                            <Typography
                              variant="h6"
                              component="h2"
                              sx={{
                                fontSize: '1.2rem',
                                fontWeight: 600,
                                lineHeight: 1.4,
                                color: theme.palette.text.primary,
                                mb: '5px',
                                display: '-webkit-box',
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden',
                                minHeight: '3rem',
                                textAlign: 'center',
                                textTransform: 'capitalize'
                              }}
                            >
                              {doc.title}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>

                  {/* Pagination Controls */}
                  {pagination.total_pages > 1 && (
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'center',
                        mt: 4,
                        mb: 2
                      }}
                    >
                      <Pagination
                        count={pagination.total_pages}
                        page={pagination.page}
                        onChange={(event, newPage) => fetchPublications(newPage)}
                        color="primary"
                        size="large"
                        sx={{
                          '& .MuiPaginationItem-root': {
                            fontSize: '1rem',
                            '&.Mui-selected': {
                              bgcolor: theme.palette.primary.main,
                              color: 'white',
                              '&:hover': {
                                bgcolor: theme.palette.primary.dark,
                              }
                            }
                          }
                        }}
                      />
                    </Box>
                  )}
                </>
              )}
            </Box>

            {/* Sidebar */}
            <Box
              sx={{
                width: 380,
                flexShrink: 0,
                display: { xs: 'none', lg: 'block' }
              }}
            >
              <Card
                sx={{
                  position: 'sticky',
                  top: 24,
                  bgcolor: 'background.paper',
                  borderRadius: 3,
                  overflow: 'hidden',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)'
                }}
              >
                <Box sx={{
                  background: theme.palette.mode === 'dark' ? '#141a3b' : '#1565c0',
                  p: 3,
                  color: 'white'
                }}>
                  <Typography
                    variant="h6"
                    sx={{
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.5
                    }}
                  >
                    <VisibilityOutlined />
                    {t('docid.top_publications')}
                  </Typography>
                </Box>
                <List sx={{ py: 2 }}>
                  {publications
                    .slice(0, 5)
                    .map((doc, index) => (
                      <ListItem
                        key={doc.id}
                        sx={{
                          px: 3,
                          py: 2,
                          cursor: 'pointer',
                          transition: 'all 0.2s ease',
                          '&:hover': {
                            bgcolor: 'rgba(0,0,0,0.02)',
                            transform: 'translateX(4px)'
                          }
                        }}
                        onClick={() => {
                          router.push(getDocIdUrl(doc.docid));
                        }}
                      >
                        <ListItemAvatar>
                          <Avatar
                            src={doc.avatar || '/assets/images/Logo2.png'}
                            alt={doc.owner || 'System'}
                            sx={{
                              width: 48,
                              height: 48,
                              bgcolor: theme.palette.primary.main,
                              border: `2px solid ${theme.palette.primary.light}`
                            }}
                          >
                            {!doc.avatar && doc.owner && doc.owner[0] ? doc.owner[0].toUpperCase() : 'S'}
                          </Avatar>
                        </ListItemAvatar>
                        <Box sx={{ flex: 1 }}>
                          <Typography
                            variant="subtitle2"
                            sx={{
                              fontWeight: 600,
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical',
                              overflow: 'hidden',
                              color: theme.palette.text.primary,
                              mb: 1,
                              textTransform: 'capitalize'
                            }}
                          >
                            {doc.title}
                          </Typography>
                          <Stack direction="column" spacing={1}>
                            <Typography
                              variant="caption"
                              sx={{
                                color: theme.palette.text.secondary,
                                fontSize: '0.75rem'
                              }}
                            >
                              {formatDate(doc.published_isoformat)}
                            </Typography>
                            <Chip
                              label={`#${getResourceTypeName(doc.resource_type_id)}`}
                              size="small"
                              sx={{
                                maxWidth: 'fit-content',
                                bgcolor: `${theme.palette.primary.main}12`,
                                color: theme.palette.primary.main,
                                fontSize: '0.75rem',
                                fontWeight: 500,
                                height: '24px',
                                textTransform: 'capitalize',
                                '& .MuiChip-label': {
                                  px: 2
                                }
                              }}
                            />
                          </Stack>
                        </Box>
                      </ListItem>
                    ))}
                </List>
              </Card>
            </Box>
          </Box>
        </Box>
      </Container>

      {/* Feature Not Available Modal */}
      <Dialog
        open={isModalOpen}
        onClose={handleCloseModal}
        aria-labelledby="feature-dialog-title"
      >
        <DialogTitle id="feature-dialog-title" sx={{
          pb: 2,
          color: theme.palette.primary.main,
          fontWeight: 600
        }}>
          Feature Coming Soon
        </DialogTitle>
        <DialogContent sx={{ pb: 2 }}>
          <Typography>
            This feature is not yet available but is in progress for the next version release.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={handleCloseModal}
            variant="contained"
            sx={{
              bgcolor: theme.palette.primary.main,
              color: 'white',
              '&:hover': {
                bgcolor: theme.palette.primary.dark,
              }
            }}
          >
            OK
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Modal */}
      <Dialog
        open={showSuccessModal}
        onClose={handleCloseSuccessModal}
        aria-labelledby="success-dialog-title"
        PaperProps={{
          sx: {
            borderRadius: 2,
            minWidth: '400px'
          }
        }}
      >
        <DialogContent sx={{ textAlign: 'center', py: 4 }}>
          <CheckCircleIcon 
            sx={{ 
              color: '#4caf50', 
              fontSize: 64,
              mb: 2
            }} 
          />
          <Typography variant="h5" component="div" sx={{ mb: 1, fontWeight: 600 }}>
            Success
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Publication added Successfully
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3, justifyContent: 'center' }}>
          <Button
            onClick={handleCloseSuccessModal}
            variant="contained"
            sx={{
              bgcolor: '#4caf50',
              '&:hover': {
                bgcolor: '#388e3c'
              }
            }}
          >
            OK
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ListDocIds;