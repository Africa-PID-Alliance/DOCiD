"use client";

import React from 'react';
import { Box, Container, Typography, Grid, useTheme } from '@mui/material';
import Image from 'next/image';
import { useTranslation } from 'react-i18next';

const Content = () => {
  const { t } = useTranslation('common');
  const theme = useTheme();
  return (
    <Container maxWidth="lg" sx={{ 
      py: 5,
      my: 6
    }}>
      <Grid container spacing={6} alignItems="center">
        {/* Left Column - Text Content */}
        <Grid item xs={12} md={6}>
          <Box>
            <Typography
              variant="h4"
              component="h3"
              sx={{
                color: theme.palette.mode === 'dark' ? '#fff' : '#141a3b',
                fontWeight: 700,
                mb: 4
              }}
            >
              {t('content.decades_expertise')}
            </Typography>
            
            <Typography
              variant="body1"
              sx={{
                fontSize: '1.1rem',
                lineHeight: 1.8,
                mb: 3,
                color: theme.palette.mode === 'dark' ? '#fff' : '#333',
                textAlign: 'justify'
              }}
            >
              {t('content.expertise_description_1')}
            </Typography>

            <Typography
              variant="body1"
              sx={{
                fontSize: '1.1rem',
                lineHeight: 1.8,
                color: theme.palette.mode === 'dark' ? '#fff' : '#333',
                textAlign: 'justify'
              }}
            >
              {t('content.expertise_description_2')}
            </Typography>
          </Box>
        </Grid>

        {/* Right Column - Images */}
        <Grid item xs={12} md={6}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 6,
              alignItems: 'center',
              width: '100%',
              maxWidth: '400px',
              margin: '0 auto'
            }}
          >
            {/* TCC Logo - Now First */}
            <Box
              sx={{
                position: 'relative',
                width: '100%',
                height: '160px',
              }}
            >
              <Image
                src="/assets/images/tcc-logo.png"
                alt="TCC Logo"
                fill
                style={{
                  objectFit: 'contain',
                  objectPosition: 'center'
                }}
                sizes="400px"
              />
            </Box>

            {/* PD Logo - Now Second */}
            <Box
              sx={{
                position: 'relative',
                width: '100%',
                height: '160px',
              }}
            >
              <Image
                src="/assets/images/pd-logo.png"
                alt="PD Logo"
                fill
                style={{
                  objectFit: 'contain',
                  objectPosition: 'center'
                }}
                sizes="400px"
              />
            </Box>
          </Box>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Content; 