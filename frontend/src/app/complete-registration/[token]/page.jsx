"use client";

import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  InputAdornment,
  Slide,
  useTheme,
  CircularProgress,
  Modal,
  Paper,
  FormControl,
  Select,
  MenuItem,
  InputLabel
} from '@mui/material';
import {
  Person as PersonIcon,
  Email as EmailIcon,
  Lock as LockIcon,
  Business as BusinessIcon,
  CancelOutlined,
  CheckCircleOutline,
  AccountCircle as AccountCircleIcon
} from '@mui/icons-material';
import { useRouter, useParams } from 'next/navigation';

const CompleteRegistrationPage = () => {
  const router = useRouter();
  const { token } = useParams();
  const theme = useTheme();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    fullName: '',
    username: '',
    email: '',
    affiliation: '',
    password: '',
    accountTypeId: '',
  });
  const [error, setError] = useState('');
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [accountTypesList, setAccountTypesList] = useState([]);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const fetchAccountTypes = async () => {
      try {
        const response = await fetch('/api/auth/get-list-account-types');
        if (response.ok) {
          const data = await response.json();
          setAccountTypesList(data);
        }
      } catch (error) {
        console.error('Error fetching account types:', error);
      }
    };
    fetchAccountTypes();
  }, []);

  const validateForm = () => {
    if (!formData.fullName) {
      setError('Full name is required');
      return false;
    }
    if (!formData.username) {
      setError('Username is required');
      return false;
    }
    if (!formData.email) {
      setError('Email is required');
      return false;
    }
    if (!/\S+@\S+\.\S+/.test(formData.email)) {
      setError('Please enter a valid email address');
      return false;
    }
    if (!formData.accountTypeId) {
      setError('Account type is required');
      return false;
    }
    if (!formData.password) {
      setError('Password is required');
      return false;
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }

    return true;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (error) {
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) {
      setShowErrorModal(true);
      return;
    }
    setIsLoading(true);
    setError('');

    try {
      console.log('Starting registration completion...');
      console.log('Token:', token);
      console.log('Form data:', formData);

      const response = await fetch(`/api/auth/complete-registration`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          username: formData.username,
          token,
          name: formData.fullName,
          picture: "https://www.shutterstock.com/image-illustration/default-avatar-profile-icon-social-260nw-2221359783.jpg",
          affiliation: formData.affiliation,
          email: formData.email,
          password: formData.password,
          account_type_id: formData.accountTypeId
        }),
      });

      //console.log('Response status:', response.status);
      const data = await response.json();
      //console.log("Full response:", data);

      if (!response.ok || data.status === false) {
       // console.error('Registration completion failed:', data.message || 'Unknown error');
        setError(data.message || 'Registration failed. Please try again.');
        setShowErrorModal(true);
        return;
      }

      //console.log('Registration completed successfully');
      setShowSuccessModal(true);
      setTimeout(() => {
        router.push('/login');
      }, 3000);
    } catch (error) {
      //console.error('Registration error:', error);
      setError('Registration failed. Please try again.');
      setShowErrorModal(true);
    } finally {
      setIsLoading(false);
    }
  };

  if (!mounted) {
    return null;
  }

  return (
    <>
      <Box 
        sx={{ 
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          py: { xs: 4, sm: 6, md: 8 },
          px: { xs: 2, sm: 4 },
          bgcolor: theme.palette.background.content
        }}
      >
        <Container maxWidth="sm">
          <Slide direction="up" in={true} timeout={500}>
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                p: { xs: 2.5, sm: 3, md: 4 },
                bgcolor: 'background.paper',
                borderRadius: 3,
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  boxShadow: '0 12px 48px rgba(0, 0, 0, 0.12)'
                }
              }}
            >
              <Typography
                component="h1"
                variant="h4"
                sx={{
                  fontWeight: 700,
                  color: theme.palette.text.primary,
                  mb: 3,
                  fontSize: { xs: '1.75rem', sm: '2rem' }
                }}
              >
                Complete Registration
              </Typography>

              <Box 
                component="form" 
                onSubmit={handleSubmit}
                sx={{ 
                  width: '100%',
                  mt: 0.5
                }}
              >
                <TextField
                  margin="normal"
                  required
                  fullWidth
                  id="fullName"
                  label="Full Name"
                  name="fullName"
                  autoComplete="name"
                  value={formData.fullName}
                  onChange={handleChange}
                  error={!!error && error.includes('Full name')}
                  helperText={error && error.includes('Full name') ? error : ''}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PersonIcon color={error && error.includes('Full name') ? "error" : "primary"} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{ mb: 2 }}
                />

                <TextField
                  margin="normal"
                  required
                  fullWidth
                  id="username"
                  label="Username"
                  name="username"
                  autoComplete="username"
                  value={formData.username}
                  onChange={handleChange}
                  error={!!error && error.includes('Username')}
                  helperText={error && error.includes('Username') ? error : ''}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PersonIcon color={error && error.includes('Username') ? "error" : "primary"} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{ mb: 2 }}
                />

                <TextField
                  margin="normal"
                  required
                  fullWidth
                  id="email"
                  label="Email Address"
                  name="email"
                  autoComplete="email"
                  value={formData.email}
                  onChange={handleChange}
                  error={!!error && error.includes('Email')}
                  helperText={error && error.includes('Email') ? error : ''}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <EmailIcon color={error && error.includes('Email') ? "error" : "primary"} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{ mb: 2 }}
                />

                <TextField
                  margin="normal"
                  fullWidth
                  id="affiliation"
                  label="Affiliation (Optional)"
                  name="affiliation"
                  value={formData.affiliation}
                  onChange={handleChange}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <BusinessIcon color="primary" />
                      </InputAdornment>
                    ),
                  }}
                  sx={{ mb: 2 }}
                />

                <FormControl
                  fullWidth
                  required
                  error={!!error && error.includes('Account type')}
                  sx={{ mb: 2, mt: 1 }}
                >
                  <InputLabel id="accountType-label">Account Type</InputLabel>
                  <Select
                    labelId="accountType-label"
                    id="accountTypeId"
                    name="accountTypeId"
                    value={formData.accountTypeId}
                    label="Account Type"
                    onChange={handleChange}
                    startAdornment={
                      <InputAdornment position="start">
                        <AccountCircleIcon color={error && error.includes('Account type') ? "error" : "primary"} />
                      </InputAdornment>
                    }
                  >
                    {accountTypesList.map((accountType) => (
                      <MenuItem key={accountType.id} value={accountType.id}>
                        {accountType.account_type_name}
                      </MenuItem>
                    ))}
                  </Select>
                  {error && error.includes('Account type') && (
                    <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 2 }}>
                      {error}
                    </Typography>
                  )}
                </FormControl>

                <TextField
                  margin="normal"
                  required
                  fullWidth
                  id="password"
                  label="Password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  value={formData.password}
                  onChange={handleChange}
                  error={!!error && error.includes('Password')}
                  helperText={error && error.includes('Password') ? error : ''}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LockIcon color={error && error.includes('Password') ? "error" : "primary"} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{ mb: 2 }}
                />

                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  disabled={isLoading}
                  sx={{
                    py: 1.5,
                    mb: 2,
                    fontSize: '1rem',
                    fontWeight: 600,
                    borderRadius: 2,
                    bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : '#1565c0',
                    color: '#fff',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      backgroundColor: theme.palette.mode === 'dark' ? '#1e2756' : '#1976d2',
                      transform: 'translateY(-2px)',
                      boxShadow: '0 6px 20px rgba(20, 26, 59, 0.3)'
                    }
                  }}
                >
                  {isLoading ? (
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <CircularProgress 
                        size={24} 
                        sx={{ 
                          color: 'white',
                          mr: 1
                        }} 
                      />
                      Creating account...
                    </Box>
                  ) : (
                    'Sign Up'
                  )}
                </Button>

                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'center',
                    mb: 3
                  }}
                >
                  <Button
                    variant="text"
                    onClick={() => router.push('/login')}
                    sx={{ 
                      color: theme.palette.primary.main,
                      textTransform: 'none',
                      fontSize: '0.95rem',
                      fontWeight: 500,
                      '&:hover': {
                        backgroundColor: 'transparent',
                        color: theme.palette.primary.dark,
                        textDecoration: 'underline'
                      }
                    }}
                  >
                    Already have an account? Sign in
                  </Button>
                </Box>
              </Box>
            </Box>
          </Slide>
        </Container>
      </Box>

      {/* Error Modal */}
      <Modal
        open={showErrorModal}
        onClose={() => setShowErrorModal(false)}
        aria-labelledby="error-modal"
      >
        <Paper
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: { xs: '90%', sm: 400 },
            p: 4,
            outline: 'none',
            borderRadius: 2,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center'
          }}
        >
          <Box
            sx={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mb: 2
            }}
          >
            <CancelOutlined
              sx={{
                fontSize: 60,
                color: 'error.main'
              }}
            />
          </Box>
          <Typography
            variant="h6"
            component="h2"
            sx={{
              fontWeight: 600,
              mb: 1,
              color: 'error.main'
            }}
          >
            Registration Error
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: 'text.secondary',
              mb: 3
            }}
          >
            {error || 'An error occurred during registration'}
          </Typography>
          <Button
            variant="contained"
            onClick={() => setShowErrorModal(false)}
            sx={{
              minWidth: 100,
              py: 1,
              px: 3,
              borderRadius: 2,
              backgroundColor: theme.palette.primary.main,
              '&:hover': {
                backgroundColor: theme.palette.primary.dark,
              }
            }}
          >
            OK
          </Button>
        </Paper>
      </Modal>

      {/* Success Modal */}
      <Modal
        open={showSuccessModal}
        onClose={() => setShowSuccessModal(false)}
        aria-labelledby="success-modal"
      >
        <Paper
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: { xs: '90%', sm: 400 },
            p: 4,
            outline: 'none',
            borderRadius: 2,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center'
          }}
        >
          <Box
            sx={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mb: 2
            }}
          >
            <CheckCircleOutline
              sx={{
                fontSize: 60,
                color: 'success.main'
              }}
            />
          </Box>
          <Typography
            variant="h6"
            component="h2"
            sx={{
              fontWeight: 600,
              mb: 1,
              color: 'success.main'
            }}
          >
            Registration Successful!
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: 'text.secondary',
              mb: 3
            }}
          >
            Your account has been created successfully. Redirecting to login...
          </Typography>
        </Paper>
      </Modal>
    </>
  );
};

export default CompleteRegistrationPage; 