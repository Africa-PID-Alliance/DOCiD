"use client";

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
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
  PersonAddOutlined,
  Email as EmailIcon,
  CancelOutlined,
  CheckCircleOutline
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';

const RegisterPage = () => {
  const { t } = useTranslation();
  const router = useRouter();
  const theme = useTheme();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: ''
  });
  const [error, setError] = useState('');
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [mounted, setMounted] = useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const validateForm = () => {
    if (!formData.email) {
      setError(t('auth.email_required'));
      return false;
    }
    if (!/\S+@\S+\.\S+/.test(formData.email)) {
      setError(t('auth.valid_email_required'));
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
      const response = await fetch('/api/auth/initiate-registration', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          email: formData.email
        }),
      });

      console.log('Response status:', response.status);
      const data = await response.json();
      console.log("Full registration response:", data);

      if (!response.ok || data.status === false) {
        setError(data.message || t('auth.registration_failed'));
        setShowErrorModal(true);
        return;
      }

      setShowSuccessModal(true);
      setTimeout(() => {
        router.push('/login');
      }, 3000);
    } catch (error) {
      setError(t('auth.registration_failed'));
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
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  mb: 3
                }}
              >
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    bgcolor: theme.palette.primary.main,
                    borderRadius: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mb: 1.5,
                    transform: 'rotate(10deg)',
                    transition: 'transform 0.3s ease',
                    '&:hover': {
                      transform: 'rotate(0deg)'
                    }
                  }}
                >
                  <PersonAddOutlined sx={{ color: 'white', fontSize: 24 }} />
                </Box>

                <Typography
                  component="h1"
                  variant="h4"
                  sx={{
                    fontWeight: 700,
                    color: theme.palette.text.primary,
                    mb: 0.5,
                    fontSize: { xs: '1.75rem', sm: '2rem' }
                  }}
                >
                  {t('auth.sign_up')}
                </Typography>
              </Box>

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
                  id="email"
                  label={t('auth.email_address')}
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
                  sx={{
                    mb: 3,
                    '& .MuiOutlinedInput-root': {
                      '&:hover fieldset': {
                        borderColor: theme.palette.primary.main,
                      },
                    }
                  }}
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
                      {t('auth.creating_account')}
                    </Box>
                  ) : (
                    t('auth.sign_up')
                  )}
                </Button>

                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    mt: 2
                  }}
                >
                  <Typography
                    variant="body2"
                    sx={{ color: theme.palette.text.secondary }}
                  >
                    {t('auth.already_have_account')}{' '}
                    <Button
                      onClick={() => router.push('/login')}
                      sx={{
                        color: theme.palette.primary.main,
                        textTransform: 'none',
                        fontWeight: 600,
                        p: 0,
                        minWidth: 'auto',
                        '&:hover': {
                          backgroundColor: 'transparent',
                          textDecoration: 'underline'
                        }
                      }}
                    >
                      {t('auth.sign_in_here')}
                    </Button>
                  </Typography>
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
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <Paper
          sx={{
            p: 4,
            maxWidth: 400,
            mx: 2,
            borderRadius: 2,
            textAlign: 'center'
          }}
        >
          <CancelOutlined
            sx={{
              fontSize: 48,
              color: 'error.main',
              mb: 2
            }}
          />
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            Registration Error
          </Typography>
          <Typography variant="body2" sx={{ mb: 3, color: 'text.secondary' }}>
            {error}
          </Typography>
          <Button
            variant="contained"
            onClick={() => setShowErrorModal(false)}
            sx={{
              bgcolor: theme.palette.primary.main,
              '&:hover': {
                bgcolor: theme.palette.primary.dark
              }
            }}
          >
            {t('auth.cancel')}
          </Button>
        </Paper>
      </Modal>

      {/* Success Modal */}
      <Modal
        open={showSuccessModal}
        onClose={() => setShowSuccessModal(false)}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <Paper
          sx={{
            p: 4,
            maxWidth: 400,
            mx: 2,
            borderRadius: 2,
            textAlign: 'center'
          }}
        >
          <CheckCircleOutline
            sx={{
              fontSize: 48,
              color: 'success.main',
              mb: 2
            }}
          />
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            {t('auth.registration_successful')}
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            {t('auth.check_email_complete')}
          </Typography>
        </Paper>
      </Modal>
    </>
  );
};

export default RegisterPage; 