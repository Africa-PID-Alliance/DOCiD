"use client";

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Box, Container, Grid, Typography, Link, Stack, Divider, useTheme } from '@mui/material';
import Image from 'next/image';
import {
  Facebook,
  Twitter,
  Instagram,
  LinkedIn,
  LocationOn,
  Email,
  Phone,
  AccessTime,
  KeyboardArrowRight
} from '@mui/icons-material';

const PreFooter = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  
  const socialLinks = [
    { icon: <Facebook />, url: 'https://docid.africapidalliance.org/#', label: 'Facebook', color: '#1877F2' },
    { icon: <Twitter />, url: 'https://docid.africapidalliance.org/#', label: 'X (Twitter)', color: '#1DA1F2' },
    { icon: <Instagram />, url: 'https://docid.africapidalliance.org/#', label: 'Instagram', color: '#E4405F' },
    { icon: <LinkedIn />, url: 'https://docid.africapidalliance.org/#', label: 'LinkedIn', color: '#0A66C2' }
  ];

  const usefulLinks = [
    { text: t('pre_footer.about_alliance'), url: 'https://africapidalliance.org/' },
    { text: t('pre_footer.infrastructure_framework'), url: '/infrastructure-framework' },
    { text: t('pre_footer.community_statement'), url: 'https://africapidalliance.org/sign-apa/' },
    { text: t('pre_footer.privacy_policy'), url: 'https://africapidalliance.org/privacy-policy' },
    { text: t('pre_footer.moderation_process'), url: '/moderation-process' },
    { text: t('pre_footer.metadata_schema_docs'), url: '/docs/index.html' }
  ];

  const SectionTitle = ({ children }) => (
    <Typography 
      variant="h6" 
      sx={{ 
        mb: 3, 
        fontWeight: 700,
        position: 'relative',
        display: 'inline-block',
        '&:after': {
          content: '""',
          position: 'absolute',
          bottom: -8,
          left: 0,
          width: 40,
          height: 3,
          backgroundColor: 'rgba(255, 255, 255, 0.5)',
          borderRadius: 1
        }
      }}
    >
      {children}
    </Typography>
  );

  return (
    <Box 
      sx={{ 
        bgcolor: '#1565c0', 
        color: 'white', 
        py: { xs: 6, md:3 },
        position: 'relative',
        '&:before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '1px',
          background: 'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0) 100%)'
        }
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={6}>
          {/* Logo Column */}
          <Grid item xs={12} md={4}>
            <Box
              sx={{
                position: 'relative',
                width: '200px',
                height: '80px',
                mb: 3,
                transition: 'transform 0.3s ease',
                '&:hover': {
                  transform: 'scale(1.05)'
                }
              }}
            >
              <Image
                src="/assets/images/Logo2.png"
                alt="Logo"
                fill
                style={{
                  objectFit: 'contain'
                }}
                sizes="200px"
                priority
              />
            </Box>
            
          </Grid>

          {/* Useful Links Column */}
          <Grid item xs={12} md={4}>
            <SectionTitle>{t('pre_footer.useful_links')}</SectionTitle>
            <Stack spacing={2}>
              {usefulLinks.map((link, index) => (
                <Link
                  key={index}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{
                    color: 'white',
                    textDecoration: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    transition: 'all 0.2s ease',
                    opacity: 0.9,
                    '&:hover': {
                      opacity: 1,
                      transform: 'translateX(8px)',
                      '& .arrow': {
                        opacity: 1,
                        transform: 'translateX(4px)'
                      }
                    }
                  }}
                >
                  <KeyboardArrowRight 
                    className="arrow"
                    sx={{ 
                      fontSize: 20, 
                      mr: 1,
                      opacity: 0,
                      transform: 'translateX(-4px)',
                      transition: 'all 0.2s ease'
                    }} 
                  />
                  <Typography 
                    variant="body2"
                    sx={{ 
                      lineHeight: 1.5,
                      flex: 1
                    }}
                  >
                    {link.text}
                  </Typography>
                </Link>
              ))}
            </Stack>
          </Grid>

          {/* Address Column */}
          <Grid item xs={12} md={4}>
            <SectionTitle>{t('pre_footer.follow_social')}</SectionTitle>
            <Stack spacing={3}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <LocationOn sx={{ color: 'rgba(255, 255, 255, 0.8)' }} />
                <Typography
                  variant="body2"
                  sx={{ 
                    opacity: 0.9,
                    lineHeight: 1.6
                  }}
                >
                  {t('pre_footer.address')}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Email sx={{ color: 'rgba(255, 255, 255, 0.8)' }} />
                <Link 
                  href="mailto:info@africapidalliance.org"
                  sx={{ 
                    color: 'white', 
                    textDecoration: 'none', 
                    opacity: 0.9,
                    transition: 'all 0.2s ease',
                    '&:hover': { 
                      opacity: 1,
                      transform: 'translateX(4px)'
                    } 
                  }}
                >
                  info@africapidalliance.org
                </Link>
              </Box>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Phone sx={{ color: 'rgba(255, 255, 255, 0.8)' }} />
                <Stack spacing={0.5}>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>+254 020 808 6820</Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>+254 020 2697401</Typography>
                </Stack>
              </Box>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <AccessTime sx={{ color: 'rgba(255, 255, 255, 0.8)' }} />
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  {t('pre_footer.working_hours')}
                </Typography>
              </Box>

              <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)', my: 2 }} />

              {/* Social Media Icons */}
              <Box>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    mb: 2,
                    opacity: 0.9
                  }}
                >
                  {t('pre_footer.follow_social')}
                </Typography>
                <Stack 
                  direction="row" 
                  spacing={2}
                >
                  {socialLinks.map((social, index) => (
                    <Link
                      key={index}
                      href={social.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label={social.label}
                      sx={{
                        color: 'white',
                        bgcolor: 'rgba(255, 255, 255, 0.1)',
                        width: 36,
                        height: 36,
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          bgcolor: social.color,
                          transform: 'translateY(-4px)',
                          boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
                        },
                        '& svg': {
                          fontSize: 18
                        }
                      }}
                    >
                      {social.icon}
                    </Link>
                  ))}
                </Stack>
              </Box>
            </Stack>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default PreFooter; 