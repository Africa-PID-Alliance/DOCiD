'use client';

import React, { useEffect, useState, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CircularProgress, Box, Container, LinearProgress, Paper, Typography } from "@mui/material";
import { useDispatch, useSelector } from "react-redux";
import { updateUser } from "@/redux/dataSlice";
import { loginSuccess } from "@/redux/slices/authSlice";

const CallbackGoogle = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(true);
  const dispatch = useDispatch();
  const exchangeAttempted = useRef(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "info"
  });

  const user = useSelector((state) => state.data.user);
  const lang = useSelector((state) => state.data.lang);

  useEffect(() => {
    if (user) {
      setLoading(false);
      setSnackbar({
        open: true,
        message: lang === "English" ? "Welcome to the DOCiD™" :
          lang === "Kiswahili" ? "Karibu kwenye DOCiD™" :
            lang === "French" ? "Bienvenue sur le DOCiD™" :
              lang === "Arabic" ? "مرحبا بكم في DOCiD™" :
                lang === "German" ? "Willkommen beim DOCiD™" :
                  lang === "Portugal" ? "Bem-vindo ao DOCiD™" :
                    "Welcome to the DOCiD™",
        severity: "success"
      });
      router.push("/list-docids");
    }
  }, [user, router, lang]);

  useEffect(() => {
    const code = searchParams.get("code");
    if (code && !exchangeAttempted.current) {
      exchangeAttempted.current = true;
      exchangeCodeForToken(code);
    }
  }, [searchParams]);

  const exchangeCodeForToken = async (code) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_BASE_URL;
      console.log('baseUrl', baseUrl);
      const redirectUri = `${baseUrl}/callback/google`;

      const response = await fetch(`/api/auth/google/token?code=${code}`)
      const userData = await response.json();

      if (!response.ok) {
        console.error('Token exchange failed:', userData);
        throw new Error(userData.error || 'Failed to exchange code for token');
      }

      console.log('Token exchange successful:', userData);

      // Store user data in localStorage
      localStorage.setItem('user', JSON.stringify(userData));

      // Update the Redux store with user data
      dispatch(loginSuccess(userData));

      setSnackbar({
        open: true,
        message: 'Successfully signed in!',
        severity: 'success'
      });

      // Redirect to list-docids page after successful login
      router.push('/list-docids');
    } catch (error) {
      setLoading(false);
      console.error("Error during callback:", error.message);
      
      // Clear the exchange attempted flag to allow a retry if the page is refreshed
      if (error.message?.includes('network') || error.message?.includes('failed to fetch')) {
        exchangeAttempted.current = false;
      }
      
      // Handle specific error cases
      if (error.message?.includes('Request already processed')) {
        setSnackbar({
          open: true,
          message: "Your login is already being processed. Please wait...",
          severity: "info"
        });
      } else if (error.message?.includes('bad_verification_code') || error.response?.data?.error === 'invalid_grant') {
        setSnackbar({
          open: true,
          message: "Your login session has expired. Please try logging in again.",
          severity: "warning"
        });
        // Redirect to login page after a short delay
        setTimeout(() => {
          router.push('/login');
        }, 2000);
      } else {
        setSnackbar({
          open: true,
          message: "Error during authentication. Please try again.",
          severity: "error"
        });
        // Redirect to login page after a short delay
        setTimeout(() => {
          router.push('/login');
        }, 2000);
      }
    } 
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'grey.50'
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={3}
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 3
          }}
        >
          <CircularProgress size={60} />
          <Typography variant="h4" component="h1" fontWeight="bold" color="text.primary">
            Processing Login
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Please wait while we complete your authentication
          </Typography>
          <Box sx={{ width: '100%', mt: 2 }}>
            <LinearProgress />
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default CallbackGoogle; 