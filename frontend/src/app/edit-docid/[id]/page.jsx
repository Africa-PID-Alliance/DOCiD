"use client";

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useSelector } from 'react-redux';
import axios from 'axios';
import {
  Box, Container, Paper, Typography, TextField, Button,
  Stepper, Step, StepLabel, Alert, CircularProgress, Stack, useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Save as SaveIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import CustomStepIcon from '../../assign-docid/components/CustomStepIcon';

// Forked forms (same UI as assign-docid)
import CreatorsForm from '../components/CreatorsForm';
import OrganizationsForm from '../components/OrganizationsForm';
import FundersForm from '../components/FundersForm';
import ProjectForm from '../components/ProjectForm';
import PublicationsForm from '../components/PublicationsForm';
import DocumentsForm from '../components/DocumentsForm';

const EDIT_BASE = (publicationId) => `/api/publications/${publicationId}/edit`;

// ---------- shape mappers ----------

function dbToFormCreator(c) {
  const isOrcid = (c.identifier_type || '').toLowerCase() === 'orcid' && c.identifier;
  return {
    id: c.id,
    familyName: c.family_name || '',
    givenName: c.given_name || '',
    affiliation: c.affiliation || '',
    role: c.role || '',
    role_name: '',
    orcidId: isOrcid ? c.identifier.replace(/^https?:\/\/orcid\.org\//, '') : '',
    otherName: '',
    _raw: c,
  };
}

function formToDbCreator(c) {
  const orcid = (c.orcidId || '').trim();
  const identifier = orcid
    ? (orcid.startsWith('http') ? orcid : `https://orcid.org/${orcid}`)
    : '';
  return {
    family_name: c.familyName || '',
    given_name: c.givenName || '',
    identifier,
    identifier_type: orcid ? 'orcid' : '',
    affiliation: c.affiliation || null,
    role_id: c.role,
  };
}

function dbToFormOrganization(o) {
  return {
    id: o.id,
    name: o.name || '',
    otherName: o.other_name || '',
    type: o.type || '',
    country: o.country || '',
    department: '',
    role: '',
    rorId: o.identifier || '',
    city: '',
    website: '',
    rrid: o.rrid || '',
    _raw: o,
  };
}

function formToDbOrganization(o) {
  return {
    name: o.name || '',
    type: o.type || 'Research',
    other_name: o.otherName || null,
    country: o.country || null,
    identifier: o.rorId || null,
    identifier_type: o.rorId ? 'ror' : null,
    rrid: o.rrid || null,
  };
}

function dbToFormFunder(f) {
  return {
    id: f.id,
    name: f.name || '',
    otherName: f.other_name || '',
    type: f.type || '',
    country: f.country || '',
    rorId: f.identifier || '',
    _raw: f,
  };
}

function formToDbFunder(f) {
  return {
    name: f.name || '',
    type: f.type || 'Grantor',
    funder_type_id: 1,
    other_name: f.otherName || null,
    country: f.country || null,
    identifier: f.rorId || null,
    identifier_type: f.rorId ? 'ror' : null,
  };
}

function dbToFormProject(p) {
  return {
    id: p.id,
    title: p.title || '',
    description: p.description || '',
    raidId: p.raid_id || p.identifier || '',
    _raw: p,
  };
}

function formToDbProject(p) {
  return {
    title: p.title || '',
    description: p.description || '',
    raid_id: p.raidId || null,
    identifier: p.raidId || null,
    identifier_type: p.raidId ? 'raid' : null,
  };
}

// Files & Documents map to PublicationsForm/DocumentsForm's "uploaded file + metadata" shape.
// Existing rows from the DB are flagged with `existing: true` so the form does not try to
// re-upload them. New rows added by the form have no `id` and carry a real File blob.
function dbToFormFile(f) {
  return {
    id: f.id,
    existing: true,
    name: f.file_name || f.title || '',
    size: 0,
    type: f.file_type || 'application/octet-stream',
    url: f.file_url || '',
    lastModified: 0,
    file: null,
    publicationType: f.publication_type_id != null ? String(f.publication_type_id) : '',
    metadata: {
      title: f.title || '',
      description: f.description || '',
      identifier: 1,                 // APA Handle iD (only option shown in edit mode)
      identifierType: 1,
      generated_identifier: f.generated_identifier || '',
    },
  };
}

function dbToFormDocument(d) {
  return {
    id: d.id,
    existing: true,
    name: d.title || '',
    size: 0,
    type: 'application/octet-stream',
    url: d.file_url || '',
    lastModified: 0,
    file: null,
    publicationType: d.publication_type != null
      ? String(d.publication_type)
      : (d.publication_type_id != null ? String(d.publication_type_id) : ''),
    metadata: {
      title: d.title || '',
      description: d.description || '',
      identifier: 1,
      identifierType: 1,
      generated_identifier: d.generated_identifier || '',
    },
  };
}

function mostCommonValue(arr) {
  if (!arr || arr.length === 0) return null;
  const counts = {};
  for (const v of arr) counts[v] = (counts[v] || 0) + 1;
  return Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0];
}

function hasChanged(a, b, keys) {
  return keys.some((k) => (a[k] ?? null) !== (b[k] ?? null));
}

// ---------- page ----------

export default function EditDocidPage() {
  const params = useParams();
  const router = useRouter();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const publicationId = params?.id;
  const { user, isAuthenticated } = useSelector((state) => state.auth || {});
  const currentUserId = user?.id || user?.user_id || null;

  const [publicationData, setPublicationData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [activeStep, setActiveStep] = useState(0);
  const [feedbackMessage, setFeedbackMessage] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  // Top-level details
  const [documentTitle, setDocumentTitle] = useState('');
  const [documentDescription, setDocumentDescription] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');

  // Per-entity state + originals
  const [creators, setCreators] = useState([]);
  const originalCreators = useRef([]);
  const [organizations, setOrganizations] = useState([]);
  const originalOrganizations = useRef([]);
  const [funders, setFunders] = useState([]);
  const originalFunders = useRef([]);
  const [projects, setProjects] = useState([]);
  const originalProjects = useRef([]);
  const [publicationsData, setPublicationsData] = useState({ publicationType: '', files: [] });
  const originalPublicationFiles = useRef([]);
  const [documentsData, setDocumentsData] = useState({ documentType: '', files: [] });
  const originalPublicationDocuments = useRef([]);

  const loadPublication = useCallback(async () => {
    if (!publicationId || !currentUserId) return;
    setIsLoading(true);
    try {
      const response = await axios.get(
        `/api/publications/get-publication-for-edit/${publicationId}`
      );
      const d = response.data;
      setPublicationData(d);
      setDocumentTitle(d.document_title || '');
      setDocumentDescription(d.document_description || '');
      setAvatarUrl(d.avatar || '');

      const mappedCreators = (d.publication_creators || []).map(dbToFormCreator);
      setCreators(mappedCreators);
      originalCreators.current = mappedCreators;

      const mappedOrgs = (d.publication_organizations || []).map(dbToFormOrganization);
      setOrganizations(mappedOrgs);
      originalOrganizations.current = mappedOrgs;

      const mappedFunders = (d.publication_funders || []).map(dbToFormFunder);
      setFunders(mappedFunders);
      originalFunders.current = mappedFunders;

      const mappedProjects = (d.publication_projects || []).map(dbToFormProject);
      setProjects(mappedProjects);
      originalProjects.current = mappedProjects;

      // Files & documents — map DB rows to PublicationsForm/DocumentsForm shape
      const mappedFiles = (d.publications_files || []).map(dbToFormFile);
      // Seed publicationType from the most common existing publication_type_id (or blank)
      const mostCommonFileType = mostCommonValue(mappedFiles.map(f => f.publicationType).filter(Boolean));
      setPublicationsData({ publicationType: mostCommonFileType || '', files: mappedFiles });
      originalPublicationFiles.current = mappedFiles;
      const mappedDocs = (d.publication_documents || []).map(dbToFormDocument);
      const mostCommonDocType = mostCommonValue(mappedDocs.map(dd => dd.publicationType).filter(Boolean));
      setDocumentsData({ documentType: mostCommonDocType || '', files: mappedDocs });
      originalPublicationDocuments.current = mappedDocs;

      setFetchError(null);
    } catch (err) {
      setFetchError(err.response?.data?.message || 'Failed to load publication');
    } finally {
      setIsLoading(false);
    }
  }, [publicationId, currentUserId]);

  useEffect(() => { loadPublication(); }, [loadPublication]);

  // ---- Top-level save ----
  const handleSaveTopLevel = async () => {
    setIsSaving(true);
    try {
      const formData = new FormData();
      // user_id intentionally not sent — server derives identity from JWT.
      formData.append('documentTitle', documentTitle);
      formData.append('documentDescription', documentDescription);
      formData.append('avatar', avatarUrl);
      await axios.put(`/api/publications/update-publication/${publicationId}`, formData);
      setFeedbackMessage({ type: 'success', text: 'Details saved' });
      loadPublication();
    } catch (err) {
      setFeedbackMessage({ type: 'error', text: err.response?.data?.message || 'Save failed' });
    } finally {
      setIsSaving(false);
    }
  };

  // ---- Generic diff-sync ----
  async function syncEntity({ endpoint, current, originalRef, toDb, compareKeys, label }) {
    const original = originalRef.current;
    let added = 0, updated = 0, deleted = 0, errors = 0;

    // DELETEs first
    for (const o of original) {
      if (o.id && !current.find((c) => c.id === o.id)) {
        try {
          await axios.delete(`${EDIT_BASE(publicationId)}/${endpoint}/${o.id}`);
          deleted++;
        } catch (err) { errors++; console.error(`Delete ${label} ${o.id}:`, err); }
      }
    }
    // POSTs for new items (no id)
    for (const c of current) {
      if (!c.id) {
        try {
          await axios.post(`${EDIT_BASE(publicationId)}/${endpoint}`, toDb(c));
          added++;
        } catch (err) { errors++; console.error(`Add ${label}:`, err); }
      }
    }
    // PUTs for changed
    for (const c of current) {
      if (!c.id) continue;
      const o = original.find((x) => x.id === c.id);
      if (o && hasChanged(toDb(o), toDb(c), compareKeys)) {
        try {
          await axios.put(`${EDIT_BASE(publicationId)}/${endpoint}/${c.id}`, toDb(c));
          updated++;
        } catch (err) { errors++; console.error(`Update ${label} ${c.id}:`, err); }
      }
    }
    return { added, updated, deleted, errors };
  }

  const saveStep = async (stepName) => {
    setIsSaving(true);
    try {
      let result;
      if (stepName === 'creators') {
        result = await syncEntity({
          endpoint: 'creators',
          current: creators,
          originalRef: originalCreators,
          toDb: formToDbCreator,
          compareKeys: ['family_name', 'given_name', 'identifier', 'affiliation', 'role_id'],
          label: 'creator',
        });
      } else if (stepName === 'organizations') {
        result = await syncEntity({
          endpoint: 'organizations',
          current: organizations,
          originalRef: originalOrganizations,
          toDb: formToDbOrganization,
          compareKeys: ['name', 'type', 'other_name', 'country', 'identifier', 'rrid'],
          label: 'organization',
        });
      } else if (stepName === 'funders') {
        result = await syncEntity({
          endpoint: 'funders',
          current: funders,
          originalRef: originalFunders,
          toDb: formToDbFunder,
          compareKeys: ['name', 'type', 'other_name', 'country', 'identifier'],
          label: 'funder',
        });
      } else if (stepName === 'projects') {
        result = await syncEntity({
          endpoint: 'projects',
          current: projects,
          originalRef: originalProjects,
          toDb: formToDbProject,
          compareKeys: ['title', 'description', 'raid_id', 'identifier'],
          label: 'project',
        });
      }
      if (result) {
        const { added, updated, deleted, errors } = result;
        if (added + updated + deleted + errors === 0) {
          setFeedbackMessage({ type: 'info', text: 'No changes to save' });
        } else {
          setFeedbackMessage({
            type: errors ? 'warning' : 'success',
            text: `Saved: ${added} added, ${updated} updated, ${deleted} deleted${errors ? `, ${errors} errors` : ''}`,
          });
        }
        // Only reload on full success — on partial failure, keep failed items in state so user can retry.
        if (errors === 0) {
          await loadPublication();
        }
      }
    } finally {
      setIsSaving(false);
    }
  };

  // ---- Files & Documents: upload / diff-update / delete on "Save" ----
  async function savePublicationFiles() {
    setIsSaving(true);
    let uploaded = 0, updated = 0, deleted = 0, errors = 0;
    const files = publicationsData.files;
    const defaultType = publicationsData.publicationType || '1';
    try {
      // DELETE removed files
      for (const o of originalPublicationFiles.current) {
        if (!files.find((f) => f.id === o.id)) {
          try {
            await axios.delete(`${EDIT_BASE(publicationId)}/files/${o.id}`);
            deleted++;
          } catch (err) { errors++; }
        }
      }
      // PUT metadata changes on existing rows
      for (const f of files) {
        if (!f.id || !f.existing) continue;
        const orig = originalPublicationFiles.current.find((x) => x.id === f.id);
        if (!orig) continue;
        const meta = f.metadata || {};
        const origMeta = orig.metadata || {};
        const newType = f.publicationType || defaultType;
        const origType = orig.publicationType || '';
        const changed =
          (meta.title || '') !== (origMeta.title || '') ||
          (meta.description || '') !== (origMeta.description || '') ||
          String(newType) !== String(origType);
        if (!changed) continue;
        try {
          await axios.put(`${EDIT_BASE(publicationId)}/files/${f.id}`, {
            title: meta.title || '',
            description: meta.description || '',
            publication_type_id: newType,
          });
          updated++;
        } catch (err) { errors++; console.error('File update:', err); }
      }
      // POST new items. PublicationsForm shape: { file: Blob, metadata: {title, description, ...}, videoUrl? }
      for (const f of files) {
        if (f.id || f.existing) continue;
        const meta = f.metadata || {};
        try {
          const fd = new FormData();
          fd.append('title', meta.title || f.name || f.file?.name || 'Untitled');
          fd.append('description', meta.description || '');
          fd.append('publication_type_id', f.publicationType || defaultType);
          if (f.videoUrl) {
            fd.append('video_url', f.videoUrl);
          } else if (f.file instanceof File || f.file instanceof Blob) {
            fd.append('file', f.file);
          } else {
            continue;
          }
          await axios.post(`${EDIT_BASE(publicationId)}/files`, fd);
          uploaded++;
        } catch (err) { errors++; console.error('File upload:', err); }
      }
      setFeedbackMessage({
        type: errors ? 'warning' : 'success',
        text: `Files: ${uploaded} uploaded, ${updated} updated, ${deleted} deleted${errors ? `, ${errors} errors` : ''}`,
      });
      if (errors === 0) {
        await loadPublication();
      }
    } finally {
      setIsSaving(false);
    }
  }

  async function savePublicationDocuments() {
    setIsSaving(true);
    let uploaded = 0, updated = 0, deleted = 0, errors = 0;
    const docs = documentsData.files;
    const defaultType = documentsData.documentType || '1';
    try {
      for (const o of originalPublicationDocuments.current) {
        if (!docs.find((d) => d.id === o.id)) {
          try {
            await axios.delete(`${EDIT_BASE(publicationId)}/documents/${o.id}`);
            deleted++;
          } catch (err) { errors++; }
        }
      }
      // PUT metadata changes on existing documents
      for (const d of docs) {
        if (!d.id || !d.existing) continue;
        const orig = originalPublicationDocuments.current.find((x) => x.id === d.id);
        if (!orig) continue;
        const meta = d.metadata || {};
        const origMeta = orig.metadata || {};
        const newType = d.publicationType || defaultType;
        const origType = orig.publicationType || '';
        const changed =
          (meta.title || '') !== (origMeta.title || '') ||
          (meta.description || '') !== (origMeta.description || '') ||
          String(newType) !== String(origType);
        if (!changed) continue;
        try {
          await axios.put(`${EDIT_BASE(publicationId)}/documents/${d.id}`, {
            title: meta.title || '',
            description: meta.description || '',
            publication_type_id: newType,
          });
          updated++;
        } catch (err) { errors++; console.error('Document update:', err); }
      }
      for (const d of docs) {
        if (d.id || d.existing) continue;
        const meta = d.metadata || {};
        try {
          const fd = new FormData();
          fd.append('title', meta.title || d.name || d.file?.name || 'Untitled');
          fd.append('description', meta.description || '');
          fd.append('publication_type_id', d.publicationType || defaultType);
          fd.append('identifier_type_id', meta.identifierType || '1');
          if (d.videoUrl) {
            fd.append('video_url', d.videoUrl);
          } else if (d.file instanceof File || d.file instanceof Blob) {
            fd.append('file', d.file);
          } else {
            continue;
          }
          await axios.post(`${EDIT_BASE(publicationId)}/documents`, fd);
          uploaded++;
        } catch (err) { errors++; console.error('Document upload:', err); }
      }
      setFeedbackMessage({
        type: errors ? 'warning' : 'success',
        text: `Documents: ${uploaded} uploaded, ${updated} updated, ${deleted} deleted${errors ? `, ${errors} errors` : ''}`,
      });
      if (errors === 0) {
        await loadPublication();
      }
    } finally {
      setIsSaving(false);
    }
  }

  // ---- Render ----
  const pageWrap = (children) => (
    <Box sx={{
      width: '100%',
      py: { xs: 2, sm: 3, md: 4 },
      bgcolor: theme.palette.background.content || theme.palette.background.default,
      minHeight: '100vh',
    }}>
      <Container maxWidth={false} sx={{ px: { xs: 2, sm: 3, md: 4 } }}>
        {children}
      </Container>
    </Box>
  );

  if (!isAuthenticated) {
    return pageWrap(
      <Paper elevation={2} sx={{ p: 4, borderRadius: 2 }}>
        <Alert severity="warning">You must be signed in to edit.</Alert>
      </Paper>
    );
  }
  if (isLoading) {
    return pageWrap(
      <Paper elevation={2} sx={{ p: 6, borderRadius: 2, textAlign: 'center' }}>
        <CircularProgress />
      </Paper>
    );
  }
  if (fetchError) {
    return pageWrap(
      <Paper elevation={2} sx={{ p: 4, borderRadius: 2 }}>
        <Alert severity="error">{fetchError}</Alert>
        <Button sx={{ mt: 2 }} startIcon={<ArrowBackIcon />} onClick={() => router.back()}>Back</Button>
      </Paper>
    );
  }
  if (!publicationData) return null;

  const stepLabels = [
    `DOCiD™`,
    `Publications (${publicationsData.files.length})`,
    `Documents (${documentsData.files.length})`,
    `Creators (${creators.length})`,
    `Organizations (${organizations.length})`,
    `Funders (${funders.length})`,
    `Projects (${projects.length})`,
  ];

  return pageWrap(
    <>
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => router.push(`/docid/${publicationData.document_docid}`)}
        sx={{ mb: 2 }}
      >
        Back to DOCiD
      </Button>

      <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 }, mb: 3, borderRadius: 2 }}>
        <Typography variant="h5" fontWeight={600} gutterBottom>Edit DOCiD</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          DOCiD: <strong>{publicationData.document_docid}</strong> (handle will not change)
        </Typography>
        {feedbackMessage && (
          <Alert severity={feedbackMessage.type} onClose={() => setFeedbackMessage(null)} sx={{ mt: 1 }}>
            {feedbackMessage.text}
          </Alert>
        )}
      </Paper>

      <Paper elevation={2} sx={{ mb: 3, borderRadius: 2, p: 2 }}>
        <Stepper
          activeStep={activeStep}
          alternativeLabel={!isMobile}
          orientation={isMobile ? 'vertical' : 'horizontal'}
        >
          {stepLabels.map((label, idx) => (
            <Step key={label} completed={false} sx={{ cursor: 'pointer' }} onClick={() => setActiveStep(idx)}>
              <StepLabel StepIconComponent={CustomStepIcon}>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      <Stack direction="row" spacing={2} justifyContent="center" mb={3}>
        <Button disabled={activeStep === 0} onClick={() => setActiveStep((p) => Math.max(0, p - 1))}>Back</Button>
        <Button variant="contained" disabled={activeStep === 6} onClick={() => setActiveStep((p) => Math.min(6, p + 1))}>Next</Button>
      </Stack>

      {/* Step 0 — Details */}
      {activeStep === 0 && (
        <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 }, borderRadius: 2 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>DOCiD™ Details</Typography>
          <Stack spacing={2}>
            <TextField label="Title" fullWidth value={documentTitle} onChange={(e) => setDocumentTitle(e.target.value)} />
            <TextField label="Description (HTML allowed)" fullWidth multiline minRows={6} value={documentDescription} onChange={(e) => setDocumentDescription(e.target.value)} />
            <TextField label="Avatar URL" fullWidth value={avatarUrl} onChange={(e) => setAvatarUrl(e.target.value)} />
            <Box>
              <Button variant="contained" startIcon={<SaveIcon />} onClick={handleSaveTopLevel} disabled={isSaving}>
                {isSaving ? 'Saving...' : 'Save Details'}
              </Button>
            </Box>
          </Stack>
        </Paper>
      )}

      {/* Step 1 — Publications (files) */}
      {activeStep === 1 && (
        <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 }, borderRadius: 2 }}>
          <PublicationsForm
            formData={publicationsData}
            updateFormData={(next) => setPublicationsData({
              publicationType: next.publicationType ?? publicationsData.publicationType ?? '',
              files: next.files || [],
            })}
          />
          <Box mt={2}>
            <Button variant="contained" startIcon={<SaveIcon />} onClick={savePublicationFiles} disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save Publications'}
            </Button>
          </Box>
        </Paper>
      )}

      {/* Step 2 — Documents */}
      {activeStep === 2 && (
        <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 }, borderRadius: 2 }}>
          <DocumentsForm
            formData={documentsData}
            updateFormData={(next) => setDocumentsData({
              documentType: next.documentType ?? documentsData.documentType ?? '',
              files: next.files || [],
            })}
          />
          <Box mt={2}>
            <Button variant="contained" startIcon={<SaveIcon />} onClick={savePublicationDocuments} disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save Documents'}
            </Button>
          </Box>
        </Paper>
      )}

      {/* Step 3 — Creators */}
      {activeStep === 3 && (
        <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 }, borderRadius: 2 }}>
          <CreatorsForm
            formData={{ creators }}
            updateFormData={(next) => setCreators(next.creators || [])}
          />
          <Box mt={2}>
            <Button variant="contained" startIcon={<SaveIcon />} onClick={() => saveStep('creators')} disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save Creators'}
            </Button>
          </Box>
        </Paper>
      )}

      {/* Step 4 — Organizations */}
      {activeStep === 4 && (
        <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 }, borderRadius: 2 }}>
          <OrganizationsForm
            formData={{ organizations }}
            updateFormData={(next) => setOrganizations(next.organizations || [])}
            type="ror"
            label="ROR"
          />
          <Box mt={2}>
            <Button variant="contained" startIcon={<SaveIcon />} onClick={() => saveStep('organizations')} disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save Organizations'}
            </Button>
          </Box>
        </Paper>
      )}

      {/* Step 5 — Funders */}
      {activeStep === 5 && (
        <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 }, borderRadius: 2 }}>
          <FundersForm
            formData={{ funders }}
            updateFormData={(next) => setFunders(next.funders || [])}
          />
          <Box mt={2}>
            <Button variant="contained" startIcon={<SaveIcon />} onClick={() => saveStep('funders')} disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save Funders'}
            </Button>
          </Box>
        </Paper>
      )}

      {/* Step 6 — Projects */}
      {activeStep === 6 && (
        <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 }, borderRadius: 2 }}>
          <ProjectForm
            formData={{ projects }}
            updateFormData={(next) => setProjects(next.projects || [])}
          />
          <Box mt={2}>
            <Button variant="contained" startIcon={<SaveIcon />} onClick={() => saveStep('projects')} disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save Projects'}
            </Button>
          </Box>
        </Paper>
      )}
    </>
  );
}
