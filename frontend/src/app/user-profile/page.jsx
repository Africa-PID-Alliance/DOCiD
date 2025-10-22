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
  TextField,
  CircularProgress,
  Snackbar,
  Alert,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Pagination,
  Chip,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Visibility as VisibilityIcon,
  LinkedIn as LinkedInIcon,
  Facebook as FacebookIcon,
  Twitter as TwitterIcon,
  Instagram as InstagramIcon,
  GitHub as GitHubIcon,
  Language as LanguageIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { useRouter } from 'next/navigation';
import axios from 'axios';

const UserProfilePage = () => {
  const router = useRouter();
  const theme = useTheme();
  const { user, isAuthenticated } = useSelector((state) => state.auth);

  // State management
  const [currentTab, setCurrentTab] = useState(0);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  const [isLoadingPublications, setIsLoadingPublications] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');

  // User profile data
  const [profileData, setProfileData] = useState(null);
  const [editedProfileData, setEditedProfileData] = useState({});

  // Publications data
  const [publicationsData, setPublicationsData] = useState([]);
  const [publicationsPagination, setPublicationsPagination] = useState({
    total: 0,
    page: 1,
    page_size: 10,
    total_pages: 0,
  });

  // Statistics data
  const [statisticsData, setStatisticsData] = useState(null);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  // Fetch user profile data
  const fetchUserProfile = async () => {
    if (!user?.id) return;

    try {
      setIsLoadingProfile(true);
      const response = await axios.get(`/api/user-profile/${user.id}`);
      setProfileData(response.data);
      setEditedProfileData(response.data);
    } catch (error) {
      console.error('Error fetching user profile:', error);
      showSnackbar('Failed to load user profile', 'error');
    } finally {
      setIsLoadingProfile(false);
    }
  };

  // Fetch user publications
  const fetchUserPublications = async (page = 1, pageSize = 10) => {
    if (!user?.id) return;

    try {
      setIsLoadingPublications(true);
      const response = await axios.get(
        `/api/user-profile/${user.id}/publications`,
        {
          params: {
            page,
            page_size: pageSize,
            sort: 'published',
            order: 'desc',
          },
        }
      );

      setPublicationsData(response.data.publications || []);
      setPublicationsPagination(response.data.pagination || {});
    } catch (error) {
      console.error('Error fetching user publications:', error);
      showSnackbar('Failed to load publications', 'error');
    } finally {
      setIsLoadingPublications(false);
    }
  };

  // Fetch user statistics
  const fetchUserStatistics = async () => {
    if (!user?.id) return;

    try {
      const response = await axios.get(`/api/user-profile/${user.id}/statistics`);
      setStatisticsData(response.data);
    } catch (error) {
      console.error('Error fetching user statistics:', error);
    }
  };

  // Initial data fetch
  useEffect(() => {
    if (user?.id) {
      fetchUserProfile();
      fetchUserPublications();
      fetchUserStatistics();
    }
  }, [user?.id]);

  // Handle profile field changes
  const handleProfileFieldChange = (fieldName, value) => {
    setEditedProfileData((prev) => ({
      ...prev,
      [fieldName]: value,
    }));
  };

  // Save profile changes
  const handleSaveProfile = async () => {
    if (!user?.id) return;

    try {
      setIsSavingProfile(true);

      const response = await axios.put(
        `/api/user-profile/${user.id}`,
        editedProfileData
      );

      setProfileData(response.data.user_data);
      setEditedProfileData(response.data.user_data);
      setIsEditingProfile(false);
      showSnackbar('Profile updated successfully', 'success');
    } catch (error) {
      console.error('Error updating profile:', error);
      showSnackbar(
        error.response?.data?.error || 'Failed to update profile',
        'error'
      );
    } finally {
      setIsSavingProfile(false);
    }
  };

  // Cancel profile editing
  const handleCancelEdit = () => {
    setEditedProfileData(profileData);
    setIsEditingProfile(false);
  };

  // Show snackbar notification
  const showSnackbar = (message, severity = 'success') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };

  // Handle pagination change
  const handlePublicationPageChange = (event, newPage) => {
    fetchUserPublications(newPage, publicationsPagination.page_size);
  };

  // Render loading state
  if (isLoadingProfile) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'background.default',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Profile Information Tab
  const renderProfileTab = () => (
    <Box sx={{ mt: 3 }}>
      <Grid container spacing={3}>
        {/* Basic Information */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, borderRadius: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6" fontWeight={600}>
                Basic Information
              </Typography>
              {!isEditingProfile ? (
                <IconButton
                  size="small"
                  onClick={() => setIsEditingProfile(true)}
                  color="primary"
                >
                  <EditIcon />
                </IconButton>
              ) : (
                <Box>
                  <IconButton
                    size="small"
                    onClick={handleSaveProfile}
                    color="success"
                    disabled={isSavingProfile}
                  >
                    {isSavingProfile ? <CircularProgress size={20} /> : <SaveIcon />}
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={handleCancelEdit}
                    color="error"
                    disabled={isSavingProfile}
                  >
                    <CancelIcon />
                  </IconButton>
                </Box>
              )}
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Full Name"
                  value={editedProfileData?.full_name || ''}
                  onChange={(e) => handleProfileFieldChange('full_name', e.target.value)}
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Email"
                  value={editedProfileData?.email || ''}
                  onChange={(e) => handleProfileFieldChange('email', e.target.value)}
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Affiliation"
                  value={editedProfileData?.affiliation || ''}
                  onChange={(e) => handleProfileFieldChange('affiliation', e.target.value)}
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Role"
                  value={editedProfileData?.role || ''}
                  onChange={(e) => handleProfileFieldChange('role', e.target.value)}
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="ORCID ID"
                  value={editedProfileData?.orcid_id || ''}
                  onChange={(e) => handleProfileFieldChange('orcid_id', e.target.value)}
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                />
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Location Information */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, borderRadius: 2 }}>
            <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
              Location
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Country"
                  value={editedProfileData?.country || ''}
                  onChange={(e) => handleProfileFieldChange('country', e.target.value)}
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="City"
                  value={editedProfileData?.city || ''}
                  onChange={(e) => handleProfileFieldChange('city', e.target.value)}
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Location"
                  value={editedProfileData?.location || ''}
                  onChange={(e) => handleProfileFieldChange('location', e.target.value)}
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="ROR ID"
                  value={editedProfileData?.ror_id || ''}
                  onChange={(e) => handleProfileFieldChange('ror_id', e.target.value)}
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                />
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Social Media Links */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, borderRadius: 2 }}>
            <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
              Social Media Links
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="LinkedIn Profile"
                  value={editedProfileData?.linkedin_profile_link || ''}
                  onChange={(e) =>
                    handleProfileFieldChange('linkedin_profile_link', e.target.value)
                  }
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                  InputProps={{
                    startAdornment: <LinkedInIcon sx={{ mr: 1, color: '#0077B5' }} />,
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Facebook Profile"
                  value={editedProfileData?.facebook_profile_link || ''}
                  onChange={(e) =>
                    handleProfileFieldChange('facebook_profile_link', e.target.value)
                  }
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                  InputProps={{
                    startAdornment: <FacebookIcon sx={{ mr: 1, color: '#1877F2' }} />,
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="X (Twitter) Profile"
                  value={editedProfileData?.x_profile_link || ''}
                  onChange={(e) =>
                    handleProfileFieldChange('x_profile_link', e.target.value)
                  }
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                  InputProps={{
                    startAdornment: <TwitterIcon sx={{ mr: 1, color: '#1DA1F2' }} />,
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Instagram Profile"
                  value={editedProfileData?.instagram_profile_link || ''}
                  onChange={(e) =>
                    handleProfileFieldChange('instagram_profile_link', e.target.value)
                  }
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                  InputProps={{
                    startAdornment: <InstagramIcon sx={{ mr: 1, color: '#E4405F' }} />,
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="GitHub Profile"
                  value={editedProfileData?.github_profile_link || ''}
                  onChange={(e) =>
                    handleProfileFieldChange('github_profile_link', e.target.value)
                  }
                  disabled={!isEditingProfile}
                  variant={isEditingProfile ? 'outlined' : 'filled'}
                  InputProps={{
                    startAdornment: <GitHubIcon sx={{ mr: 1, color: '#333' }} />,
                  }}
                />
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );

  // Publications Tab
  const renderPublicationsTab = () => (
    <Box sx={{ mt: 3 }}>
      <Paper sx={{ p: 3, borderRadius: 2 }}>
        <Typography variant="h6" fontWeight={600} sx={{ mb: 3 }}>
          My Publications ({publicationsPagination.total || 0})
        </Typography>

        {isLoadingPublications ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : publicationsData.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography color="text.secondary">
              No publications found. Start by assigning a DOCiD!
            </Typography>
            <Button
              variant="contained"
              sx={{ mt: 2 }}
              onClick={() => router.push('/assign-docid')}
            >
              Assign DOCiD
            </Button>
          </Box>
        ) : (
          <>
            <Grid container spacing={2}>
              {publicationsData.map((publication) => (
                <Grid item xs={12} key={publication.id}>
                  <Card
                    variant="outlined"
                    sx={{
                      '&:hover': {
                        boxShadow: 3,
                        borderColor: 'primary.main',
                      },
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="h6" gutterBottom>
                            {publication.document_title}
                          </Typography>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ mb: 1 }}
                          >
                            {publication.document_description}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            <Chip
                              label={`DOCiD: ${publication.document_docid}`}
                              size="small"
                              color="primary"
                            />
                            {publication.doi && (
                              <Chip
                                label={`DOI: ${publication.doi}`}
                                size="small"
                                variant="outlined"
                              />
                            )}
                            {publication.published && (
                              <Chip
                                label={new Date(publication.published).toLocaleDateString()}
                                size="small"
                                variant="outlined"
                              />
                            )}
                          </Box>
                        </Box>
                        <CardActions>
                          <IconButton
                            color="primary"
                            onClick={() =>
                              router.push(
                                `/docid/${encodeURIComponent(publication.document_docid)}`
                              )
                            }
                          >
                            <VisibilityIcon />
                          </IconButton>
                        </CardActions>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            {publicationsPagination.total_pages > 1 && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                <Pagination
                  count={publicationsPagination.total_pages}
                  page={publicationsPagination.page}
                  onChange={handlePublicationPageChange}
                  color="primary"
                />
              </Box>
            )}
          </>
        )}
      </Paper>
    </Box>
  );

  // Statistics Tab
  const renderStatisticsTab = () => (
    <Box sx={{ mt: 3 }}>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 3, textAlign: 'center', borderRadius: 2 }}>
            <Typography variant="h3" color="primary" fontWeight={600}>
              {statisticsData?.total_publications || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Publications
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 3, textAlign: 'center', borderRadius: 2 }}>
            <Typography variant="h3" color="primary" fontWeight={600}>
              {statisticsData?.publications_this_year || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Publications This Year
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 3, textAlign: 'center', borderRadius: 2 }}>
            <Typography variant="h3" color="primary" fontWeight={600}>
              {statisticsData?.publications_this_month || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Publications This Month
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 3, textAlign: 'center', borderRadius: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Member Since
            </Typography>
            <Typography variant="h6" color="primary" fontWeight={600}>
              {statisticsData?.member_since
                ? new Date(statisticsData.member_since).toLocaleDateString()
                : 'N/A'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );

  return (
    <Box sx={{ minHeight: '100vh', pt: 4, pb: 4, backgroundColor: 'background.default' }}>
      <Container maxWidth="lg">
        {/* Profile Header */}
        <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item>
              <Avatar
                src={profileData?.avator || user?.picture}
                alt={profileData?.full_name || user?.name}
                sx={{ width: 120, height: 120 }}
              />
            </Grid>
            <Grid item xs>
              <Typography variant="h4" fontWeight={600} gutterBottom>
                {profileData?.full_name || user?.name}
              </Typography>
              <Typography variant="body1" color="text.secondary" gutterBottom>
                {profileData?.email || user?.email}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {profileData?.affiliation || 'No affiliation'}
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Chip
                  label={profileData?.type || 'Standard User'}
                  color="primary"
                  size="small"
                />
              </Box>
            </Grid>
          </Grid>
        </Paper>

        {/* Tabs */}
        <Paper sx={{ borderRadius: 2 }}>
          <Tabs
            value={currentTab}
            onChange={(e, newValue) => setCurrentTab(newValue)}
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="Profile Information" />
            <Tab label="My Publications" />
            <Tab label="Statistics" />
          </Tabs>

          {currentTab === 0 && renderProfileTab()}
          {currentTab === 1 && renderPublicationsTab()}
          {currentTab === 2 && renderStatisticsTab()}
        </Paper>

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbarOpen}
          autoHideDuration={6000}
          onClose={() => setSnackbarOpen(false)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert
            onClose={() => setSnackbarOpen(false)}
            severity={snackbarSeverity}
            sx={{ width: '100%' }}
          >
            {snackbarMessage}
          </Alert>
        </Snackbar>
      </Container>
    </Box>
  );
};

export default UserProfilePage;
