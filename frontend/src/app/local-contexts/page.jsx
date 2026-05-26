"use client";

import React, { useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Link as MuiLink,
  Stack,
  useTheme,
  Divider,
  Chip,
} from '@mui/material';

/**
 * /local-contexts — public documentation page for the DOCiD <> Local Contexts
 * Hub integration. This URL is the "Documentation link" required on our
 * Integration Partner account profile on https://localcontextshub.org for
 * "manual" mode integrations to surface to Hub users.
 *
 * Audience: LC Hub users, Indigenous community members, certification reviewers
 * (Local Contexts team), and DOCiD researchers wanting to know how attaching
 * a project to their record works.
 *
 * Keep the copy verbatim-aligned with the LC display contract: icons and
 * label/notice text rendered on DOCiD pages are unmodified, with the Hub as
 * the authoritative source.
 */
export default function LocalContextsDocsPage() {
  const theme = useTheme();

  useEffect(() => {
    document.documentElement.style.scrollBehavior = 'smooth';
    return () => { document.documentElement.style.scrollBehavior = 'auto'; };
  }, []);

  const Section = ({ title, children }) => (
    <Box sx={{ mb: 5 }}>
      <Typography
        variant="h5"
        sx={{
          mb: 2.5,
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
            borderRadius: 1,
          },
        }}
      >
        {title}
      </Typography>
      <Box sx={{ pt: 1 }}>{children}</Box>
    </Box>
  );

  return (
    <Box component="main" sx={{ bgcolor: theme.palette.background.default, minHeight: '100vh', py: { xs: 3, md: 6 } }}>
      <Container maxWidth="md">
        <Paper elevation={0} sx={{ p: { xs: 2, sm: 3, md: 5 }, borderRadius: 2 }}>

          {/* Header */}
          <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
            <Typography variant="h4" fontWeight={700}>Local Contexts</Typography>
            <Chip label="Integration Partner" size="small" color="primary" />
          </Stack>
          <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>
            How DOCiD™ integrates with the Local Contexts Hub to display TK Labels, BC Labels, and Notices on African research records.
          </Typography>

          <Divider sx={{ mb: 4 }} />

          {/* What is Local Contexts */}
          <Section title="What is Local Contexts?">
            <Typography paragraph>
              <MuiLink href="https://localcontexts.org/" target="_blank" rel="noopener noreferrer">Local Contexts</MuiLink>
              {' '}is a global initiative that supports Indigenous communities with tools to express cultural authority and protocols for the digital reuse of their materials, data, and knowledge. The two flagship tool families are <strong>TK (Traditional Knowledge) Labels</strong> and <strong>BC (Biocultural) Labels</strong>, plus a set of standardised <strong>Notices</strong> that communicate provenance and protocol obligations.
            </Typography>
            <Typography paragraph>
              The <MuiLink href="https://localcontextshub.org/" target="_blank" rel="noopener noreferrer">Local Contexts Hub</MuiLink> is the canonical platform where communities, institutions, and researchers create projects and attach the Labels and Notices that apply to specific materials.
            </Typography>
          </Section>

          {/* What we display */}
          <Section title="What DOCiD displays">
            <Typography paragraph>
              When a Local Contexts project is attached to a DOCiD record, the public detail page renders a panel titled <em>Local Contexts Labels and Notices</em> containing each Label and Notice exactly as the Hub publishes it:
            </Typography>
            <List dense sx={{ pl: 1 }}>
              <ListItem><ListItemText primary="The official Label / Notice icon served directly from the Hub (unmodified)" /></ListItem>
              <ListItem><ListItemText primary="The Label or Notice name (verbatim)" /></ListItem>
              <ListItem><ListItemText primary="The full default text (verbatim)" /></ListItem>
              <ListItem><ListItemText primary="Translations when the Hub provides them, selectable via per-card language chips" /></ListItem>
              <ListItem><ListItemText primary="Contributing institution(s) and a hyperlink to the project page on the Hub" /></ListItem>
              <ListItem><ListItemText primary="A per-item “View on Local Contexts Hub” link for provenance" /></ListItem>
            </List>
            <Typography paragraph sx={{ mt: 1 }}>
              DOCiD never modifies, abbreviates, or paraphrases Label or Notice content. All authoritative content remains under the control of the originating community and the Hub.
            </Typography>
          </Section>

          {/* How attachment works */}
          <Section title="How a researcher attaches a project">
            <Typography paragraph>
              The Local Contexts panel is part of the <strong>Assign DOCiD™ wizard</strong> at <code>/assign-docid</code>. It appears automatically when the chosen <strong>Resource Type</strong> is <em>Indigenous Knowledge</em> or <em>Cultural Heritage</em>, and is hidden for resource types that are out of scope.
            </Typography>
            <Typography paragraph>From the Local Contexts panel a researcher can:</Typography>
            <List dense sx={{ pl: 1 }}>
              <ListItem><ListItemText primary="Type the project title (debounced autocomplete searches the Hub live)" /></ListItem>
              <ListItem><ListItemText primary="Paste a canonical Project UUID copied from a Hub project URL (the picker resolves it directly)" /></ListItem>
              <ListItem><ListItemText primary="Attach multiple projects — each renders as its own panel on the public page" /></ListItem>
              <ListItem><ListItemText primary="Remove an attachment before saving, or via the equivalent /edit-docid flow afterwards" /></ListItem>
            </List>
            <Typography paragraph sx={{ mt: 1 }}>
              On submission, DOCiD records the attachment (project UUID + per-item identifiers + the cached snapshot at attach time) so the public detail page can render even if the Hub is temporarily unreachable.
            </Typography>
          </Section>

          {/* Integration mode */}
          <Section title="Integration mode">
            <Typography paragraph>
              DOCiD uses the <strong>manual integration</strong> mode on the Local Contexts Hub. All Hub calls are server-side, authenticated with our Integration Partner API key on the <code>x-api-key</code> header. The key never reaches a browser or a third party.
            </Typography>
            <Typography paragraph>
              Hub users do not authenticate to DOCiD through the Hub — researchers identify projects by title or UUID on the DOCiD side and the attachment is persisted in DOCiD&apos;s database.
            </Typography>
          </Section>

          {/* Data lifecycle */}
          <Section title="Data lifecycle and refresh">
            <Typography paragraph>
              DOCiD caches a minimal snapshot of each attached Label / Notice (icon URL, item name, default text, language) so the public page renders reliably. The cache is refreshed on every page render from the Hub when reachable; otherwise the cached values render with a small <em>cached data</em> indicator.
            </Typography>
            <Typography paragraph>
              If a project is updated, retired, or rescinded on the Hub, the next DOCiD page render reflects that change. The Hub remains the authoritative source.
            </Typography>
          </Section>

          {/* Display compliance */}
          <Section title="Compliance with Local Contexts display requirements">
            <List dense sx={{ pl: 1 }}>
              <ListItem><ListItemText primary="Icons rendered unmodified (served from Hub URLs, no CSS overrides applied)" /></ListItem>
              <ListItem><ListItemText primary="Label / Notice name and default text rendered prominently and verbatim" /></ListItem>
              <ListItem><ListItemText primary="Translations available on demand, never silently substituted" /></ListItem>
              <ListItem><ListItemText primary="Each project links back to its Hub project page; each item links to its Hub source page" /></ListItem>
              <ListItem><ListItemText primary="Attachment is initiated by the DOCiD record owner; cannot be added by third parties" /></ListItem>
            </List>
          </Section>

          {/* Endpoint reference */}
          <Section title="Public endpoints used by this integration">
            <Typography paragraph>
              All Hub calls go through DOCiD&apos;s backend. The frontend never calls the Hub directly.
            </Typography>
            <List dense sx={{ pl: 1 }}>
              <ListItem><ListItemText primary="GET /projects/?title=… — title autocomplete (rate-limited, cached 5 minutes)" /></ListItem>
              <ListItem><ListItemText primary="GET /projects/<uuid>/ — single-project resolve (used by paste-a-UUID and by display)" /></ListItem>
              <ListItem><ListItemText primary="GET /projects/multi/<uuid>,<uuid>,…/ — batch hydration for records with multiple attached projects" /></ListItem>
            </List>
          </Section>

          {/* Contact */}
          <Section title="Questions, takedown requests, or attribution issues">
            <Typography paragraph>
              For project-content concerns, contact the originating community or the Hub directly via <MuiLink href="https://localcontextshub.org/" target="_blank" rel="noopener noreferrer">localcontextshub.org</MuiLink>.
            </Typography>
            <Typography paragraph>
              For DOCiD-side integration questions (attach flow, display issues on a specific DOCiD record), email <MuiLink href="mailto:info@africapidalliance.org">info@africapidalliance.org</MuiLink>.
            </Typography>
          </Section>

          <Divider sx={{ my: 3 }} />
          <Typography variant="caption" color="text.secondary">
            DOCiD™ is operated by the <MuiLink href="https://africapidalliance.org/" target="_blank" rel="noopener noreferrer">Africa PID Alliance</MuiLink>, in partnership with the <MuiLink href="https://tcc-africa.org/" target="_blank" rel="noopener noreferrer">Training Centre in Communication</MuiLink>. Africa PID Alliance is a certified Local Contexts Integration Partner.
          </Typography>
        </Paper>
      </Container>
    </Box>
  );
}
