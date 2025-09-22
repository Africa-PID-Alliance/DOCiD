'use client';

import React, { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import axios from "axios";
import { Backdrop, CircularProgress, TextField, Button, Box, Container, Avatar, Link, Grid, Typography, IconButton, InputAdornment, Snackbar, Alert, Paper, LinearProgress } from "@mui/material";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import { useDispatch, useSelector } from "react-redux";
import { loginStart, loginSuccess, loginFailure, logout } from '@/redux/slices/authSlice';
import { updateUser } from "@/redux/dataSlice";

const CallbackOrcid = ({ onCallback }) => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [response1, setResponse1] = useState();
  const [email, setEmail] = useState("");
  const [dbID, setDbID] = useState("");
  const [password, setPassword] = useState("");
  const dispatch = useDispatch();
  const [authName, setAuthName] = useState("");
  const [authPhoto, setAuthPhoto] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [data, setData] = useState(null);
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
      router.push("/list-docids/1");
    }
  }, [user, router, lang]);

  useEffect(() => {
    const code = searchParams.get("code");
    if (code) {
      exchangeCodeForToken(code);
    }
  }, [searchParams]);

  // Process flag to prevent duplicate requests
  const processingRef = React.useRef(false);

  const exchangeCodeForToken = async (code) => {
    // Skip if already processing this code
    if (processingRef.current) {
      console.log("Already processing a code, skipping duplicate request");
      return;
    }
    
    processingRef.current = true;
    
    try {
      const baseUrl = process.env.NEXT_PUBLIC_BASE_URL;
      console.log('Final baseUrl:', baseUrl);
      const redirectUri = `${baseUrl}/callback/orcid`;
 
      const response = await fetch(
        `/api/auth/orcid/token?code=${code}&redirectUri=${redirectUri}`
      );

      const userData = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to exchange code for token');
    }

    console.log('Token exchange successful:', data);

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
      setLoading(false);
    } catch (error) {
      setLoading(false);
      console.error("Error during callback", error);
      
      // Handle specific error cases
      if (error.response?.data?.error === 'invalid_grant') {
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

export default CallbackOrcid;
