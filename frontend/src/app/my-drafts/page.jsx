"use client";

import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Chip,
  Avatar,
  Button,
  Stack,
  useTheme,
  Skeleton,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  DraftsOutlined as DraftsIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';

const MyDrafts = () => {
  const [drafts, setDrafts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRehydrated, setIsRehydrated] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [draftToDelete, setDraftToDelete] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
  const router = useRouter();
  const theme = useTheme();
  const { t } = useTranslation();
  const { user, isAuthenticated } = useSelector((state) => state.auth);

  // Wait for Redux Persist to rehydrate before checking authentication
  useEffect(() => {
    const checkRehydration = () => {
      const persistedAuth = localStorage.getItem('persist:root');
      if (persistedAuth) {
        setIsRehydrated(true);
      } else {
        setTimeout(() => setIsRehydrated(true), 100);
      }
    };
    checkRehydration();
  }, []);

  useEffect(() => {
    if (isRehydrated && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isRehydrated, router]);

  // Fetch drafts
  useEffect(() => {
    const fetchDrafts = async () => {
      if (!user?.id) return;
      
      try {
        setIsLoading(true);
        const response = await axios.get(`/api/publications/draft/by-user/${user.id}`);
        
        console.log('Drafts response:', response.data);
        
        // The backend returns a single draft object with hasDraft flag
        if (response.data.hasDraft && response.data.formData) {
          // Convert single draft to array format for rendering
          setDrafts([{
            id: user.id, // Use user ID as draft ID
            form_data: response.data.formData,
            created_at: response.data.lastSaved,
            updated_at: response.data.lastSaved,
            user_email: response.data.user_email
          }]);
        } else {
          // No draft found
          setDrafts([]);
        }
      } catch (error) {
        console.error('Error fetching drafts:', error);
        setNotification({
          open: true,
          message: t('drafts.error_load_drafts'),
          severity: 'error'
        });
        setDrafts([]);
      } finally {
        setIsLoading(false);
      }
    };

    if (isRehydrated && isAuthenticated && user?.id) {
      fetchDrafts();
    }
  }, [user?.id, isRehydrated, isAuthenticated]);

  const handleEditDraft = (draft) => {
    // Navigate to assign-docid page - the page will automatically load the draft
    router.push('/assign-docid');
  };

  const handleDeleteClick = (draft) => {
    setDraftToDelete(draft);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!draftToDelete || !user?.email) return;

    try {
      await axios.delete(`/api/publications/draft/${user.email}`);
      
      // Remove draft from local state
      setDrafts(drafts.filter(d => d.id !== draftToDelete.id));
      
      setNotification({
        open: true,
        message: t('drafts.success_delete_draft'),
        severity: 'success'
      });
    } catch (error) {
      console.error('Error deleting draft:', error);
      setNotification({
        open: true,
        message: t('drafts.error_delete_draft'),
        severity: 'error'
      });
    } finally {
      setDeleteDialogOpen(false);
      setDraftToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setDraftToDelete(null);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Recently';
    const date = new Date(dateString);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const day = days[date.getDay()];
    const month = months[date.getMonth()];
    const dateNum = date.getDate();
    const year = date.getFullYear();
    const time = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    return `${day}, ${month} ${dateNum}, ${year} at ${time}`;
  };

  const renderSkeleton = () => (
    <Grid container spacing={3}>
      {[1, 2, 3].map((item) => (
        <Grid item xs={12} sm={6} md={4} key={item}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ pb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Skeleton variant="circular" width={40} height={40} />
                <Box sx={{ ml: 2, flex: 1 }}>
                  <Skeleton width="60%" />
                  <Skeleton width="40%" />
                </Box>
              </Box>
            </CardContent>
            <Skeleton variant="rectangular" height={200} />
            <CardContent>
              <Skeleton width="80%" height={24} sx={{ mb: 1 }} />
              <Skeleton variant="text" sx={{ mb: 1 }} />
              <Skeleton variant="text" sx={{ mb: 1 }} />
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Skeleton variant="rectangular" width={100} height={36} />
                <Skeleton variant="rectangular" width={100} height={36} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

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
            gap: { xs: 3, md: 0 }
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
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
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
                <DraftsIcon sx={{ fontSize: '2rem' }} />
                {t('drafts.page_title')}
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  color: theme.palette.text.secondary,
                  maxWidth: 600,
                  lineHeight: 1.6,
                  mt: 3
                }}
              >
                {t('drafts.page_description')}
              </Typography>
            </Box>
            <Button
              variant="outlined"
              onClick={() => router.push('/list-docids')}
              sx={{
                px: { xs: 3, md: 4 },
                py: 1.75,
                fontSize: '1rem',
                fontWeight: 600,
                borderRadius: 2,
                whiteSpace: 'nowrap',
                borderColor: theme.palette.primary.main,
                color: theme.palette.primary.main,
                '&:hover': {
                  borderColor: theme.palette.primary.dark,
                  bgcolor: `${theme.palette.primary.main}08`
                }
              }}
            >
              {t('drafts.back_to_publications')}
            </Button>
          </Box>
        </Box>

        {/* Main Content */}
        <Box>
          {isLoading ? (
            renderSkeleton()
          ) : drafts.length === 0 ? (
            <Box
              sx={{
                textAlign: 'center',
                py: 8,
                px: 2,
                backgroundColor: 'background.paper',
                borderRadius: 3,
                boxShadow: '0 2px 12px rgba(0, 0, 0, 0.03)'
              }}
            >
              <DraftsIcon
                sx={{
                  fontSize: 80,
                  color: theme.palette.text.disabled,
                  mb: 2
                }}
              />
              <Typography
                variant="h5"
                sx={{
                  color: theme.palette.text.secondary,
                  mb: 2,
                  fontWeight: 600
                }}
              >
                {t('drafts.no_drafts_title')}
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  color: theme.palette.text.secondary,
                  mb: 4
                }}
              >
                {t('drafts.no_drafts_description')}
              </Typography>
              <Button
                variant="contained"
                onClick={() => router.push('/assign-docid')}
                sx={{
                  bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : '#1565c0',
                  color: 'white',
                  px: 4,
                  py: 1.5,
                  fontSize: '1rem',
                  fontWeight: 600,
                  '&:hover': {
                    bgcolor: theme.palette.mode === 'dark' ? '#1e2756' : '#1976d2'
                  }
                }}
              >
                {t('drafts.create_new_publication')}
              </Button>
            </Box>
          ) : (
            <Grid container spacing={3}>
              {drafts.map((draft) => {
                // Parse form data if it's a string
                let formData = draft.form_data;
                if (typeof formData === 'string') {
                  try {
                    formData = JSON.parse(formData);
                  } catch (e) {
                    console.error('Error parsing form data:', e);
                    formData = {};
                  }
                }

                const title = formData?.docId?.title || t('drafts.untitled_draft');
                const resourceType = formData?.docId?.resourceType || t('drafts.unknown_type');
                const description = formData?.docId?.description || t('drafts.no_description');
                const lastSaved = draft.updated_at || draft.created_at;

                return (
                  <Grid item xs={12} sm={6} md={4} key={draft.id}>
                    <Card
                      sx={{
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        position: 'relative',
                        transition: 'all 0.3s ease',
                        bgcolor: 'background.paper',
                        border: `2px solid ${theme.palette.divider}`,
                        '&:hover': {
                          transform: 'translateY(-4px)',
                          boxShadow: '0 8px 16px rgba(0, 0, 0, 0.1)',
                          borderColor: theme.palette.primary.main
                        }
                      }}
                    >
                      {/* Draft Badge */}
                      <Chip
                        icon={<ScheduleIcon />}
                        label={t('drafts.draft_badge')}
                        size="small"
                        sx={{
                          position: 'absolute',
                          top: 16,
                          right: 16,
                          bgcolor: theme.palette.warning.main,
                          color: 'white',
                          fontWeight: 600,
                          zIndex: 1
                        }}
                      />

                      {/* Creator Info Section */}
                      <CardContent sx={{ pb: 1 }}>
                        <Box sx={{
                          display: 'flex',
                          alignItems: 'center',
                          mb: 2,
                          gap: 2
                        }}>
                          <Avatar
                            src={user?.picture || '/assets/images/Logo2.png'}
                            alt={user?.name}
                            sx={{
                              width: 44,
                              height: 44,
                              bgcolor: theme.palette.primary.main,
                              border: `2px solid ${theme.palette.primary.light}`
                            }}
                          >
                            {!user?.picture && user?.name && user.name[0]?.toUpperCase()}
                          </Avatar>
                          <Box>
                            <Typography
                              variant="subtitle1"
                              sx={{
                                fontWeight: 600,
                                color: theme.palette.text.primary
                              }}
                            >
                              {user?.name || 'You'}
                            </Typography>
                            <Typography
                              variant="caption"
                              sx={{
                                color: theme.palette.text.secondary,
                                display: 'block'
                              }}
                            >
                              {formatDate(lastSaved)}
                            </Typography>
                          </Box>
                        </Box>
                      </CardContent>

                      {/* Image Section */}
                      <Box sx={{
                        position: 'relative',
                        overflow: 'hidden',
                        bgcolor: `${theme.palette.primary.main}08`,
                        height: 200,
                        width: '100%'
                      }}>
                        <CardMedia
                          component="img"
                          image="/assets/images/Logo2.png"
                          alt="Draft"
                          sx={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'contain',
                            p: 2
                          }}
                        />
                      </Box>

                      {/* Content Section */}
                      <CardContent sx={{ flexGrow: 1, pt: 2 }}>
                        <Box sx={{ mb: 2, textAlign: 'center' }}>
                          <Chip
                            label={`#${resourceType}`}
                            size="medium"
                            sx={{
                              bgcolor: `${theme.palette.primary.main}12`,
                              color: theme.palette.primary.main,
                              fontSize: '0.875rem',
                              fontWeight: 600,
                              textTransform: 'capitalize'
                            }}
                          />
                        </Box>

                        <Typography
                          variant="h6"
                          component="h2"
                          sx={{
                            fontSize: '1.1rem',
                            fontWeight: 600,
                            lineHeight: 1.4,
                            color: theme.palette.text.primary,
                            mb: 1,
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                            minHeight: '3rem',
                            textAlign: 'center',
                            textTransform: 'capitalize'
                          }}
                        >
                          {title}
                        </Typography>

                        <Typography
                          variant="body2"
                          sx={{
                            color: theme.palette.text.secondary,
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                            minHeight: '2.5rem'
                          }}
                        >
                          {description}
                        </Typography>
                      </CardContent>

                      {/* Action Buttons */}
                      <CardContent sx={{ pt: 0 }}>
                        <Stack direction="row" spacing={1}>
                          <Button
                            fullWidth
                            variant="contained"
                            startIcon={<EditIcon />}
                            onClick={() => handleEditDraft(draft)}
                            sx={{
                              bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : '#1565c0',
                              color: 'white',
                              '&:hover': {
                                bgcolor: theme.palette.mode === 'dark' ? '#1e2756' : '#1976d2'
                              }
                            }}
                          >
                            {t('drafts.continue_button')}
                          </Button>
                          <IconButton
                            color="error"
                            onClick={() => handleDeleteClick(draft)}
                            sx={{
                              border: `1px solid ${theme.palette.error.main}`,
                              borderRadius: 1,
                              '&:hover': {
                                bgcolor: `${theme.palette.error.main}08`
                              }
                            }}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          )}
        </Box>
      </Container>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-dialog-title"
      >
        <DialogTitle id="delete-dialog-title" sx={{
          color: theme.palette.error.main,
          fontWeight: 600
        }}>
          {t('drafts.delete_dialog_title')}
        </DialogTitle>
        <DialogContent>
          <Typography>
            {t('drafts.delete_dialog_message')}
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={handleDeleteCancel}
            variant="outlined"
            sx={{
              borderColor: theme.palette.text.secondary,
              color: theme.palette.text.secondary
            }}
          >
            {t('drafts.cancel_button')}
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            sx={{
              bgcolor: theme.palette.error.main,
              '&:hover': {
                bgcolor: theme.palette.error.dark
              }
            }}
          >
            {t('drafts.delete_button')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setNotification({ ...notification, open: false })}
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MyDrafts;

