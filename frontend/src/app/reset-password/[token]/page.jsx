"use client";

import React, { useState } from 'react';
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
  Paper
} from '@mui/material';
import {
  Lock as LockIcon,
  CancelOutlined,
  CheckCircleOutline
} from '@mui/icons-material';
import { useRouter, useParams } from 'next/navigation';

const ResetPasswordPage = () => {
  const router = useRouter();
  const { token } = useParams();
  const theme = useTheme();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [mounted, setMounted] = useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const validateForm = () => {
    if (!formData.password) {
      setError('Password is required');
      return false;
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
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
      console.log('Starting password reset...');
      console.log('Token:', token);
      console.log('Form data:', formData);

      const response = await fetch(`/api/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          token,
          password: formData.password
        }),
      });

      console.log('Response status:', response.status);
      const data = await response.json();
      console.log("Full response:", data);

      if (!response.ok || data.status === false) {
        console.error('Password reset failed:', data.message || 'Unknown error');
        setError(data.message || 'Password reset failed. Please try again.');
        setShowErrorModal(true);
        return;
      }

      console.log('Password reset successful');
      setShowSuccessModal(true);
      setTimeout(() => {
        router.push('/login');
      }, 3000);
    } catch (error) {
      console.error('Password reset error:', error);
      setError('Password reset failed. Please try again.');
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
                bgcolor: 'white',
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
                Reset Password
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
                  id="password"
                  label="New Password"
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

                <TextField
                  margin="normal"
                  required
                  fullWidth
                  id="confirmPassword"
                  label="Confirm New Password"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  error={!!error && error.includes('Passwords do not match')}
                  helperText={error && error.includes('Passwords do not match') ? error : ''}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LockIcon color={error && error.includes('Passwords do not match') ? "error" : "primary"} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{ mb: 3 }}
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
                    backgroundColor: theme.palette.primary.main,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      backgroundColor: theme.palette.primary.dark,
                      transform: 'translateY(-2px)',
                      boxShadow: '0 6px 20px rgba(25, 118, 210, 0.3)'
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
                      Resetting password...
                    </Box>
                  ) : (
                    'Reset Password'
                  )}
                </Button>
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
            Password Reset Error
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: 'text.secondary',
              mb: 3
            }}
          >
            {error || 'An error occurred while resetting your password'}
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
            Password Reset Successful!
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: 'text.secondary',
              mb: 3
            }}
          >
            Your password has been reset successfully. Redirecting to login...
          </Typography>
        </Paper>
      </Modal>
    </>
  );
};

export default ResetPasswordPage; 