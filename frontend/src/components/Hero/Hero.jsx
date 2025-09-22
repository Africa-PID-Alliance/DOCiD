"use client";

import React from 'react';
import { Box, Typography, Container, Button, useTheme } from '@mui/material';
import Image from 'next/image';
import { ArrowForward, KeyboardArrowDown } from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';

const Hero = () => {
  const router = useRouter();
  const { t } = useTranslation('common');
  const theme = useTheme();

  const handleGetStarted = () => {
    router.push('/login');
  };

  return (
    <Box
      component="section"
      sx={{
        height: '95vh',
        position: 'relative',
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        overflow: 'hidden',
      }}
    >
      {/* Background Image Container */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 0,
        }}
      >
        <Image
          src="/assets/images/hero.jpg"
          alt="Hero Background"
          fill
          sizes="100vw"
          quality={100}
          priority
          style={{
            objectFit: 'cover',
            objectPosition: 'center',
          }}
        />
        {/* Gradient Overlay */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(rgba(0, 0, 0, 0.7), rgba(25, 33, 94, 0.8))',
            zIndex: 1,
          }}
        />
      </Box>

      {/* Content */}
      <Container
        maxWidth="lg"
        sx={{
          position: 'relative',
          zIndex: 2,
          color: '#ffffff',
          textAlign: 'center',
        }}
      >
        {/* Logo */}
        <Box
          sx={{
            width: '200px',
            height: '80px',
            position: 'relative',
            margin: '0 auto 2rem',
          }}
        >
          <Image
            src="/assets/images/Logo2.png"
            alt="DOCiD™ Logo"
            fill
            sizes="200px"
            style={{
              objectFit: 'contain',
            }}
            priority
          />
        </Box>

        <Typography
          variant="h1"
          component="h1"
          sx={{
            fontWeight: 700,
            marginBottom: 3,
            fontSize: { xs: '2.5rem', md: '3.5rem' },
            color: '#ffffff',
          }}
        >
          {t('welcome')}
        </Typography>

        <Typography
          variant="subtitle1"
          sx={{
            maxWidth: '800px',
            margin: '0 auto',
            lineHeight: 1.6,
            marginBottom: 4,
            fontSize: { xs: '1rem', md: '1.1rem' },
            color: '#ffffff',
          }}
        >
          {t('hero_description')}
        </Typography>

        <Button
          onClick={handleGetStarted}
          variant="contained"
          endIcon={<ArrowForward />}
          sx={{
            backgroundColor: '#19215E',
            color: '#ffffff',
            fontSize: '1.1rem',
            padding: '12px 32px',
            textTransform: 'none',
            border: '2px solid #ffffff',
            animation: 'pulse 2s infinite',
            '@keyframes pulse': {
              '0%': {
                transform: 'scale(1)',
                boxShadow: '0 0 0 0 rgba(25, 33, 94, 0.7)',
              },
              '70%': {
                transform: 'scale(1.05)',
                boxShadow: '0 0 0 10px rgba(25, 33, 94, 0)',
              },
              '100%': {
                transform: 'scale(1)',
                boxShadow: '0 0 0 0 rgba(25, 33, 94, 0)',
              },
            },
            '&:hover': {
              backgroundColor: '#2A3275',
              transform: 'translateY(-2px)',
              boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
              animation: 'none',
              border: '2px solid #ffffff',
            },
            transition: 'all 0.3s ease',
          }}
        >
          {t('get_started')}
        </Button>
      </Container>

      {/* Scroll Indicator */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 40,
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 2,
          animation: 'bounce 2s infinite',
          '@keyframes bounce': {
            '0%, 20%, 50%, 80%, 100%': {
              transform: 'translateY(0) translateX(-50%)',
            },
            '40%': {
              transform: 'translateY(-20px) translateX(-50%)',
            },
            '60%': {
              transform: 'translateY(-10px) translateX(-50%)',
            },
          },
        }}
      >
        <KeyboardArrowDown 
          sx={{ 
            color: '#ffffff',
            fontSize: '40px',
            cursor: 'pointer',
            animation: 'glow 1.5s ease-in-out infinite alternate',
            '@keyframes glow': {
              from: {
                opacity: 0.5,
              },
              to: {
                opacity: 1,
              },
            },
          }} 
        />
      </Box>
    </Box>
  );
};

export default Hero; 