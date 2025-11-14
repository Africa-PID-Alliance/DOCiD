'use client'
import { Box, Container, Grid, Paper, Typography, useTheme, Divider, Modal, IconButton, Collapse } from '@mui/material';
import { motion } from 'framer-motion';
import Image from 'next/image';
import React, { useState } from 'react'
import ZoomOutMapIcon from '@mui/icons-material/ZoomOutMap';
import CloseIcon from '@mui/icons-material/Close';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useTranslation } from 'react-i18next';


const AboutDocid = () => {
  const [openModal, setOpenModal] = useState(false)
  const [selectedImage, setSelectedImage] = useState(null);
  const [expandedInnovation, setExpandedInnovation] = useState(false);
  const { t } = useTranslation();

  const theme = useTheme();

  const handleOpenModal = (imageSrc) => {
    setSelectedImage(imageSrc);
    setOpenModal(true);
  };
  const handleCloseModal = () => {
    setOpenModal(false);
    setSelectedImage(null);
  };

  const handleToggleInnovation = () => {
    setExpandedInnovation(!expandedInnovation);
  };

  const commonTypographyStyles = {
    fontSize: '1.1rem',
    lineHeight: 1.8,
    textAlign: 'justify',
    color: theme.palette.text.primary
  };

  const MotionPaper = motion(Paper);

  const fadeInUp = {
    initial: { opacity: 0, y: 30 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.8, ease: "easeOut" }
  };

  const staggerContainer = {
    animate: {
      transition: {
        staggerChildren: 0.2
      }
    }
  };



  return (
    <Box sx={{ bgcolor: theme.palette.background.content, minHeight: '100vh' }}>
      {/* Header Section with Logo */}
      <Box
        component={motion.div}
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, ease: "easeOut" }}
        sx={{
          bgcolor: '#141a3b',
          py: { xs: 6, md: 10 },
          borderBottom: `1px solid ${theme.palette.divider}`,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Container
          maxWidth="lg"
          sx={{
            width: '100%',
            maxWidth: { sm: '100%', md: '100%', lg: '100%' },
            position: 'relative',
            zIndex: 1,

          }}
        >
          <Box sx={{ textAlign: 'center' }}>

            <Typography
              variant="h1"
              sx={{
                color: theme.palette.text.light,
                fontWeight: 800,
                mb: 3,
                fontSize: { xs: '1.5rem', sm: '2rem', md: '2.5rem' },
                letterSpacing: '-0.02em',
                lineHeight: 1.2
              }}
            >
              {t('about.title')}
            </Typography>
            <Box
              sx={{
                position: 'relative',
                width: { xs: '180px', md: '220px' },
                height: { xs: '72px', md: '88px' },
                margin: '0 auto 2rem',
                transition: 'transform 0.3s ease',
                '&:hover': {
                  transform: 'scale(1.05)'
                }
              }}
            >
              <Image
                src="/assets/images/Logo2.png"
                alt="DOCiD Logo"
                fill
                style={{
                  objectFit: 'contain'
                }}
                sizes="(max-width: 600px) 180px, 220px"
                priority
              />
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Main Content */}
      <Container
        maxWidth="lg"
        sx={{
          py: { xs: 6, md: 10 },
          width: '90%',
          maxWidth: { sm: '90%', md: '85%', lg: '80%' }
        }}
      >

        <Grid
          container
          spacing={{ xs: 4, md: 6 }}
          component={motion.div}
          variants={staggerContainer}
          initial="initial"
          animate="animate"
        >
          {/* Mission Section */}
          <Grid item xs={12} md={6}>
            <MotionPaper
              variants={fadeInUp}
              elevation={3}
              sx={{
                p: { xs: 3, md: 4 },
                height: '100%',
                bgcolor: 'background.paper',
                borderRadius: 3,
                transition: 'all 0.3s ease-in-out',
              }}
            >
              <Typography
                variant="h4"
                component="h2"
                sx={{
                  color: theme.palette.primary.main,
                  fontWeight: 700,
                  mb: 3,
                  fontSize: { xs: '1.75rem', md: '2rem' }
                }}
              >
                {t('about.mission_title')}
              </Typography>
              <Typography variant="body1" sx={commonTypographyStyles}>
                {t('about.mission_text')}
              </Typography>
            </MotionPaper>
          </Grid>

          {/* Open Infrastructure Section */}
          <Grid item xs={12} md={6}>
            <MotionPaper
              variants={fadeInUp}
              elevation={3}
              sx={{
                p: { xs: 3, md: 4 },
                height: '100%',
                bgcolor: 'background.paper',
                borderRadius: 3,
                transition: 'all 0.3s ease-in-out',
              }}
            >
              <Typography
                variant="h4"
                component="h2"
                sx={{
                  color: theme.palette.primary.main,
                  fontWeight: 700,
                  mb: 3,
                  fontSize: { xs: '1.75rem', md: '2rem' }
                }}
              >
                {t('about.infrastructure_title')}
              </Typography>
              <Typography variant="body1" sx={commonTypographyStyles}>
                {t('about.infrastructure_text')}
              </Typography>
            </MotionPaper>
          </Grid>

          {/* Who Should Use DOCiD Section */}
          <Grid item xs={12}>
            <MotionPaper
              variants={fadeInUp}
              elevation={1}
              sx={{
                p: { xs: 3, md: 4 },
                bgcolor: 'background.paper',
                borderRadius: 3,
                transition: 'all 0.3s ease-in-out',
              }}
            >
              <Typography
                variant="h4"
                component="h2"
                sx={{
                  color: theme.palette.primary.dark,
                  fontWeight: 700,
                  mb: { xs: 2, sm: 4 },
                  fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                  textAlign: 'center'
                }}
              >
                {t('about.who_should_use_title')}
              </Typography>

              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: { xs: 2, sm: 4 }
                }}
              >
                <Box
                  sx={{
                    position: 'relative',
                    width: '100%',
                    maxWidth: { xs: '280px', sm: '400px' },
                    height: 'auto',
                    borderRadius: 3,
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mb: { xs: 2, sm: 4 }
                  }}
                >
                  <Image
                    src={theme.palette.mode === 'dark' ? '/assets/images/Logo2.png' : '/assets/images/Docid-dark.png'}
                    alt="Who should use DOCiD"
                    width={200}
                    height={100}
                    style={{
                      width: '70%',
                      height: 'auto'
                    }}
                    priority
                    quality={100}
                  />
                </Box>

                <Typography
                  variant="body1"
                  sx={{
                    textAlign: 'center',
                    color: theme.palette.text.primary,
                    fontSize: { xs: '1rem', sm: '1.1rem', md: '1.2rem' },
                    maxWidth: '800px',
                    lineHeight: 1.6,
                    mb: { xs: 3, sm: 6 },
                    px: { xs: 2, sm: 4 }
                  }}
                >
                  {t('about.who_should_use_text')}
                </Typography>

                <Grid container spacing={{ xs: 2, sm: 3, md: 4 }} sx={{ justifyContent: 'center', width: '100%', mx: 'auto' }}>
                  {/* Universities Card */}
                  <Grid item xs={12} sm={6} md={4} lg={2.4} sx={{ width: '100%', display: 'flex' }}>
                    <Box
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        p: { xs: 1, sm: 2 },
                        bgcolor: 'background.paper',
                        borderRadius: 2,
                        transition: 'transform 0.3s ease-in-out',
                        '&:hover': {
                          transform: 'translateY(-5px)'
                        },
                        height: '100%',
                        width: '100%'
                      }}
                    >
                      <Box
                        sx={{
                          width: { xs: 100, sm: 120, md: 150 },
                          height: { xs: 100, sm: 120, md: 150 },
                          mb: { xs: 1, sm: 2 },
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0
                        }}
                      >
                        <Image
                          src="/assets/images/universities-icon.png"
                          alt="Universities Icon"
                          width={150}
                          height={150}
                          style={{ objectFit: 'contain', width: '100%', height: '100%' }}
                        />
                      </Box>
                      <Box
                        sx={{
                          position: 'relative',
                          width: '100%',
                          mt: { xs: 1, sm: 2 },
                          pt: { xs: 2, sm: 3 },
                          px: { xs: 1, sm: 2 },
                          pb: { xs: 1, sm: 2 },
                          border: `2px solid ${theme.palette.primary.main}`,
                          borderRadius: 1,
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'center'
                        }}
                      >
                        <Typography
                          variant="subtitle2"
                          sx={{
                            position: 'absolute',
                            top: 0,
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            bgcolor: 'background.paper',
                            px: 2,
                            fontWeight: 600,
                            color: theme.palette.primary.main,
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {t('about.universities')}
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            textAlign: 'center',
                            color: theme.palette.text.primary,
                            lineHeight: 1.5,
                            flex: 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            px: 1,
                            fontSize: '0.875rem'
                          }}
                        >
                          {t('about.universities_text')}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>

                  {/* Museums Card */}
                  <Grid item xs={12} sm={6} md={4} lg={2.4} sx={{ width: '100%', display: 'flex' }}>
                    <Box
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        p: { xs: 1, sm: 2 },
                        bgcolor: 'background.paper',
                        borderRadius: 2,
                        transition: 'transform 0.3s ease-in-out',
                        '&:hover': {
                          transform: 'translateY(-5px)'
                        },
                        height: '100%',
                        width: '100%'
                      }}
                    >
                      <Box
                        sx={{
                          width: { xs: 100, sm: 120, md: 150 },
                          height: { xs: 100, sm: 120, md: 150 },
                          mb: { xs: 1, sm: 2 },
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0
                        }}
                      >
                        <Image
                          src="/assets/images/museums-Icon.png"
                          alt="Museums Icon"
                          width={150}
                          height={150}
                          style={{ objectFit: 'contain', width: '100%', height: '100%' }}
                        />
                      </Box>
                      <Box
                        sx={{
                          position: 'relative',
                          width: '100%',
                          mt: { xs: 1, sm: 2 },
                          pt: { xs: 2, sm: 3 },
                          px: { xs: 1, sm: 2 },
                          pb: { xs: 1, sm: 2 },
                          border: `2px solid ${theme.palette.primary.main}`,
                          borderRadius: 1,
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'center'
                        }}
                      >
                        <Typography
                          variant="subtitle2"
                          sx={{
                            position: 'absolute',
                            top: 0,
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            bgcolor: 'background.paper',
                            px: 2,
                            fontWeight: 600,
                            color: theme.palette.primary.main,
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {t('about.museums')}
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            textAlign: 'center',
                            color: theme.palette.text.primary,
                            lineHeight: 1.5,
                            flex: 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            px: 1,
                            fontSize: '0.875rem'
                          }}
                        >
                          {t('about.museums_text')}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>

                  {/* Patent Registration Offices Card */}
                  <Grid item xs={12} sm={6} md={4} lg={2.4} sx={{ width: '100%', display: 'flex' }}>
                    <Box
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        p: { xs: 1, sm: 2 },
                        bgcolor: 'background.paper',
                        borderRadius: 2,
                        transition: 'transform 0.3s ease-in-out',
                        '&:hover': {
                          transform: 'translateY(-5px)'
                        },
                        height: '100%',
                        width: '100%'
                      }}
                    >
                      <Box
                        sx={{
                          width: { xs: 100, sm: 120, md: 150 },
                          height: { xs: 100, sm: 120, md: 150 },
                          mb: { xs: 1, sm: 2 },
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0
                        }}
                      >
                        <Image
                          src="/assets/images/patent-icon.png"
                          alt="Patent Registration Offices Icon"
                          width={150}
                          height={150}
                          style={{ objectFit: 'contain', width: '100%', height: '100%' }}
                        />
                      </Box>
                      <Box
                        sx={{
                          position: 'relative',
                          width: '100%',
                          mt: { xs: 1, sm: 2 },
                          pt: { xs: 2, sm: 3 },
                          px: { xs: 1, sm: 2 },
                          pb: { xs: 1, sm: 2 },
                          border: `2px solid ${theme.palette.primary.main}`,
                          borderRadius: 1,
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'center'
                        }}
                      >
                        <Typography
                          variant="subtitle2"
                          sx={{
                            position: 'absolute',
                            top: 0,
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            bgcolor: 'background.paper',
                            px: 2,
                            fontWeight: 600,
                            color: theme.palette.primary.main,
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {t('about.patent_offices')}
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            textAlign: 'center',
                            color: theme.palette.text.primary,
                            lineHeight: 1.5,
                            flex: 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            px: 1,
                            fontSize: '0.875rem'
                          }}
                        >
                          {t('about.patent_offices_text')}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>

                  {/* Research Projects Card */}
                  <Grid item xs={12} sm={6} md={4} lg={2.4} sx={{ width: '100%', display: 'flex' }}>
                    <Box
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        p: { xs: 1, sm: 2 },
                        bgcolor: 'background.paper',
                        borderRadius: 2,
                        transition: 'transform 0.3s ease-in-out',
                        '&:hover': {
                          transform: 'translateY(-5px)'
                        },
                        height: '100%',
                        width: '100%'
                      }}
                    >
                      <Box
                        sx={{
                          width: { xs: 100, sm: 120, md: 150 },
                          height: { xs: 100, sm: 120, md: 150 },
                          mb: { xs: 1, sm: 2 },
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0
                        }}
                      >
                        <Image
                          src="/assets/images/Research-icon.png"
                          alt="Research Projects Icon"
                          width={150}
                          height={150}
                          style={{ objectFit: 'contain', width: '100%', height: '100%' }}
                        />
                      </Box>
                      <Box
                        sx={{
                          position: 'relative',
                          width: '100%',
                          mt: { xs: 1, sm: 2 },
                          pt: { xs: 2, sm: 3 },
                          px: { xs: 1, sm: 2 },
                          pb: { xs: 1, sm: 2 },
                          border: `2px solid ${theme.palette.primary.main}`,
                          borderRadius: 1,
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'center'
                        }}
                      >
                        <Typography
                          variant="subtitle2"
                          sx={{
                            position: 'absolute',
                            top: 0,
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            bgcolor: 'background.paper',
                            px: 2,
                            fontWeight: 600,
                            color: theme.palette.primary.main,
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {t('about.research_projects')}
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            textAlign: 'center',
                            color: theme.palette.text.primary,
                            lineHeight: 1.5,
                            flex: 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            px: 1,
                            fontSize: '0.875rem'
                          }}
                        >
                          {t('about.research_projects_text')}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>

                  {/* Other PID Providers Card */}
                  <Grid item xs={12} sm={6} md={4} lg={2.4} sx={{ width: '100%', display: 'flex' }}>
                    <Box
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        p: { xs: 1, sm: 2 },
                        bgcolor: 'background.paper',
                        borderRadius: 2,
                        transition: 'transform 0.3s ease-in-out',
                        '&:hover': {
                          transform: 'translateY(-5px)'
                        },
                        height: '100%',
                        width: '100%'
                      }}
                    >
                      <Box
                        sx={{
                          width: { xs: 100, sm: 120, md: 150 },
                          height: { xs: 100, sm: 120, md: 150 },
                          mb: { xs: 1, sm: 2 },
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0
                        }}
                      >
                        <Image
                          src="/assets/images/other-icon.png"
                          alt="Other PID Providers Icon"
                          width={150}
                          height={150}
                          style={{ objectFit: 'contain', width: '100%', height: '100%' }}
                        />
                      </Box>
                      <Box
                        sx={{
                          position: 'relative',
                          width: '100%',
                          mt: { xs: 1, sm: 2 },
                          pt: { xs: 2, sm: 3 },
                          px: { xs: 1, sm: 2 },
                          pb: { xs: 1, sm: 2 },
                          border: `2px solid ${theme.palette.primary.main}`,
                          borderRadius: 1,
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'center'
                        }}
                      >
                        <Typography
                          variant="subtitle2"
                          sx={{
                            position: 'absolute',
                            top: 0,
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            bgcolor: 'background.paper',
                            px: 2,
                            fontWeight: 600,
                            color: theme.palette.primary.main,
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {t('about.other_pid_providers')}
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            textAlign: 'center',
                            color: theme.palette.text.primary,
                            lineHeight: 1.5,
                            flex: 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            px: 1,
                            fontSize: '0.875rem'
                          }}
                        >
                          {t('about.other_pid_providers_text')}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                </Grid>
              </Box>
            </MotionPaper>
          </Grid>

          {/* Scenarios Section */}
          <Grid item xs={12}>
            <MotionPaper
              variants={fadeInUp}
              elevation={3}
              sx={{
                p: { xs: 3, md: 4 },
                bgcolor: 'background.paper',
                borderRadius: 3,
                transition: 'all 0.3s ease-in-out',
              }}
            >
              <Typography
                variant="h4"
                component="h2"
                sx={{
                  color: theme.palette.primary.main,
                  fontWeight: 700,
                  mb: 4,
                  fontSize: { xs: '1.75rem', md: '2rem' }
                }}
              >
                {t('about.use_cases_title')}
              </Typography>

              <Grid container spacing={4}>

                {/* Universities Scenario */}
                <Grid item xs={12} md={6}>
                  <Box sx={{ height: '100%' }}>
                    <Box
                      sx={{
                        position: 'relative',
                        width: '100%',
                        height: '300px',
                        mb: 2,
                        borderRadius: 2,
                        overflow: 'hidden',
                        boxShadow: `0 4px 16px ${theme.palette.primary.main}15`,
                        cursor: 'pointer',
                        transition: 'transform 0.3s ease',
                        '&:hover': {
                          transform: 'scale(1.02)',
                          '& .expand-overlay': {
                            opacity: 1
                          }
                        }
                      }}
                      onClick={() => handleOpenModal('/assets/images/universities.png')}
                    >
                      <Image
                        src="/assets/images/universities.png"
                        alt="University Use Case"
                        fill
                        style={{
                          objectFit: 'contain',
                          backgroundColor: '#f5f5f5'
                        }}
                        sizes="(max-width: 600px) 100vw, 600px"
                      />
                      <Box
                        className="expand-overlay"
                        sx={{
                          position: 'absolute',
                          bottom: 0,
                          left: 0,
                          right: 0,
                          bgcolor: 'rgba(0, 0, 0, 0.7)',
                          color: 'white',
                          p: 2,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          opacity: 0,
                          transition: 'opacity 0.3s ease',
                        }}
                      >
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {t('about.click_to_expand')}
                        </Typography>
                        <ZoomOutMapIcon />
                      </Box>
                    </Box>
                    <Typography variant="h6" sx={{ mb: 1, color: theme.palette.primary.main }}>
                      {t('about.universities')}
                    </Typography>

                  </Box>
                </Grid>

                {/* Museum Scenario */}
                <Grid item xs={12} md={6}>
                  <Box sx={{ height: '100%' }}>
                    <Box
                      sx={{
                        position: 'relative',
                        width: '100%',
                        height: '300px',
                        mb: 2,
                        borderRadius: 2,
                        overflow: 'hidden',
                        boxShadow: `0 4px 16px ${theme.palette.primary.main}15`,
                        cursor: 'pointer',
                        transition: 'transform 0.3s ease',
                        '&:hover': {
                          transform: 'scale(1.02)',
                          '& .expand-overlay': {
                            opacity: 1
                          }
                        }
                      }}
                      onClick={() => handleOpenModal('/assets/images/museum.png')}
                    >
                      <Image
                        src="/assets/images/museum.png"
                        alt="Museum Use Case"
                        fill
                        style={{
                          objectFit: 'contain',
                          backgroundColor: '#f5f5f5'
                        }}
                        sizes="(max-width: 600px) 100vw, 600px"
                      />
                      <Box
                        className="expand-overlay"
                        sx={{
                          position: 'absolute',
                          bottom: 0,
                          left: 0,
                          right: 0,
                          bgcolor: 'rgba(0, 0, 0, 0.7)',
                          color: 'white',
                          p: 2,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          opacity: 0,
                          transition: 'opacity 0.3s ease',
                        }}
                      >
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {t('about.click_to_expand')}
                        </Typography>
                        <ZoomOutMapIcon />
                      </Box>
                    </Box>
                    <Typography variant="h6" sx={{ mb: 1, color: theme.palette.primary.main }}>
                      {t('about.museums')}
                    </Typography>

                  </Box>
                </Grid>



                {/* Patent Registration Offices Scenario */}
                <Grid item xs={12} md={6}>
                  <Box sx={{ height: '100%' }}>
                    <Box
                      sx={{
                        position: 'relative',
                        width: '100%',
                        height: '300px',
                        mb: 2,
                        borderRadius: 2,
                        overflow: 'hidden',
                        boxShadow: `0 4px 16px ${theme.palette.primary.main}15`,
                        cursor: 'pointer',
                        transition: 'transform 0.3s ease',
                        '&:hover': {
                          transform: 'scale(1.02)',
                          '& .expand-overlay': {
                            opacity: 1
                          }
                        }
                      }}
                      onClick={() => handleOpenModal('/assets/images/patent.png')}
                    >
                      <Image
                        src="/assets/images/patent.png"
                        alt="Patent Registration Office Use Case"
                        fill
                        style={{
                          objectFit: 'contain',
                          backgroundColor: '#f5f5f5'
                        }}
                        sizes="(max-width: 600px) 100vw, 600px"
                      />
                      <Box
                        className="expand-overlay"
                        sx={{
                          position: 'absolute',
                          bottom: 0,
                          left: 0,
                          right: 0,
                          bgcolor: 'rgba(0, 0, 0, 0.7)',
                          color: 'white',
                          p: 2,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          opacity: 0,
                          transition: 'opacity 0.3s ease',
                        }}
                      >
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {t('about.click_to_expand')}
                        </Typography>
                        <ZoomOutMapIcon />
                      </Box>
                    </Box>
                    <Typography variant="h6" sx={{ mb: 1, color: theme.palette.primary.main }}>
                      {t('about.patent_offices')}
                    </Typography>

                  </Box>
                </Grid>

                {/* Research Scenario */}
                <Grid item xs={12} md={6}>
                  <Box sx={{ height: '100%' }}>
                    <Box
                      sx={{
                        position: 'relative',
                        width: '100%',
                        height: '300px',
                        mb: 2,
                        borderRadius: 2,
                        overflow: 'hidden',
                        boxShadow: `0 4px 16px ${theme.palette.primary.main}15`,
                        cursor: 'pointer',
                        transition: 'transform 0.3s ease',
                        '&:hover': {
                          transform: 'scale(1.02)',
                          '& .expand-overlay': {
                            opacity: 1
                          }
                        }
                      }}
                      onClick={() => handleOpenModal('/assets/images/research.png')}
                    >
                      <Image
                        src="/assets/images/research.png"
                        alt="Research Use Case"
                        fill
                        style={{
                          objectFit: 'contain',
                          backgroundColor: '#f5f5f5'
                        }}
                        sizes="(max-width: 600px) 100vw, 600px"
                      />
                      <Box
                        className="expand-overlay"
                        sx={{
                          position: 'absolute',
                          bottom: 0,
                          left: 0,
                          right: 0,
                          bgcolor: 'rgba(0, 0, 0, 0.7)',
                          color: 'white',
                          p: 2,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          opacity: 0,
                          transition: 'opacity 0.3s ease',
                        }}
                      >
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {t('about.click_to_expand')}
                        </Typography>
                        <ZoomOutMapIcon />
                      </Box>
                    </Box>
                    <Typography variant="h6" sx={{ mb: 1, color: theme.palette.primary.main }}>
                      {t('about.research_projects')}
                    </Typography>

                  </Box>
                </Grid>


              </Grid>
            </MotionPaper>
          </Grid>

          {/* Approach Section */}
          <Grid item xs={12}>
            <MotionPaper
              variants={fadeInUp}
              elevation={3}
              sx={{
                p: { xs: 3, md: 4 },
                bgcolor: 'background.paper',
                borderRadius: 3,
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-8px)',
                  boxShadow: theme.shadows[8],
                }
              }}
            >
              <Typography
                variant="h4"
                component="h2"
                sx={{
                  color: theme.palette.primary.main,
                  fontWeight: 700,
                  mb: 3,
                  fontSize: { xs: '1.75rem', md: '2rem' }
                }}
              >
                {t('about.approach_title')}
              </Typography>
              <Typography variant="body1" sx={{ ...commonTypographyStyles, mb: 3 }}>
                {t('about.approach_text_1')}
              </Typography>
              <Divider sx={{ my: 3, opacity: 0.6 }} />
              <Typography variant="body1" sx={commonTypographyStyles}>
                {t('about.approach_text_2')}
              </Typography>

              {/* Diffusion of Innovation Accordion Section */}
              <Box sx={{ mt: 4 }}>
                <Box
                  onClick={handleToggleInnovation}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    p: 2,
                    borderRadius: 2,
                    bgcolor: expandedInnovation ? theme.palette.action.selected : 'transparent',
                    transition: 'all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
                    '&:hover': {
                      bgcolor: theme.palette.action.hover,
                    }
                  }}
                >
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <InfoOutlinedIcon
                        sx={{
                          fontSize: '1.4rem',
                          color: theme.palette.primary.main,
                        }}
                      />
                      <Typography
                        sx={{
                          fontWeight: 700,
                          fontSize: '1.1rem',
                          color: theme.palette.primary.main,
                        }}
                      >
                        {t('about.diffusion_innovation_title')}
                      </Typography>
                    </Box>
                    <Typography
                      variant="caption"
                      sx={{
                        color: theme.palette.text.secondary,
                        fontStyle: 'italic',
                        ml: 4.5,
                        fontSize: '0.85rem',
                      }}
                    >
                      {expandedInnovation ? t('about.diffusion_innovation_collapse') : t('about.diffusion_innovation_read_more')}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      display: 'flex',
                      transition: 'transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
                      transform: expandedInnovation ? 'rotate(180deg)' : 'rotate(0deg)',
                    }}
                  >
                    <ExpandMoreIcon sx={{ color: theme.palette.primary.main }} />
                  </Box>
                </Box>

                <Collapse
                  in={expandedInnovation}
                  timeout={1000}
                  unmountOnExit
                  easing={{
                    enter: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
                    exit: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
                  }}
                >
                  <Box
                    sx={{
                      mt: 2,
                      p: 3,
                      borderLeft: `4px solid ${theme.palette.primary.main}`,
                      bgcolor: theme.palette.mode === 'dark'
                        ? 'rgba(255, 255, 255, 0.05)'
                        : 'rgba(0, 0, 0, 0.02)',
                      borderRadius: 1,
                      animation: expandedInnovation ? 'fadeInSlide 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94)' : 'none',
                      '@keyframes fadeInSlide': {
                        '0%': {
                          opacity: 0,
                          transform: 'translateY(-10px)',
                        },
                        '100%': {
                          opacity: 1,
                          transform: 'translateY(0)',
                        },
                      },
                    }}
                  >
                    <Typography variant="body1" sx={{ ...commonTypographyStyles, mb: 3 }}>
                      {t('about.diffusion_innovation_text_1')}
                    </Typography>

                    <Typography variant="body1" sx={{ ...commonTypographyStyles, mb: 3 }}>
                      {t('about.diffusion_innovation_text_2')}
                    </Typography>

                    <Typography variant="body1" sx={{ ...commonTypographyStyles, mb: 3 }}>
                      {t('about.diffusion_innovation_text_3')}
                    </Typography>

                    <Typography variant="body1" sx={{ ...commonTypographyStyles, mb: 3 }}>
                      {t('about.diffusion_innovation_text_4')}
                    </Typography>

                    <Typography variant="body1" sx={{ ...commonTypographyStyles, mb: 3 }}>
                      {t('about.diffusion_innovation_text_5')}
                    </Typography>

                    <Typography variant="body1" sx={{ ...commonTypographyStyles, mb: 3 }}>
                      {t('about.diffusion_innovation_text_6')}
                    </Typography>

                    <Typography variant="body1" sx={{ ...commonTypographyStyles, mb: 3 }}>
                      {t('about.diffusion_innovation_text_7')}
                    </Typography>

                    <Typography variant="body1" sx={commonTypographyStyles}>
                      {t('about.diffusion_innovation_text_8')}
                    </Typography>
                  </Box>
                </Collapse>
              </Box>
            </MotionPaper>
          </Grid>

          {/* Collaboration and Showcase Section */}
          <Grid item xs={12} md={6}>
            <MotionPaper
              variants={fadeInUp}
              elevation={3}
              sx={{
                p: { xs: 3, md: 4 },
                height: '100%',
                bgcolor: 'background.paper',
                borderRadius: 3,
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-8px)',
                  boxShadow: theme.shadows[8],
                }
              }}
            >
              <Typography
                variant="h4"
                component="h2"
                sx={{
                  color: theme.palette.primary.main,
                  fontWeight: 700,
                  mb: 3,
                  fontSize: { xs: '1.75rem', md: '2rem' }
                }}
              >
                {t('about.collaboration_title')}
              </Typography>
              <Typography variant="body1" sx={commonTypographyStyles}>
                {t('about.collaboration_text')}
              </Typography>
            </MotionPaper>
          </Grid>

          {/* Showcase Section */}
          <Grid item xs={12} md={6}>
            <MotionPaper
              variants={fadeInUp}
              elevation={3}
              sx={{
                p: { xs: 3, md: 4 },
                height: '100%',
                bgcolor: 'background.paper',
                borderRadius: 3,
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-8px)',
                  boxShadow: theme.shadows[8],
                }
              }}
            >
              <Typography
                variant="h4"
                component="h2"
                sx={{
                  color: theme.palette.primary.main,
                  fontWeight: 700,
                  mb: 3,
                  fontSize: { xs: '1.75rem', md: '2rem' }
                }}
              >
                {t('about.showcase_title')}
              </Typography>
              <Box
                sx={{
                  position: 'relative',
                  width: '100%',
                  height: '300px',
                  cursor: 'pointer',
                  borderRadius: 2,
                  overflow: 'hidden',
                  transition: 'transform 0.3s ease',
                  '&:hover': {
                    transform: 'scale(1.02)',
                    '& .expand-overlay': {
                      opacity: 1
                    }
                  }
                }}
                onClick={() => handleOpenModal('/assets/images/illustrate.jpg')}
              >
                <Image
                  src="/assets/images/illustrate.jpg"
                  alt="Digital Object Container Identifier Illustration"
                  fill
                  style={{
                    objectFit: 'contain'
                  }}
                  sizes="(max-width: 600px) 100vw, 600px"
                />
                <Box
                  className="expand-overlay"
                  sx={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    bgcolor: 'rgba(0, 0, 0, 0.7)',
                    color: 'white',
                    p: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    opacity: 0,
                    transition: 'opacity 0.3s ease',
                  }}
                >
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {t('about.click_to_expand')}
                  </Typography>
                  <ZoomOutMapIcon />
                </Box>
              </Box>
            </MotionPaper>
          </Grid>
        </Grid>

      </Container>

      {/* Lightbox Modal */}
      <Modal
        open={openModal}
        onClose={handleCloseModal}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 2
        }}
      >
        <Box
          sx={{
            position: 'relative',
            maxWidth: '90vw',
            maxHeight: '90vh',
            bgcolor: 'background.paper',
            borderRadius: 2,
            boxShadow: 24,
            outline: 'none',
            overflow: 'hidden'
          }}
        >
          {/* Close Button */}
          <IconButton
            onClick={handleCloseModal}
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              bgcolor: 'rgba(0, 0, 0, 0.5)',
              color: 'white',
              zIndex: 1,
              '&:hover': {
                bgcolor: 'rgba(0, 0, 0, 0.7)'
              }
            }}
          >
            <CloseIcon />
          </IconButton>

          {/* Image */}
          {selectedImage && (
            <Box
              sx={{
                position: 'relative',
                width: '80vw',
                height: '80vh',
                maxWidth: '1200px',
                maxHeight: '800px'
              }}
            >
              <Image
                src={selectedImage}
                alt="Expanded view"
                fill
                style={{
                  objectFit: 'contain'
                }}
                sizes="80vw"
                quality={100}
              />
            </Box>
          )}
        </Box>
      </Modal>

    </Box>
  )
}

export default AboutDocid;
