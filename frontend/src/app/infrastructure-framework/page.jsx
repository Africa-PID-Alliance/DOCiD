"use client";

import React, { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  List,
  ListItem,
  ListItemText,
  Divider,
  Card,
  CardContent,
  useTheme,
  Link,
  Stack,
} from '@mui/material';
import CodeBlock from '@/components/CodeBlock';

export default function InfrastructureFramework() {
  const { t } = useTranslation();
  const theme = useTheme();

  // Add smooth scroll behavior
  useEffect(() => {
    document.documentElement.style.scrollBehavior = 'smooth';
    return () => {
      document.documentElement.style.scrollBehavior = 'auto';
    };
  }, []);

  const pythonCode = `class DOI:
    def __init__(self, identifier, description):
        self.identifier = identifier
        self.description = description

class DOCiD:
    def __init__(self):
        self.dois = []

    def add_doi(self, identifier, description):
        doi = DOI(identifier, description)
        self.dois.append(doi)

    def get_doi_description(self, identifier):
        for doi in self.dois:
            if doi.identifier == identifier:
                return doi.description
        return None

# Example usage:
docid_container = DOCiD()
docid_container.add_doi("id1", "Description of ID1")
docid_container.add_doi("id2", "Description of ID2")

# Retrieving DOI description
doi_description = docid_container.get_doi_description("id2")
if doi_description:
    print(f"Description of ID2: {doi_description}")
else:
    print("DOI not found.")`;

  const Section = ({ title, children }) => (
    <Box sx={{ mb: 6 }}>
      <Typography
        variant="h5"
        sx={{
          mb: 3,
          fontWeight: 600,
          color: theme.palette.primary.main,
          position: 'relative',
          '&:after': {
            content: '""',
            position: 'absolute',
            bottom: -8,
            left: 0,
            width: 60,
            height: 3,
            backgroundColor: theme.palette.primary.main,
            borderRadius: 1
          }
        }}
      >
        {title}
      </Typography>
      {children}
    </Box>
  );

  return (
    <Box sx={{ py: 8, bgcolor: 'background.default' }}>
      <Container maxWidth="lg">
        <Typography
          variant="h3"
          sx={{
            mb: 6,
            fontWeight: 700,
            textAlign: 'center',
            color: theme.palette.primary.main
          }}
        >
          Africa PID Alliance Registration Agency Infrastructure Roadmap
        </Typography>

        <Grid container spacing={4}>
          {/* Sticky Navigation Sidebar */}
          <Grid item xs={12} md={3}>
            <Box
              sx={{
                position: 'sticky',
                top: 24,
                maxHeight: 'calc(100vh - 48px)',
                overflowY: 'auto',
                scrollbarWidth: 'thin',
                '&::-webkit-scrollbar': {
                  width: '6px',
                },
                '&::-webkit-scrollbar-track': {
                  background: 'transparent',
                },
                '&::-webkit-scrollbar-thumb': {
                  background: theme.palette.primary.main,
                  borderRadius: '3px',
                },
              }}
            >
              <Paper 
                sx={{ 
                  p: 2,
                  bgcolor: 'background.paper',
                  boxShadow: 2,
                }}
              >
                <Typography variant="h6" gutterBottom sx={{ borderBottom: `2px solid ${theme.palette.primary.main}`, pb: 1 }}>
                  Quick Navigation
                </Typography>
                <Stack spacing={1}>
                  {[
                    { id: 'resolution', title: '1. Resolution Framework' },
                    { id: 'infrastructure', title: '2. Infrastructure and Partnerships' },
                    { id: 'platform', title: '3. DOCiD Platform Features' },
                    { id: 'api-design', title: '4. API Design' },
                    { id: 'api-registry', title: '5. API Registry Platform' },
                    { id: 'ui-services', title: '6. User Interface & Services' },
                    { id: 'preparation', title: '7. Preparation and Launch' },
                    { id: 'technical', title: '8. Technical Draft' },
                    { id: 'code-example', title: '9. Python Code Example' },
                    { id: 'search', title: '10. Search and Retrieval' },
                    { id: 'references', title: 'References' }
                  ].map((section) => (
                    <Link
                      key={section.id}
                      href={`#${section.id}`}
                      sx={{
                        color: theme.palette.text.primary,
                        textDecoration: 'none',
                        display: 'block',
                        p: 1,
                        borderRadius: 1,
                        fontSize: '0.9rem',
                        transition: 'all 0.2s ease',
                        '&:hover': {
                          bgcolor: 'rgba(25, 118, 210, 0.08)',
                          color: theme.palette.primary.main,
                          pl: 2
                        }
                      }}
                    >
                      {section.title}
                    </Link>
                  ))}
                </Stack>
              </Paper>
            </Box>
          </Grid>

          {/* Main Content */}
          <Grid item xs={12} md={9}>
            <div id="resolution">
              <Section title="1. Resolution Framework">
                <Typography variant="h6" sx={{ mb: 2, color: 'text.secondary' }}>
                  The Africa PID Alliance (APA)'s DOCiD:
                </Typography>
                <Typography variant="body1" paragraph>
                  As Africa's data infrastructure needs grow rapidly and research output expands, there is a pressing need for Persistent Identifiers (PIDs) tailored to the African context. Currently, many African universities can afford DOIs only for selected scholarly outputs, leaving a large volume of gray literature unregistered. Additionally, the APA RA aims to specialize in indigenous knowledge, cultural heritage, and patent digital object containers—areas underrepresented in current PID services.
                </Typography>
                <Typography variant="body1" paragraph>
                  To address these challenges, the APA RA proposes a hybrid digital object identification system that combines locally created handles (prefix 20.) with DOIs from international registration agencies (prefix 10.) through collaboration with DOI Foundation, Crossref, and DataCite. This system is designed to capture the unique characteristics of African research and cultural heritage.
                </Typography>
                
                <Card sx={{ mb: 3, mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Patent Case Study:</Typography>
                    <Typography variant="body2">
                      A Digital Object Identifier (DOI) container for patents will consolidate DOIs and locally created handles to capture the entire innovation lifecycle—from research and development to the patent grant—and include associated works, documents, and media. This comprehensive digital object container enhances visibility and collaboration across borders.
                    </Typography>
                  </CardContent>
                </Card>

                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Indigenous Knowledge and Cultural Heritage:</Typography>
                    <Typography variant="body2">
                      The same multilinear data model will be used for indigenous knowledge, combining biocultural attributes with scientific data into one digital object container. This model is adaptable to complex cultural objects like ceremonies, which encompass multiple forms of heritage (textiles, music, dance, research studies). These will be identified using both local handles and DOIs, with the goal of creating a unified digital object container.
                    </Typography>
                  </CardContent>
                </Card>
              </Section>
            </div>

            <div id="infrastructure">
              <Section title="2. Infrastructure and Partnerships">
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <Paper sx={{ p: 3, mb: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        Collaboration with Crossref, DataCite, DONA Foundation and DOI Foundation:
                      </Typography>
                      <Typography variant="body1">
                        The Africa PID Alliance seeks strong collaboration with Crossref, DataCite, DONA Foundation and DOI Foundation to enhance the discoverability of APA RA-registered DOIs and identifiers, particularly those related to indigenous knowledge and patents. The integration of these globally recognized PID systems will help African research and cultural heritage to be widely disseminated and recognized.
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12}>
                    <Paper sx={{ p: 3, mb: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        Collaboration with Asian DOI Registration Agencies:
                      </Typography>
                      <Typography variant="body1">
                        To broaden our scope, we are in talks with DOI registration agencies in Asia to explore synergies in supporting innovation and indigenous knowledge. This collaboration aims to bridge geographical and cultural gaps, ensuring that African research connects globally.
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12}>
                    <Paper sx={{ p: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        CORDRA Federation Model:
                      </Typography>
                      <Typography variant="body1">
                        The APA RA will implement a CORDRA-based federated architecture for managing digital objects, ensuring scalability and interoperability across various research domains. (
                        <Link 
                          href="https://www.researchgate.net/figure/Layered-CORDRA-Model_fig2_228629455"
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{ 
                            color: theme.palette.primary.main,
                            textDecoration: 'none',
                            '&:hover': {
                              textDecoration: 'underline'
                            }
                          }}
                        >
                          Layered CORDRA Model
                        </Link>
                        )
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>
              </Section>
            </div>

            <div id="platform">
              <Section title="3. DOCiD Platform Features and Technical Specifications">
                <Typography variant="body1" paragraph>
                  The DOCiD platform is the cornerstone of the Africa PID Alliance, designed to manage digital object identifiers for African research and cultural heritage.
                </Typography>
                
                <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
                  Key Features of DOCiD:
                </Typography>

                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <List>
                      <ListItem>
                        <ListItemText 
                          primary={
                            <Typography variant="body1">
                              <strong>1. Faceted Navigation:</strong>
                            </Typography>
                          }
                          secondary="Enables refined searches by author, subject, and date."
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary={
                            <Typography variant="body1">
                              <strong>2. Browsable Categories or Taxonomies:</strong>
                            </Typography>
                          }
                          secondary="Users can navigate through predefined categories based on research or cultural classifications."
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary={
                            <Typography variant="body1">
                              <strong>3. Thumbnails and Previews:</strong>
                            </Typography>
                          }
                          secondary="Provides quick visual representations of digital objects."
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary={
                            <Typography variant="body1">
                              <strong>4. Linking and Cross-Referencing:</strong>
                            </Typography>
                          }
                          secondary="Facilitates seamless navigation between related digital objects."
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary={
                            <Typography variant="body1">
                              <strong>5. Persistent Identifiers (DOIs, Handles):</strong>
                            </Typography>
                          }
                          secondary="Visible, clickable DOIs and local handles for immediate access to digital objects."
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary={
                            <Typography variant="body1">
                              <strong>6. Access Controls:</strong>
                            </Typography>
                          }
                          secondary="Permissions-based access to digital objects."
                        />
                      </ListItem>
                    </List>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <List>
                      <ListItem>
                        <ListItemText 
                          primary={
                            <Typography variant="body1">
                              <strong>7. APIs for Integration:</strong>
                            </Typography>
                          }
                          secondary="APIs to allow integration with other platforms and research systems."
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary={
                            <Typography variant="body1">
                              <strong>8. User Authentication and SSO:</strong>
                            </Typography>
                          }
                          secondary="Secure access with options for single sign-on (SSO)."
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary={
                            <Typography variant="body1">
                              <strong>9. Usage Analytics:</strong>
                            </Typography>
                          }
                          secondary="Tracks user behavior and performance metrics."
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary={
                            <Typography variant="body1">
                              <strong>10. Personalization:</strong>
                            </Typography>
                          }
                          secondary="Users can save searches, set preferences, and receive personalized recommendations."
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary={
                            <Typography variant="body1">
                              <strong>11. Mobile Responsiveness:</strong>
                            </Typography>
                          }
                          secondary="Optimized for mobile devices."
                        />
                      </ListItem>
                    </List>
                  </Grid>
                </Grid>
              </Section>
            </div>

            <div id="api-design">
              <Section title="4. API Design for Patents and Indigenous Knowledge">
                <Box sx={{ mb: 4 }}>
                  <Typography variant="h6" gutterBottom>Infrastructure Requirements:</Typography>
                  <List sx={{ 
                    listStyleType: 'disc',
                    pl: 4,
                    '& .MuiListItem-root': {
                      display: 'list-item',
                      pl: 0,
                      py: 0.5
                    }
                  }}>
                    <ListItem>
                      <ListItemText primary="Repository: Built on the Invenio platform." />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="CORDRA Hosting: Scalable infrastructure for digital object management." />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Integrations with Crossref and DataCite: Ensuring that APA RA objects are fully discoverable and compliant with global standards." />
                    </ListItem>
                  </List>
                </Box>

                <Box sx={{ mb: 4 }}>
                  <Typography variant="h6" gutterBottom>Data Models:</Typography>
                  <List sx={{ 
                    listStyleType: 'disc',
                    pl: 4,
                    '& .MuiListItem-root': {
                      display: 'list-item',
                      pl: 0,
                      py: 0.5
                    }
                  }}>
                    <ListItem>
                      <ListItemText 
                        primary={
                          <Typography variant="body1">
                            <strong>Multilinear Data Models</strong> for both patents and indigenous knowledge to accommodate complex metadata and high volumes. (
                            <Link 
                              href="https://docs.google.com/document/d/119wPyCYGWifT-zc1sXajJk0k20GRFt7X2nZFpU1mjis/edit?tab=t.0#heading=h.tt8izr6bnq12"
                              target="_blank"
                              rel="noopener noreferrer"
                              sx={{ 
                                color: theme.palette.primary.main,
                                textDecoration: 'none',
                                '&:hover': {
                                  textDecoration: 'underline'
                                }
                              }}
                            >
                              Documentation
                            </Link>
                            )
                          </Typography>
                        }
                      />
                    </ListItem>
                  </List>

                  <Grid container spacing={4}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
                        Proposed Indigenous Knowledge Schema:
                      </Typography>
                      <List sx={{ 
                        listStyleType: 'disc',
                        pl: 4,
                        '& .MuiListItem-root': {
                          display: 'list-item',
                          pl: 0,
                          py: 0.5
                        }
                      }}>
                        {[
                          'Language',
                          'Origin',
                          'Creator',
                          'Context',
                          'Rights and Permissions'
                        ].map((item, index) => (
                          <ListItem key={index}>
                            <ListItemText primary={item} />
                          </ListItem>
                        ))}
                      </List>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
                        Proposed Patent Metadata Schema:
                      </Typography>
                      <List sx={{ 
                        listStyleType: 'disc',
                        pl: 4,
                        '& .MuiListItem-root': {
                          display: 'list-item',
                          pl: 0,
                          py: 0.5
                        }
                      }}>
                        {[
                          'Title',
                          'Inventor(s)',
                          'Assignee(s)',
                          'Application and Grant Dates',
                          'Classification Codes',
                          'Country',
                          'Rights and Permissions'
                        ].map((item, index) => (
                          <ListItem key={index}>
                            <ListItemText primary={item} />
                          </ListItem>
                        ))}
                      </List>
                    </Grid>
                  </Grid>
                </Box>
              </Section>
            </div>

            <div id="api-registry">
              <Section title="5. API Registry Platform and Documentation Process">
                <Box sx={{ mb: 4 }}>
                  <Typography variant="h6" gutterBottom>API Registry Features:</Typography>
                  <List sx={{ 
                    listStyleType: 'disc',
                    pl: 4,
                    '& .MuiListItem-root': {
                      display: 'list-item',
                      pl: 0,
                      py: 0.5
                    }
                  }}>
                    <ListItem>
                      <ListItemText 
                        primary={<>
                          <strong>Identifiers as a Service (iDaaS):</strong>
                          <Typography component="span" sx={{ display: 'block', ml: 2 }}>
                            Managing digital objects mapped to containers for structured storage and discovery.
                          </Typography>
                        </>}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary={<>
                          <strong>Multilinear Data Model:</strong>
                          <Typography component="span" sx={{ display: 'block', ml: 2 }}>
                            Supporting diverse identifier types for patents and cultural heritage objects.
                          </Typography>
                        </>}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary={<>
                          <strong>API Registration and Documentation Workflows:</strong>
                          <Typography component="span" sx={{ display: 'block', ml: 2 }}>
                            End-to-end workflows for registering and managing digital object identifiers.
                          </Typography>
                        </>}
                      />
                    </ListItem>
                  </List>
                </Box>

                <Box sx={{ mb: 4 }}>
                  <Typography variant="h6" gutterBottom>API Documentation Templates:</Typography>
                  <List sx={{ 
                    listStyleType: 'disc',
                    pl: 4,
                    '& .MuiListItem-root': {
                      display: 'list-item',
                      pl: 0,
                      py: 0.5
                    }
                  }}>
                    <ListItem>
                      <ListItemText primary="Templates for clear, concise API documentation, including validation and approval workflows." />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary={<>
                          <Link
                            href="https://docs.google.com/document/d/119wPyCYGWifT-zc1sXajJk0k20GRFt7X2nZFpU1mjis/edit?tab=t.0#heading=h.tt8izr6bnq12"
                            target="_blank"
                            rel="noopener noreferrer"
                            sx={{ 
                              color: theme.palette.primary.main,
                              textDecoration: 'none',
                              '&:hover': {
                                textDecoration: 'underline'
                              }
                            }}
                          >
                            DOCiD HyperGraph Data Model
                          </Link>
                          : Provides templates for documenting complex digital objects, including linked data and metadata validation rules.
                        </>}
                      />
                    </ListItem>
                  </List>
                </Box>

                <Box sx={{ mb: 4 }}>
                  <Typography variant="h6" gutterBottom>API Search and Discovery:</Typography>
                  <List sx={{ 
                    listStyleType: 'disc',
                    pl: 4,
                    '& .MuiListItem-root': {
                      display: 'list-item',
                      pl: 0,
                      py: 0.5
                    }
                  }}>
                    <ListItem>
                      <ListItemText primary="Advanced Search Features for APIs based on keywords, categories, and filters, improving discoverability." />
                    </ListItem>
                  </List>
                </Box>

                <Box>
                  <Typography variant="h6" gutterBottom>Analytics and Monitoring:</Typography>
                  <List sx={{ 
                    listStyleType: 'disc',
                    pl: 4,
                    '& .MuiListItem-root': {
                      display: 'list-item',
                      pl: 0,
                      py: 0.5
                    }
                  }}>
                    <ListItem>
                      <ListItemText primary="Dashboards for tracking API usage and performance, providing actionable insights for both providers and consumers." />
                    </ListItem>
                  </List>
                </Box>
              </Section>
            </div>

            <div id="ui-services">
              <Section title="6. User Interface & Services">
                <List sx={{ 
                  listStyleType: 'disc',
                  pl: 4,
                  mb: 3,
                  '& .MuiListItem-root': {
                    display: 'list-item',
                    pl: 0,
                    py: 1
                  }
                }}>
                  <ListItem>
                    <ListItemText 
                      primary={<>
                        <strong>User Interface (UI):</strong>
                        <Typography component="span" sx={{ display: 'block', ml: 2 }}>
                          The DOCiD UI will be accessible in multiple African languages and offer user-friendly tools to search, create, and manage multilinear digital object containers linking existing and new identifiers.
                        </Typography>
                      </>}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary={<>
                        <strong>Mobile and Web Application:</strong>
                        <Typography component="span" sx={{ display: 'block', ml: 2 }}>
                          A mobile application will allow users to scan DOIs and identify their associated containers. If no container exists, users can create one and configure it through a simple UI.
                        </Typography>
                      </>}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary={<>
                        <strong>Docking Feature:</strong>
                        <Typography component="span" sx={{ display: 'block', ml: 2 }}>
                          The platform will support an easy "dock" functionality to attach existing identifiers to new containers, generating a persistent DOCiD for future use.
                        </Typography>
                      </>}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary={
                        <Link
                          href="https://docs.google.com/document/d/1Pfs-pZ6lXH1OV6lNDt8qOriehWrbDh21yb9SfsQbhHo/edit?tab=t.0#heading=h.nnwvkt7jpsj3"
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{ 
                            color: theme.palette.primary.main,
                            textDecoration: 'none',
                            '&:hover': {
                              textDecoration: 'underline'
                            }
                          }}
                        >
                          Submission moderation user process
                        </Link>
                      }
                    />
                  </ListItem>
                </List>
              </Section>
            </div>

            <div id="preparation">
              <Section title="7. Preparation and Launch">
                <Typography variant="h6" gutterBottom>Steps for Launch:</Typography>
                <List sx={{ 
                  listStyleType: 'disc',
                  pl: 4,
                  '& .MuiListItem-root': {
                    display: 'list-item',
                    pl: 0,
                    py: 0.5
                  }
                }}>
                  <ListItem>
                    <ListItemText 
                      primary={<>
                        <strong>Policy Development:</strong>
                        <Typography component="span" sx={{ display: 'block', ml: 2 }}>
                          Establish metadata, data quality, and management policies (ongoing).
                        </Typography>
                      </>}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary={<>
                        <strong>Tool Development:</strong>
                        <Typography component="span" sx={{ display: 'block', ml: 2 }}>
                          Create user-friendly tools for DOI registration, metadata management, and tracking (testing CORDRA from CNRI).
                        </Typography>
                      </>}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary={<>
                        <strong>Testing:</strong>
                        <Typography component="span" sx={{ display: 'block', ml: 2 }}>
                          Conduct tests with a pilot group of users to refine the system before full deployment.
                        </Typography>
                      </>}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary={<>
                        <strong>Launch:</strong>
                        <Typography component="span" sx={{ display: 'block', ml: 2 }}>
                          Promote the registry platform to potential users, highlighting its benefits for managing digital objects and data.
                        </Typography>
                      </>}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary={<>
                        <strong>Ongoing Support:</strong>
                        <Typography component="span" sx={{ display: 'block', ml: 2 }}>
                          Provide continuous updates, maintenance, and support to ensure the platform's sustainability and usability.
                        </Typography>
                      </>}
                    />
                  </ListItem>
                </List>
              </Section>
            </div>

            <div id="technical">
              <Section title="8. Technical Draft and Integrations">
                <Grid container spacing={4}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>Priority Integrations:</Typography>
                    <List sx={{ 
                      listStyleType: 'disc',
                      pl: 4,
                      '& .MuiListItem-root': {
                        display: 'list-item',
                        pl: 0,
                        py: 0.5
                      }
                    }}>
                      {[
                        'ORCID',
                        'ROR',
                        'RAID',
                        'Crossref',
                        'DataCite',
                        'TK Labels',
                        'Local Handle IDs'
                      ].map((item, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={item} />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>Possible Integrations:</Typography>
                    <List sx={{ 
                      listStyleType: 'disc',
                      pl: 4,
                      '& .MuiListItem-root': {
                        display: 'list-item',
                        pl: 0,
                        py: 0.5
                      }
                    }}>
                      {[
                        'Papermill API',
                        'Pypi',
                        'Dimensions',
                        'Nature',
                        'Figshare',
                        'OpenAlex'
                      ].map((item, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={item} />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                </Grid>
              </Section>
            </div>

            <div id="code-example">
              <Section title="9. Python Code Example">
                <Paper sx={{ p: 3, bgcolor: 'grey.900' }}>
                  <CodeBlock code={pythonCode} language="python" />
                </Paper>
              </Section>
            </div>

            <div id="search">
              <Section title="10. Search and Retrieval">
                <Typography variant="body1">
                  DOCiD integrates search engines like Elasticsearch and Apache Solr for fast, accurate retrieval of digital objects based on complex query filters such as date ranges, categories, and object types.
                </Typography>
              </Section>
            </div>

            {/* References section */}
            <div id="references">
              <Section title="References">
                <List sx={{ pl: 2 }}>
                  <ListItem sx={{ display: 'list-item', listStyleType: 'decimal' }}>
                    <Typography variant="body1">
                      <Link 
                        href="https://www.researchgate.net/figure/Layered-CORDRA-Model_fig2_228629455"
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{ 
                          color: theme.palette.primary.main,
                          textDecoration: 'none',
                          '&:hover': {
                            textDecoration: 'underline'
                          }
                        }}
                      >
                        CORDRA Federation Model
                      </Link>
                    </Typography>
                  </ListItem>
                  <ListItem sx={{ display: 'list-item', listStyleType: 'decimal' }}>
                    <Typography variant="body1" sx={{ 
                      '& .wip': { 
                        color: theme.palette.warning.main,
                        fontStyle: 'italic',
                        mx: 1
                      }
                    }}>
                      APA GitHub Repository:
                      <span className="wip">(Work in progress)</span>
                      <Link 
                        href="https://github.com/Africa-PID-Alliance"
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{ 
                          color: theme.palette.primary.main,
                          textDecoration: 'none',
                          ml: 1,
                          '&:hover': {
                            textDecoration: 'underline'
                          }
                        }}
                      >
                        Africa PID Alliance GitHub
                      </Link>
                    </Typography>
                  </ListItem>
                </List>
              </Section>
            </div>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
} 