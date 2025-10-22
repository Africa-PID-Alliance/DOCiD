"use client";

import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { loginStart, loginSuccess, loginFailure, logout } from '@/redux/slices/authSlice';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Divider,
  Stack,
  CircularProgress,
  InputAdornment,
  IconButton,
  Alert,
  Slide,
  useTheme,
  Modal,
  Paper,
  Snackbar
} from '@mui/material';
import {
  LockOutlined,
  GitHub,
  Google,
  Visibility,
  VisibilityOff,
  Email as EmailIcon,
  Lock as LockIcon,
  Close as CloseIcon,
  CheckCircleOutline
} from '@mui/icons-material';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import axios from 'axios';

const LoginPage = () => {
  const { t } = useTranslation();
  const router = useRouter();
  const theme = useTheme();
  const dispatch = useDispatch();
  const { loading, error } = useSelector((state) => state.auth);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [showError, setShowError] = useState(false);
  const [resetPasswordModal, setResetPasswordModal] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetEmailError, setResetEmailError] = useState('');
  const [isResetting, setIsResetting] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });

  const validateForm = () => {
    const newErrors = {};
    if (!formData.email) {
      newErrors.email = t('auth.email_required');
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = t('auth.valid_email_required');
    }
    if (!formData.password) {
      newErrors.password = t('auth.password_required');
    } else if (formData.password.length < 6) {
      newErrors.password = t('auth.password_min_length');
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleSignIn = async (e) => {
    e.preventDefault();
    if (!validateForm()) {
      setShowError(true);
      return;
    }
    
    dispatch(loginStart());
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        dispatch(loginFailure(data.error || 'Invalid email or password'));
        setSnackbar({
          open: true,
          message: data.error || 'Invalid email or password',
          severity: 'error'
        });
        return;
      }

      // Fetch user's social_id
      const userResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/user/email/${encodeURIComponent(formData.email)}`);
      const userDataSocial = await userResponse.json();
    

      const userData = {
        accessToken: data.token,
        refreshToken: data.refresh_token,
        user_id: data.user_id,
        full_name: data.full_name,
        avator: data.avator,
        user_name: data.user_name,
        type: data.type,
        affiliation: data.affiliation,
        email: data.email,
        social_id: userDataSocial.social_id || null,

      };

      // Store user data in localStorage
      localStorage.setItem('user', JSON.stringify(userData));

      dispatch(loginSuccess(userData));

      setSnackbar({
        open: true,
        message: 'Successfully signed in!',
        severity: 'success'
      });

      // Redirect to list-docids page after successful login
      router.push('/list-docids');
    } catch (error) {
      dispatch(loginFailure('An error occurred during sign in. Please try again.'));
      setSnackbar({
        open: true,
        message: 'An error occurred during sign in. Please try again.',
        severity: 'error'
      });
    }
  };


  //social login

  const handleSocialLogin = async (provider) => {
    //setLoading(true);
    //setShowReload(false);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_BASE_URL;
      
      switch(provider) {
        case 'ORCID':
          console.log('Final baseUrl:', baseUrl);
          const redirectUri = `${baseUrl}/callback/orcid`;
          const scope = process.env.NEXT_PUBLIC_ORCID_SCOPE || '/authenticate';
          const clientId = process.env.NEXT_PUBLIC_ORCID_CLIENT_ID;
          const orcidAuthorizeUrl = process.env.NEXT_PUBLIC_ORCID_SANDBOX_URL;
          
          const authUrl = `${orcidAuthorizeUrl}?client_id=${clientId}&response_type=code&scope=${scope}&redirect_uri=${redirectUri}`;
          console.log('authUrl', authUrl);
          window.location.href = authUrl;
          break;
          
        case 'Google':
          const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
          const googleRedirectUri = process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI;;
          const googleScope = 'profile email';
          const googleAuthUrl = `https://accounts.google.com/o/oauth2/auth?client_id=${googleClientId}&redirect_uri=${googleRedirectUri}&scope=${googleScope}&response_type=code`;
          window.location.href = googleAuthUrl;
          break;
          
        case 'GitHub':
          const githubClientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID;
          const githubRedirectUri = `${baseUrl}/callback/github`;
          const githubScope = 'user:email';
          const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${githubClientId}&redirect_uri=${githubRedirectUri}&scope=${githubScope}`;
          window.location.href = githubAuthUrl;
          break;
          
        default:
          const fallbackBaseUrl = process.env.NEXT_PUBLIC_BASE_URL;
          window.location.href = `${fallbackBaseUrl}/auth/${provider}`;
      }
    } catch (error) {
      console.error("Social login error:", error);
      setSnackbar({
        open: true,
        message: "An error occurred during social login. Please try again.",
        severity: "error"
      });
    }
  };
  
  
  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (!resetEmail) {
      setResetEmailError(t('auth.email_required'));
      return;
    }
    if (!/\S+@\S+\.\S+/.test(resetEmail)) {
      setResetEmailError(t('auth.valid_email_required'));
      return;
    }
    
    setIsResetting(true);
    try {
      const response = await axios.post(
        `/api/auth/request-reset-password`,
        { 
          type: 'email', 
          email: resetEmail 
        }
      );

      const message = response.data.message;

      if (message === "Email not found for the given type.") {
        setSnackbar({
          open: true,
          message: "Email not found in our database or used as social login",
          severity: 'warning'
        });
      } else if (message === "Email provided does not exists!") {
        setSnackbar({
          open: true,
          message: message,
          severity: 'warning'
        });
      } else {
        setResetPasswordModal(false);
        setShowSuccessModal(true);
      }
      setResetEmail('');
    } catch (error) {
      console.error("Password reset request error:", error);
      setSnackbar({
        open: true,
        message: "Failed to request password reset.",
        severity: 'error'
      });
    } finally {
      setIsResetting(false);
    }
  };

  const handleLogout = () => {
    dispatch(logout());
    setSnackbar({
      open: true,
      message: 'Successfully logged out!',
      severity: 'success'
    });
    router.push('/');
  };

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
              {/* Logo and Title */}
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
                  <LockOutlined sx={{ color: 'white', fontSize: 24 }} />
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
                  {t('auth.welcome_back')}
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    color: theme.palette.text.secondary,
                    textAlign: 'center'
                  }}
                >
                  {t('auth.sign_in_subtitle')}
                </Typography>
              </Box>

              {/* Error Alert */}
              {showError && (
                <Slide direction="down" in={showError}>
                  <Alert 
                    severity="error" 
                    onClose={() => setShowError(false)}
                    sx={{ width: '100%', mb: 2 }}
                  >
                    {t('auth.correct_errors')}
                  </Alert>
                </Slide>
              )}

              {/* Login Form */}
              <Box 
                component="form" 
                onSubmit={handleSignIn}
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
                  autoFocus
                  value={formData.email}
                  onChange={handleChange}
                  error={!!errors.email}
                  helperText={errors.email}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <EmailIcon color={errors.email ? "error" : "primary"} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    mb: 2,
                    '& .MuiOutlinedInput-root': {
                      '&:hover fieldset': {
                        borderColor: theme.palette.primary.main,
                      },
                    }
                  }}
                />
                <TextField
                  margin="normal"
                  required
                  fullWidth
                  name="password"
                  label={t('auth.password')}
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  autoComplete="current-password"
                  value={formData.password}
                  onChange={handleChange}
                  error={!!errors.password}
                  helperText={errors.password}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LockIcon color={errors.password ? "error" : "primary"} />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPassword(!showPassword)}
                          edge="end"
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    mb: 2,
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
                  disabled={loading}
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
                  {loading ? (
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <CircularProgress 
                        size={24} 
                        sx={{ 
                          color: 'white',
                          mr: 1
                        }} 
                      />
                      {t('auth.signing_in')}
                    </Box>
                  ) : (
                    t('auth.sign_in')
                  )}
                </Button>

                {/* Links */}
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: { xs: 'column', sm: 'row' },
                    justifyContent: 'space-between',
                    alignItems: { xs: 'stretch', sm: 'center' },
                    gap: 1,
                    mb: 3
                  }}
                >
                  <Button
                    variant="text"
                    onClick={() => setResetPasswordModal(true)}
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
                    {t('auth.forgot_password')}
                  </Button>
                  <Button
                    variant="text"
                    onClick={() => router.push('/register')}
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
                    {t('auth.dont_have_account')}
                  </Button>
                </Box>

                <Divider>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      color: theme.palette.text.secondary,
                      px: 2
                    }}
                  >
                    {t('auth.or_sign_in_with')}
                  </Typography>
                </Divider>

                {/* Social Login Buttons */}
                <Box 
                  sx={{ 
                    mt: 3,
                    display: 'flex',
                    justifyContent: 'center',
                    gap: 2,
                    flexWrap: 'wrap'
                  }}
                >
                  {[
                    {
                      icon: <GitHub sx={{ fontSize: 22 }} />,
                      name: 'GitHub',
                      color: '#24292e',
                      hoverBg: 'rgba(36, 41, 46, 0.04)'
                    },
                    {
                      icon: <Google sx={{ fontSize: 22 }} />,
                      name: 'Google',
                      color: '#db4437',
                      hoverBg: 'rgba(219, 68, 55, 0.04)'
                    },
                    {
                      icon: (
                        <Image
                          src="/assets/images/orcid-logo.png"
                          alt="ORCID"
                          width={22}
                          height={22}
                        />
                      ),
                      name: 'ORCID',
                      color: '#a6ce39',
                      hoverBg: 'rgba(166, 206, 57, 0.04)'
                    }
                  ].map((provider, index) => (
                    <Button
                      onClick={() => handleSocialLogin(provider.name)}
                      key={index}
                      variant="outlined"
                      startIcon={provider.icon}
                      aria-label={`Sign in with ${provider.name}`}
                      sx={{
                        minWidth: '120px',
                        height: 42,
                        color: provider.color,
                        borderColor: provider.color,
                        backgroundColor: 'transparent',
                        fontSize: '0.9rem',
                        fontWeight: 500,
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          backgroundColor: provider.hoverBg,
                          borderColor: provider.color,
                          transform: 'translateY(-2px)',
                          boxShadow: `0 4px 8px ${provider.color}33`
                        }
                      }}
                    >
                      {provider.name}
                    </Button>
                  ))}
                </Box>
              </Box>
            </Box>
          </Slide>
        </Container>
      </Box>

      {/* Reset Password Modal */}
      <Modal
        open={resetPasswordModal}
        onClose={() => {
          setResetPasswordModal(false);
          setResetEmail('');
          setResetEmailError('');
        }}
        aria-labelledby="reset-password-modal"
      >
        <Paper
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: { xs: '90%', sm: 700 },
            outline: 'none',
            borderRadius: 2,
            overflow: 'hidden'
          }}
        >
          {/* Header */}
          <Box
            sx={{
              bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : '#1565c0',
              py: 2,
              px: 3,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <Typography
              variant="h6"
              component="h2"
              sx={{
                color: 'white',
                fontWeight: 600
              }}
            >
              {t('auth.reset_password')}
            </Typography>
            <IconButton
              onClick={() => {
                setResetPasswordModal(false);
                setResetEmail('');
                setResetEmailError('');
              }}
              sx={{ 
                color: 'white',
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.1)'
                }
              }}
              aria-label="close"
            >
              <CloseIcon />
            </IconButton>
          </Box>
          
          <Box 
            component="form" 
            onSubmit={handleResetPassword}
            sx={{
              p: 3
            }}
          >
            <TextField
              fullWidth
              label={t('auth.email_address')}
              type="email"
              value={resetEmail}
              onChange={(e) => {
                setResetEmail(e.target.value);
                setResetEmailError('');
              }}
              error={!!resetEmailError}
              helperText={resetEmailError}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <EmailIcon color={resetEmailError ? "error" : "primary"} />
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 3 }}
            />
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={isResetting}
              sx={{
                py: 1.5,
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
              {isResetting ? (
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
                  <CircularProgress 
                    size={24} 
                    sx={{ 
                      color: 'white',
                      mr: 1
                    }} 
                  />
                  {t('auth.sending_reset_link')}
                </Box>
              ) : (
                t('auth.reset_password')
              )}
            </Button>
          </Box>
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
            width: { xs: '90%', sm: 600 },
            p: 4,
            outline: 'none',
            borderRadius: 2,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center'
          }}
        >
          <CheckCircleOutline
            sx={{
              fontSize: 64,
              color: 'success.main',
              mb: 2
            }}
          />
          <Typography
            variant="h6"
            component="h2"
            sx={{
              fontWeight: 600,
              mb: 1
            }}
          >
            {t('auth.password_reset_success')}
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: 'text.secondary',
              mb: 3
            }}
          >
            {t('auth.password_reset_message')}
          </Typography>
          <Button
            variant="contained"
            onClick={() => setShowSuccessModal(false)}
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
            {t('auth.ok')}
          </Button>
        </Paper>
      </Modal>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))} 
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default LoginPage; 