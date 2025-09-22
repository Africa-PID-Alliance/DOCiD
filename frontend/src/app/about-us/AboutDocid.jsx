'use client'
import { Box, Container, Grid, Paper, Typography, useTheme, Divider, Modal, IconButton } from '@mui/material';
import { motion } from 'framer-motion';
import Image from 'next/image';
import React, { useState } from 'react'
import ZoomOutMapIcon from '@mui/icons-material/ZoomOutMap';
import CloseIcon from '@mui/icons-material/Close';


const AboutDocid = () => {
  const [openModal, setOpenModal] = useState(false)
  const [selectedImage, setSelectedImage] = useState(null);

  const theme = useTheme();

  const handleOpenModal = (imageSrc) => {
    setSelectedImage(imageSrc);
    setOpenModal(true);
  };
  const handleCloseModal = () => {
    setOpenModal(false);
    setSelectedImage(null);
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
              Introducing the Digital Object Container Identifier
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
                Our Mission
              </Typography>
              <Typography variant="body1" sx={commonTypographyStyles}>
                Africa PID Alliances' mission and projects in disseminating multidisciplinary African research outputs are key in promoting infrastructure technology readiness and open research. By sharing the process of integrating persistent identifiers in academia, industry, and cultural heritage, the Africa PID Alliance initiative is inspired to promote a FAIR African technological and sustainable open research infrastructure.
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
                Using Open Infrastructure
              </Typography>
              <Typography variant="body1" sx={commonTypographyStyles}>
                The Africa PID Alliance is working to fulfil the continent's need for academic data infrastructures. Africa's diverse economic development is reflected in the continent's fast-growing requirement for strong scholarly data infrastructures. Many universities are unable to provide Digital Object Identifiers (DOIs) for all scholarly outputs, even though some can afford them for their research. Grey literature still contains a large amount of research conducted in Africa. The Africa PID Alliance recognises this gap and seeks to focus on protecting and advancing indigenous knowledge, cultural heritage, and patent digital object containers.
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
                Who Should Use
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
                  DOCID™ connects knowledge across sectors, ensuring that research, innovation, and heritage remain traceable and impactful.
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
                          Universities
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
                          DOCID™ empowers researchers, grants offices, libraries, and technology transfer teams to manage research outputs seamlessly, ensuring long-term visibility, compliance, and impact.
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
                          Museums
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
                          DOCID™ helps collections librarians, knowledge managers, and data specialists document and link museum collections with research, preserving cultural and scientific heritage for future generations.
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
                          Patent Registration Offices
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
                          DOCID™ supports patent filing officers and IP managers in tracking patents from application to commercialization, ensuring accessibility and compliance at every stage.
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
                          Research Projects
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
                          DOCID™ enables principal investigators, knowledge managers, and funding agencies to connect research outputs, maintain integrity, and ensure long-term accessibility.
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
                          Other PID Providers
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
                          DOCID™ complements existing PID systems by enhancing discoverability, interoperability, and traceability. We are working alongside global PID systems to create a more connected and structured research ecosystem.
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
                Use Case Scenarios
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
                          Click to expand
                        </Typography>
                        <ZoomOutMapIcon />
                      </Box>
                    </Box>
                    <Typography variant="h6" sx={{ mb: 1, color: theme.palette.primary.main }}>
                      Universities
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
                          Click to expand
                        </Typography>
                        <ZoomOutMapIcon />
                      </Box>
                    </Box>
                    <Typography variant="h6" sx={{ mb: 1, color: theme.palette.primary.main }}>
                      Museums
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
                          Click to expand
                        </Typography>
                        <ZoomOutMapIcon />
                      </Box>
                    </Box>
                    <Typography variant="h6" sx={{ mb: 1, color: theme.palette.primary.main }}>
                      Patent Registration Offices
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
                          Click to expand
                        </Typography>
                        <ZoomOutMapIcon />
                      </Box>
                    </Box>
                    <Typography variant="h6" sx={{ mb: 1, color: theme.palette.primary.main }}>
                      Research Projects
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
                Our Approach
              </Typography>
              <Typography variant="body1" sx={{ ...commonTypographyStyles, mb: 3 }}>
                Presenting Hybrid Digital Object Identification from the Africa PID Alliance: A hybrid digital object identification system is being pioneered by the Africa PID Alliance. This method connects DOIs produced by the DOI Foundation (prefix 10) with locally generated handles (prefix 20). A digital object identifier container will combine DOIs with locally generated handle IDs for patents, offering a thorough overview of the research process, the inventions that result in patents, and associated publications, papers, and media.
              </Typography>
              <Divider sx={{ my: 3, opacity: 0.6 }} />
              <Typography variant="body1" sx={commonTypographyStyles}>
                By combining scientific data and biocultural characteristics into a single digital object container, this novel multilinear data model also applies to indigenous knowledge. It successfully connects different kinds of digital items. Ceremonies, for example, incorporate various forms of cultural heritage, including dance, singing, textile art, and associated research, all of which require digital identification and preservation.
              </Typography>
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
                Collaboration
              </Typography>
              <Typography variant="body1" sx={commonTypographyStyles}>
                Working together with current registration agencies is crucial to improving the discovery and integration of the Africa PID Alliance's DOCiD (TM). The infrastructure team of the Africa PID Alliance, which includes its data centre at the Kenya Education Network, data scientists, and co-leaders from the Africa PID Alliance and founding partners, are collaborating closely to determine the most effective ways to accomplish this objective.
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
                Showcase
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
                    Click to expand
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