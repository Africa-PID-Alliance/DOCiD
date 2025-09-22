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
  Link,
  Stack,
  useTheme,
} from '@mui/material';

export default function ModerationProcess() {
  const { t } = useTranslation();
  const theme = useTheme();

  // Add smooth scroll behavior
  useEffect(() => {
    document.documentElement.style.scrollBehavior = 'smooth';
    return () => {
      document.documentElement.style.scrollBehavior = 'auto';
    };
  }, []);

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

  const SubSection = ({ title, children }) => (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" sx={{ mb: 2, color: 'text.secondary', fontWeight: 600 }}>
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
          Submission Moderation User Process
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
                    { id: 'purpose', title: '1. Purpose and Scope' },
                    { id: 'guidelines', title: '2. Submission Guidelines' },
                    { id: 'process', title: '3. Moderation Process' },
                    { id: 'special-cases', title: '4. Special Cases' },
                    { id: 'approval', title: '5. Approval and Rejection' },
                    { id: 'appeals', title: '6. Appeals' },
                    { id: 'improvement', title: '7. Continuous Improvement' },
                    { id: 'considerations', title: '8. Additional Considerations' },
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
            <div id="purpose">
              <Section title="1. Purpose and Scope of Moderation">
                <Typography variant="body1" paragraph>
                  The moderation system aims to:
                </Typography>
                <List sx={{ pl: 4, listStyleType: 'disc' }}>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText primary="Ensure that submitted digital objects are relevant, respectful, and meet the requirements set by the Africa PID Alliance." />
                  </ListItem>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText primary="Protect cultural heritage, intellectual property, and indigenous knowledge by enforcing rights and permissions." />
                  </ListItem>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText primary="Maintain the quality, integrity, and accuracy of the metadata and digital objects registered in the DOCiD system." />
                  </ListItem>
                </List>
              </Section>
            </div>

            <div id="guidelines">
              <Section title="2. Submission Guidelines">
                <Typography variant="body1" paragraph>
                  Users who submit digital objects for registration must adhere to the following guidelines:
                </Typography>
                
                <SubSection title="A. Eligible Content">
                  <List sx={{ pl: 4, listStyleType: 'disc' }}>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Digital Object Types"
                        secondary="Submissions should include objects such as patents, research outputs, cultural heritage items (e.g., artifacts, traditional knowledge), and other scholarly contributions."
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Cultural Sensitivity"
                        secondary="Submissions that pertain to indigenous knowledge, ceremonies, or community-specific data must respect community norms, and users must ensure they have the appropriate permissions."
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Originality and Attribution"
                        secondary="All submissions should be original or properly attributed to the rightful creators. Plagiarized content will be rejected."
                      />
                    </ListItem>
                  </List>
                </SubSection>

                <SubSection title="B. Metadata Requirements">
                  <List sx={{ pl: 4, listStyleType: 'disc' }}>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Complete and Accurate Metadata"
                        secondary="Submitters must provide complete metadata, including language, origin, creator(s), and other required fields (e.g., ROR, ORCID, Funder, DMP, and Project IDs)."
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Rights and Permissions"
                        secondary='Clearly state the rights and permissions (e.g., "Community Use Only") and include any supporting legal frameworks (e.g., customary law, TK Labels, Creative Commons licenses).'
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Ethical Considerations"
                        secondary="Users must avoid submitting sensitive or personal data without appropriate consent."
                      />
                    </ListItem>
                  </List>
                </SubSection>
              </Section>
            </div>

            <div id="process">
              <Section title="3. Moderation Process">
                <Typography variant="body1" paragraph>
                  Moderators are responsible for reviewing and approving submissions to the DOCiD registry. The moderation process includes the following steps:
                </Typography>

                <SubSection title="A. Initial Review">
                  <List sx={{ pl: 4, listStyleType: 'disc' }}>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Metadata Verification"
                        secondary="Verify that all required metadata fields are filled in accurately, including any identifiers (DOI, ROR, ORCID, etc.)."
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Content Suitability"
                        secondary="Ensure the submitted content aligns with the purpose of DOCiD, is culturally respectful, and adheres to submission guidelines."
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Cultural and Ethical Sensitivity"
                        secondary='If the submission contains indigenous knowledge, verify that appropriate community permissions have been provided, including rights like "Community Use Only."'
                      />
                    </ListItem>
                  </List>
                </SubSection>

                <SubSection title="B. Rights and Permissions Review">
                  <List sx={{ pl: 4, listStyleType: 'disc' }}>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Verification of Permissions"
                        secondary='Confirm that the rights and permissions (e.g., "Community Use Only") are accurate, backed by documentation, and comply with relevant laws and community norms.'
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Legal Frameworks"
                        secondary="Verify that the submission includes appropriate references to legal or customary frameworks (e.g., UNESCO conventions, TK Labels)."
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="User Contact"
                        secondary="If necessary, contact the submitter for clarifications on rights, permissions, or missing information."
                      />
                    </ListItem>
                  </List>
                </SubSection>

                <SubSection title="C. Quality Control">
                  <List sx={{ pl: 4, listStyleType: 'disc' }}>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Metadata Accuracy"
                        secondary="Ensure all metadata conforms to DOCiD's standards for accuracy and consistency."
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Content Relevance"
                        secondary="Reject submissions that do not contribute meaningfully to the DOCiD registry or are unrelated to scholarly, patent, or cultural heritage objects."
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Checks for Duplicates"
                        secondary="Ensure that the submission is not a duplicate of existing records unless additional context is provided (e.g., new related media or documents)."
                      />
                    </ListItem>
                  </List>
                </SubSection>
              </Section>
            </div>

            <div id="special-cases">
              <Section title="4. Guidelines for Special Cases">
                <SubSection title="A. Indigenous Knowledge and Cultural Heritage">
                  <List sx={{ pl: 4, listStyleType: 'disc' }}>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Community Consent"
                        secondary="Submissions involving indigenous knowledge or cultural heritage should include written or digital consent from the respective community. If the knowledge is protected by customary law, this must be indicated in the metadata."
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Sensitive Data"
                        secondary="In cases where sensitive cultural practices are shared, submissions should include clear documentation of who has access to the data (e.g., restricted to community members only)."
                      />
                    </ListItem>
                  </List>
                </SubSection>

                <SubSection title="B. Patents and Intellectual Property">
                  <List sx={{ pl: 4, listStyleType: 'disc' }}>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Verification of Patent Information"
                        secondary="Moderators should ensure that patent-related submissions include accurate data about inventors, assignees, application/grant dates, and classification codes."
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Compliance with International Guidelines"
                        secondary="Ensure that patent submissions comply with international intellectual property frameworks."
                      />
                    </ListItem>
                  </List>
                </SubSection>
              </Section>
            </div>

            <div id="approval">
              <Section title="5. Approval, Rejection, and Feedback">
                <SubSection title="A. Approval Process">
                  <List sx={{ pl: 4, listStyleType: 'disc' }}>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Final Review"
                        secondary="Once the metadata and content are verified, moderators approve the submission and notify the user."
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Notification of Approval"
                        secondary="The submitter will receive an automated notification confirming that their submission has been accepted, along with a DOCiD for their object."
                      />
                    </ListItem>
                  </List>
                </SubSection>

                <SubSection title="B. Rejection Process">
                  <Typography variant="body1" paragraph>
                    Submissions may be rejected for the following reasons:
                  </Typography>
                  <List sx={{ pl: 4, listStyleType: 'disc' }}>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText primary="Incomplete or inaccurate metadata." />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText primary="Missing or inadequate rights and permissions." />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText primary="Unethical or culturally insensitive content." />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText primary="Irrelevant or off-topic submissions." />
                    </ListItem>
                  </List>
                  <Typography variant="body1" paragraph sx={{ mt: 2 }}>
                    If a submission is rejected, the moderator must provide clear reasons and offer guidance on how the submitter can revise their content.
                  </Typography>
                </SubSection>

                <SubSection title="C. Resubmission Process">
                  <List sx={{ pl: 4, listStyleType: 'disc' }}>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Resubmission Guidelines"
                        secondary="Submitters whose objects are rejected may revise their content and metadata based on the moderator's feedback and resubmit."
                      />
                    </ListItem>
                    <ListItem sx={{ display: 'list-item', pl: 0 }}>
                      <ListItemText 
                        primary="Limit on Resubmissions"
                        secondary="Limit the number of times a submission can be resubmitted (e.g., a maximum of 3 attempts) to prevent spamming the system."
                      />
                    </ListItem>
                  </List>
                </SubSection>
              </Section>
            </div>

            <div id="appeals">
              <Section title="6. Appeals and Conflict Resolution">
                <List sx={{ pl: 4, listStyleType: 'disc' }}>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText 
                      primary="Appeals Process"
                      secondary="Submitters who believe their submission was wrongly rejected can appeal by contacting the DOCiD moderation team with a justification."
                    />
                  </ListItem>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText 
                      primary="Moderation Review"
                      secondary="An internal review will be conducted, and a final decision made by senior moderators or the Africa PID Alliance governance team."
                    />
                  </ListItem>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText 
                      primary="Conflict Resolution"
                      secondary="In cases of disputes involving rights or permissions, moderators should defer to customary laws or community governance bodies for a final decision."
                    />
                  </ListItem>
                </List>
              </Section>
            </div>

            <div id="improvement">
              <Section title="7. Continuous Improvement">
                <Typography variant="body1" paragraph>
                  Moderators should engage in continuous improvement by:
                </Typography>
                <List sx={{ pl: 4, listStyleType: 'disc' }}>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText 
                      primary="Periodic Audits"
                      secondary="Conduct regular audits of the submissions to ensure adherence to DOCiD policies."
                    />
                  </ListItem>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText 
                      primary="Training and Development"
                      secondary="Provide training for moderators on cultural sensitivity, intellectual property, and the legal frameworks governing indigenous knowledge."
                    />
                  </ListItem>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText 
                      primary="Feedback Loop"
                      secondary="Implement a feedback system where submitters and users can provide input on the moderation process to improve transparency and fairness."
                    />
                  </ListItem>
                </List>
              </Section>
            </div>

            <div id="considerations">
              <Section title="8. Additional Considerations for Moderators">
                <List sx={{ pl: 4, listStyleType: 'disc' }}>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText 
                      primary="Impartiality and Fairness"
                      secondary="Moderators must act without bias, ensuring fair treatment of all submissions, regardless of the origin of the submitter or type of digital object."
                    />
                  </ListItem>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText 
                      primary="Respect for Diversity"
                      secondary="Moderators should respect the diversity of cultures and research disciplines represented in DOCiD submissions."
                    />
                  </ListItem>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText 
                      primary="Confidentiality"
                      secondary="Protect the confidentiality of sensitive submissions, especially those involving unpublished research or community-protected knowledge."
                    />
                  </ListItem>
                </List>
              </Section>
            </div>

            <div id="references">
              <Section title="References for Best Practices">
                <List sx={{ pl: 4, listStyleType: 'disc' }}>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText 
                      primary={
                        <Link
                          href="https://ich.unesco.org/en/convention"
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
                          UNESCO Convention for the Safeguarding of Intangible Cultural Heritage (2003)
                        </Link>
                      }
                      secondary="Guidelines on preserving and respecting intangible cultural heritage."
                    />
                  </ListItem>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText 
                      primary={
                        <Link
                          href="https://localcontexts.org/labels/traditional-knowledge-labels/"
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
                          Local Contexts Traditional Knowledge (TK) Labels
                        </Link>
                      }
                      secondary="Best practices for managing and attributing indigenous knowledge."
                    />
                  </ListItem>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText 
                      primary={
                        <Link
                          href="https://creativecommons.org/licenses/"
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
                          Creative Commons Licensing
                        </Link>
                      }
                      secondary="For establishing clear rights and permissions in digital environments."
                    />
                  </ListItem>
                  <ListItem sx={{ display: 'list-item', pl: 0 }}>
                    <ListItemText 
                      primary={
                        <Link
                          href="https://www.wipo.int/tk/en/"
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
                          WIPO Guidelines on Traditional Knowledge and Intellectual Property
                        </Link>
                      }
                      secondary="Principles for respecting traditional knowledge within intellectual property frameworks."
                    />
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