"use client";

import React, { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useSelector } from 'react-redux';
import axios from 'axios';
import {
  Box, Container, Paper, Typography, TextField, Button,
  Stepper, Step, StepLabel, Alert, CircularProgress, Stack, useTheme,
  useMediaQuery,
  Dialog, DialogTitle, DialogContent, DialogActions,
} from '@mui/material';
import {
  Save as SaveIcon,
  ArrowBack as ArrowBackIcon,
  AutoAwesome as AutoAwesomeIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import CustomStepIcon from '../../assign-docid/components/CustomStepIcon';
import RichTextEditor from '@/components/RichTextEditor';

// Forked forms (same UI as assign-docid)
import CreatorsForm from '../components/CreatorsForm';
import OrganizationsForm from '../components/OrganizationsForm';
import FundersForm from '../components/FundersForm';
import ProjectForm from '../components/ProjectForm';
import PublicationsForm from '../components/PublicationsForm';
import DocumentsForm from '../components/DocumentsForm';
// Shared LC step wrapper (defined under assign-docid; same component is used here).
import LocalContextsForm from '../../assign-docid/components/LocalContextsForm';

// Resource type IDs where the Local Contexts step is shown (Indigenous Knowledge, Cultural Heritage).
const LC_RESOURCE_TYPE_IDS = new Set([1, 3]);

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

/**
 * Deep-clone an array of plain-data entity snapshots for use as a baseline.
 * Forms mutate nested `metadata` in place; sharing references between state
 * and originalRef would make the diff-loop's `orig !== current` comparison
 * see equal values and silently skip the PUT. Structured-clone handles
 * nested metadata/blobs safely.
 */
function snapshotCopy(items) {
  if (!items || !Array.isArray(items)) return [];
  try {
    return structuredClone(items);
  } catch {
    // Fallback for older runtimes. File/Blob refs are dropped but baselines
    // never hold live blobs (we null out `file` on persisted rows), so safe.
    return JSON.parse(JSON.stringify(items));
  }
}

/**
 * Rebuild a baseline snapshot after a partial save so retry replays only the
 * failed work. Mirrors the inline logic in syncEntity() for reuse in the file
 * and document save paths where deletes/PUTs/POSTs need independent tracking.
 */
function rebuildBaseline({ original, working, deletedIds, putById }) {
  const next = [];
  for (const o of original) {
    if (deletedIds.has(o.id)) continue;          // successfully removed
    if (putById.has(o.id)) continue;              // replaced below
    next.push(o);                                  // untouched (failed or unchanged)
  }
  for (const [, c] of putById) next.push(c);
  const originalIds = new Set(original.map((x) => x.id).filter(Boolean));
  for (const c of working) {
    if (c.id && !originalIds.has(c.id) && !putById.has(c.id)) {
      next.push(c);                                // newly-POSTed and persisted
    }
  }
  return snapshotCopy(next);
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

  const [isRehydrated, setIsRehydrated] = useState(false);
  const [publicationData, setPublicationData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [activeStep, setActiveStep] = useState(0);
  const [feedbackMessage, setFeedbackMessage] = useState(null);
  const [openAlexBusy, setOpenAlexBusy] = useState(false);
  const [openAlexResult, setOpenAlexResult] = useState(null); // { status, review_status, conflicts, enrichment, provenance, match_method, openalex_id, reason }
  const [openAlexDialogOpen, setOpenAlexDialogOpen] = useState(false);
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
  // True only after loadPublication() has successfully populated the file/doc
  // baseline refs. Until then the diff-on-save flow would treat every absent
  // row as a deletion target, so we gate the Save button on this. See
  // /Users/ekariz/.claude/plans/next-we-need-to-mutable-matsumoto.md for the
  // 2026-06-25 data-loss incident that motivates this gate.
  const [publicationsLoaded, setPublicationsLoaded] = useState(false);
  // Bumped on every successful loadPublication(). Child forms watch this to
  // know when to re-seed their local state from the fresh DB shape (e.g.
  // newly-assigned ids after upload). Without this, the previous "sync on
  // every formData change" effect created the data-loss bug; with this, the
  // child form only re-syncs at controlled moments.
  const [loadGeneration, setLoadGeneration] = useState(0);

  // Local Contexts attachments (project-level, M2M). `_legacy` synthetic entry
  // groups NULL-project attachment rows so we never lose-track-of legacy data.
  const [localContexts, setLocalContexts] = useState([]);
  const originalLocalContexts = useRef([]);
  // pendingDetach holds the snapshot when the user changes resource type away
  // from IK/Cultural Heritage; restored if they switch back before saving.
  const pendingLcDetach = useRef([]);
  const [resourceTypeId, setResourceTypeId] = useState(null);
  const [lcDialogOpen, setLcDialogOpen] = useState(false);
  const [lcDialogTargetType, setLcDialogTargetType] = useState(null);

  const showLocalContextsStep = useMemo(
    () => LC_RESOURCE_TYPE_IDS.has(Number(resourceTypeId)),
    [resourceTypeId]
  );

  const loadPublication = useCallback(async () => {
    if (!publicationId || !currentUserId) return;
    setIsLoading(true);
    // Force gate closed during reload so a slow refetch can't be saved against
    // a stale (or partially-mutated) state. Reopened only on success below.
    setPublicationsLoaded(false);
    try {
      const response = await axios.get(
        `/api/publications/get-publication-for-edit/${publicationId}`
      );
      const d = response.data;
      setPublicationData(d);
      setDocumentTitle(d.document_title || '');
      setDocumentDescription(d.document_description || '');
      setAvatarUrl(d.avatar || '');

      // Deep-clone the baseline so forms' in-place mutations on state
      // don't poison the originalRef comparison. Codex v3 H1.
      const mappedCreators = (d.publication_creators || []).map(dbToFormCreator);
      setCreators(mappedCreators);
      originalCreators.current = snapshotCopy(mappedCreators);

      const mappedOrgs = (d.publication_organizations || []).map(dbToFormOrganization);
      setOrganizations(mappedOrgs);
      originalOrganizations.current = snapshotCopy(mappedOrgs);

      const mappedFunders = (d.publication_funders || []).map(dbToFormFunder);
      setFunders(mappedFunders);
      originalFunders.current = snapshotCopy(mappedFunders);

      const mappedProjects = (d.publication_projects || []).map(dbToFormProject);
      setProjects(mappedProjects);
      originalProjects.current = snapshotCopy(mappedProjects);

      // Files & documents — map DB rows to PublicationsForm/DocumentsForm shape
      const mappedFiles = (d.publications_files || []).map(dbToFormFile);
      // Seed publicationType from the most common existing publication_type_id (or blank)
      const mostCommonFileType = mostCommonValue(mappedFiles.map(f => f.publicationType).filter(Boolean));
      setPublicationsData({ publicationType: mostCommonFileType || '', files: mappedFiles });
      originalPublicationFiles.current = snapshotCopy(mappedFiles);
      const mappedDocs = (d.publication_documents || []).map(dbToFormDocument);
      const mostCommonDocType = mostCommonValue(mappedDocs.map(dd => dd.publicationType).filter(Boolean));
      setDocumentsData({ documentType: mostCommonDocType || '', files: mappedDocs });
      originalPublicationDocuments.current = snapshotCopy(mappedDocs);

      setResourceTypeId(d.resource_type_id ?? null);

      // Local Contexts attachments — reuse /projects-display which already
      // returns the {projects, legacy} envelope shape we need.
      try {
        const lcResp = await axios.get(`/api/localcontexts/publications/${publicationId}/projects-display`);
        const projectsArr = Array.isArray(lcResp.data?.projects) ? lcResp.data.projects : [];
        const legacyArr = Array.isArray(lcResp.data?.legacy) ? lcResp.data.legacy : [];
        const grouped = projectsArr.map((p) => ({
          external_id: p.project_external_id,
          title: p.title,
          project_type: p.project_type || 'Other',
          project_page: p.project_page,
          contributing_institutions: p.contributing_institutions || [],
        }));
        if (legacyArr.length > 0) {
          grouped.push({
            external_id: '_legacy',
            title: `${legacyArr.length} legacy item-level attachment(s)`,
            project_type: 'Legacy',
            project_page: null,
            contributing_institutions: [],
            _legacy: true,
          });
        }
        setLocalContexts(grouped);
        originalLocalContexts.current = snapshotCopy(grouped);
        pendingLcDetach.current = [];
      } catch (lcErr) {
        // Non-fatal; LC step will appear with empty state if applicable.
        console.warn('Failed to load Local Contexts attachments:', lcErr);
        setLocalContexts([]);
        originalLocalContexts.current = [];
      }

      setFetchError(null);
      // Only flip the gate open AFTER the baseline refs above were populated
      // by a successful response. If we got here, the diff-on-save flow is
      // safe to run against a real baseline.
      setPublicationsLoaded(true);
      // Bump the load generation so child forms (PublicationsForm /
      // DocumentsForm) know to re-seed their local list from the fresh
      // server shape (e.g. newly-minted ids after an upload).
      setLoadGeneration((g) => g + 1);
    } catch (err) {
      setFetchError(err.response?.data?.message || 'Failed to load publication');
      // Leave publicationsLoaded=false so Save stays disabled until reload.
    } finally {
      setIsLoading(false);
    }
  }, [publicationId, currentUserId]);

  useEffect(() => {
    const persistedAuth = typeof window !== 'undefined' ? localStorage.getItem('persist:root') : null;
    if (persistedAuth) {
      setIsRehydrated(true);
    } else {
      setTimeout(() => setIsRehydrated(true), 100);
    }
  }, []);

  useEffect(() => {
    if (isRehydrated && !isAuthenticated) {
      router.push('/login');
    }
  }, [isRehydrated, isAuthenticated, router]);

  useEffect(() => { loadPublication(); }, [loadPublication]);

  // ---- OpenAlex enrichment (Phase 2/3) ----
  // A "real" DOI is a CrossRef/DataCite-style 10.xxxx/yyyy identifier — NOT a
  // DOCiD/Handle prefix (e.g. 20.500.14351/...). OpenAlex only indexes real DOIs,
  // so we use this check to decide whether to offer the title-search fallback.
  const hasRealDoi = (() => {
    const raw = (publicationData?.doi || '').trim();
    if (!raw) return false;
    const bare = raw.replace(/^https?:\/\/(dx\.)?doi\.org\//i, '');
    return /^10\./.test(bare);
  })();

  const runOpenAlexEnrichment = async ({ titleFallback = false } = {}) => {
    setOpenAlexBusy(true);
    try {
      const query = titleFallback ? '?title_fallback=1' : '';
      const response = await axios.post(
        `/api/publications/${publicationId}/enrich/openalex${query}`
      );
      setOpenAlexResult(response.data);
      setOpenAlexDialogOpen(true);
      if (response.data?.review_status === 'accepted') {
        setFeedbackMessage({ type: 'success', text: 'OpenAlex enrichment accepted and applied.' });
        loadPublication();
      } else if (response.data?.review_status === 'pending_review') {
        setFeedbackMessage({ type: 'info', text: 'OpenAlex returned a match that needs your review.' });
      } else if (response.data?.status === 'not_found') {
        const hint = !hasRealDoi
          ? ' This publication has no CrossRef DOI (only a DOCiD/Handle), so OpenAlex cannot match it by DOI. Try "Try title search" instead.'
          : '';
        setFeedbackMessage({ type: 'warning', text: `No OpenAlex match found.${hint}` });
      } else if (response.data?.status === 'skipped') {
        setFeedbackMessage({ type: 'warning', text: response.data?.message || 'OpenAlex enrichment skipped.' });
      }
    } catch (err) {
      const status = err.response?.status;
      const message = err.response?.data?.message || err.response?.data?.reason || 'OpenAlex enrichment failed.';
      // 400 no_valid_doi -- offer title fallback automatically next click; just surface a hint here.
      if (status === 400 && err.response?.data?.reason === 'no_valid_doi') {
        setFeedbackMessage({ type: 'info', text: 'No DOI on this publication. Use "Try title search" to attempt title-based match.' });
      } else {
        setFeedbackMessage({ type: 'error', text: message });
      }
    } finally {
      setOpenAlexBusy(false);
    }
  };

  const acceptOpenAlexCandidate = async () => {
    setOpenAlexBusy(true);
    try {
      const response = await axios.post(
        `/api/publications/${publicationId}/enrich/openalex/accept`
      );
      setFeedbackMessage({ type: 'success', text: 'OpenAlex candidate accepted.' });
      setOpenAlexResult((prev) => prev ? { ...prev, review_status: 'accepted', openalex_id: response.data?.openalex_id } : prev);
      loadPublication();
    } catch (err) {
      setFeedbackMessage({ type: 'error', text: err.response?.data?.message || 'Accept failed.' });
    } finally {
      setOpenAlexBusy(false);
    }
  };

  const rejectOpenAlexCandidate = async () => {
    setOpenAlexBusy(true);
    try {
      await axios.post(`/api/publications/${publicationId}/enrich/openalex/reject`);
      setFeedbackMessage({ type: 'success', text: 'OpenAlex candidate rejected.' });
      setOpenAlexResult((prev) => prev ? { ...prev, review_status: 'rejected' } : prev);
    } catch (err) {
      setFeedbackMessage({ type: 'error', text: err.response?.data?.message || 'Reject failed.' });
    } finally {
      setOpenAlexBusy(false);
    }
  };

  const undoOpenAlexCandidate = async () => {
    setOpenAlexBusy(true);
    try {
      const response = await axios.post(`/api/publications/${publicationId}/enrich/openalex/undo`);
      const restored = response.data?.restored_fields?.join(', ');
      setFeedbackMessage({
        type: 'success',
        text: restored
          ? `OpenAlex enrichment undone. Restored: ${restored}.`
          : 'OpenAlex enrichment undone.',
      });
      setOpenAlexResult((prev) => prev ? { ...prev, review_status: 'rejected' } : prev);
      loadPublication();
    } catch (err) {
      setFeedbackMessage({ type: 'error', text: err.response?.data?.message || 'Undo failed.' });
    } finally {
      setOpenAlexBusy(false);
    }
  };

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
  // `setter` is the React setState for `current`; used to update in-memory
  // state with returned ids from successful POSTs, so retry-after-partial-
  // failure doesn't re-POST items that actually succeeded the first time.
  async function syncEntity({ endpoint, current, setter, originalRef, toDb, compareKeys, label }) {
    const original = originalRef.current;
    let added = 0, updated = 0, deleted = 0, errors = 0;

    // Make a mutable working copy we can patch with new ids.
    let working = current.slice();

    // Track which originals we successfully deleted so we can drop them from
    // the baseline on return; failed deletes stay in `original` so retry
    // re-attempts them.
    const successfullyDeletedIds = new Set();

    // DELETEs first
    for (const o of original) {
      if (o.id && !current.find((c) => c.id === o.id)) {
        try {
          await axios.delete(`${EDIT_BASE(publicationId)}/${endpoint}/${o.id}`);
          deleted++;
          successfullyDeletedIds.add(o.id);
        } catch (err) { errors++; console.error(`Delete ${label} ${o.id}:`, err); }
      }
    }

    // POSTs for new items (no id). On success, record the returned id in
    // `working` so the next save won't re-POST the same row.
    for (let i = 0; i < working.length; i++) {
      const c = working[i];
      if (c.id) continue;
      try {
        const response = await axios.post(`${EDIT_BASE(publicationId)}/${endpoint}`, toDb(c));
        const newId = response?.data?.id;
        if (newId) {
          working[i] = { ...c, id: newId };
        }
        added++;
      } catch (err) { errors++; console.error(`Add ${label}:`, err); }
    }

    // PUTs for changed rows (must use `working` post-POST because a failed
    // POST leaves the row id-less, which correctly skips this loop for it).
    const successfullyPutById = new Map();
    for (const c of working) {
      if (!c.id) continue;
      const o = original.find((x) => x.id === c.id);
      if (o && hasChanged(toDb(o), toDb(c), compareKeys)) {
        try {
          await axios.put(`${EDIT_BASE(publicationId)}/${endpoint}/${c.id}`, toDb(c));
          updated++;
          successfullyPutById.set(c.id, c);
        } catch (err) { errors++; console.error(`Update ${label} ${c.id}:`, err); }
      }
    }

    // Commit working array back to React state so UI reflects new ids.
    setter(working);

    // Rebuild baseline (deep-cloned) so retry replays only failed work
    // and subsequent edits on persisted rows are detected by diff.
    originalRef.current = rebuildBaseline({
      original,
      working,
      deletedIds: successfullyDeletedIds,
      putById: successfullyPutById,
    });

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
          setter: setCreators,
          originalRef: originalCreators,
          toDb: formToDbCreator,
          compareKeys: ['family_name', 'given_name', 'identifier', 'affiliation', 'role_id'],
          label: 'creator',
        });
      } else if (stepName === 'organizations') {
        result = await syncEntity({
          endpoint: 'organizations',
          current: organizations,
          setter: setOrganizations,
          originalRef: originalOrganizations,
          toDb: formToDbOrganization,
          compareKeys: ['name', 'type', 'other_name', 'country', 'identifier', 'rrid'],
          label: 'organization',
        });
      } else if (stepName === 'funders') {
        result = await syncEntity({
          endpoint: 'funders',
          current: funders,
          setter: setFunders,
          originalRef: originalFunders,
          toDb: formToDbFunder,
          compareKeys: ['name', 'type', 'other_name', 'country', 'identifier'],
          label: 'funder',
        });
      } else if (stepName === 'projects') {
        result = await syncEntity({
          endpoint: 'projects',
          current: projects,
          setter: setProjects,
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

  // ---- Local Contexts: serial diff + project-level attach/detach ----
  const saveLocalContexts = async () => {
    setIsSaving(true);
    let added = 0, removed = 0, errors = 0;
    try {
      const realCurrent = (localContexts || []).filter((p) => !p._legacy);
      const realOriginal = (originalLocalContexts.current || []).filter((p) => !p._legacy);
      const currentIds = new Set(realCurrent.map((p) => p.external_id));
      const originalIds = new Set(realOriginal.map((p) => p.external_id));

      // The pendingDetach snapshot captures projects the user marked-for-removal
      // via the resource-type-change dialog. They are no longer in the picker
      // (which currently only shows _legacy) but must still be detached server-side.
      const detachPool = realOriginal.filter((p) => !currentIds.has(p.external_id));
      for (const p of detachPool) {
        try {
          await axios.delete(`/api/localcontexts/publications/${publicationId}/projects/${p.external_id}`);
          removed += 1;
        } catch (err) {
          console.error(`Detach failed for ${p.external_id}:`, err);
          errors += 1;
        }
      }
      const toAdd = realCurrent.filter((p) => !originalIds.has(p.external_id));
      for (const p of toAdd) {
        try {
          await axios.post(`/api/localcontexts/publications/${publicationId}/projects`, {
            external_id: p.external_id,
          });
          added += 1;
        } catch (err) {
          console.error(`Attach failed for ${p.external_id}:`, err);
          errors += 1;
        }
      }

      if (errors === 0) {
        setFeedbackMessage({
          type: 'success',
          text: `Local Contexts: ${added} attached, ${removed} detached.`,
        });
        // Refresh the snapshot so a second save in the same session doesn't replay this diff.
        pendingLcDetach.current = [];
        await loadPublication();
      } else {
        setFeedbackMessage({
          type: 'warning',
          text: `Local Contexts: ${added} attached, ${removed} detached, ${errors} error(s).`,
        });
      }
    } finally {
      setIsSaving(false);
    }
  };

  // ---- Files & Documents: upload / diff-update / delete on "Save" ----
  async function savePublicationFiles() {
    // Defensive guards against the 2026-06-25 data-loss bug. The diff-and-save
    // flow below DELETEs any baseline row not present in the current state. If
    // the page never finished loading (or was clobbered to empty), running the
    // diff would silently wipe every attached file.
    if (!publicationsLoaded) {
      setFeedbackMessage({
        type: 'error',
        text: 'Publication is still loading — please wait, then try again.',
      });
      return;
    }
    const files = publicationsData.files || [];
    const original = originalPublicationFiles.current || [];
    if (original.length > 0 && files.length === 0) {
      setFeedbackMessage({
        type: 'error',
        text:
          'Publications list is empty — refusing to delete all attached files. ' +
          'Please reload the page and try again.',
      });
      return;
    }
    const wouldDeleteCount = original.filter(
      (o) => !files.find((f) => f.id === o.id)
    ).length;
    if (original.length >= 3 && wouldDeleteCount > original.length / 2) {
      const ok = typeof window !== 'undefined'
        ? window.confirm(
            `This will delete ${wouldDeleteCount} of ${original.length} attached files. Continue?`
          )
        : false;
      if (!ok) {
        setFeedbackMessage({ type: 'info', text: 'Save cancelled.' });
        return;
      }
    }

    setIsSaving(true);
    let uploaded = 0, updated = 0, deleted = 0, errors = 0;
    const defaultType = publicationsData.publicationType || '1';
    const successfullyDeletedIds = new Set();
    const successfullyPutById = new Map();
    try {
      // DELETE removed files — only successful ones drop from the baseline.
      for (const o of original) {
        if (!files.find((f) => f.id === o.id)) {
          try {
            await axios.delete(`${EDIT_BASE(publicationId)}/files/${o.id}`);
            deleted++;
            successfullyDeletedIds.add(o.id);
          } catch (err) { errors++; console.error(`Delete file ${o.id}:`, err); }
        }
      }
      // PUT metadata changes on existing rows
      for (const f of files) {
        if (!f.id || !f.existing) continue;
        const orig = original.find((x) => x.id === f.id);
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
          successfullyPutById.set(f.id, f);
        } catch (err) { errors++; console.error('File update:', err); }
      }
      // POST new items. Track response.id so retry doesn't duplicate.
      let working = files.slice();
      for (let i = 0; i < working.length; i++) {
        const f = working[i];
        if (f.id || f.existing) continue;
        const meta = f.metadata || {};
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
        try {
          const response = await axios.post(`${EDIT_BASE(publicationId)}/files`, fd);
          const newId = response?.data?.id;
          if (newId) {
            working[i] = { ...f, id: newId, existing: true, file: null };
          }
          uploaded++;
        } catch (err) { errors++; console.error('File upload:', err); }
      }
      setPublicationsData((prev) => ({ ...prev, files: working }));
      originalPublicationFiles.current = rebuildBaseline({
        original,
        working,
        deletedIds: successfullyDeletedIds,
        putById: successfullyPutById,
      });

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
    // Same defensive guards as savePublicationFiles — the Documents tab uses
    // the same diff-and-delete pattern against publication_documents and is
    // equally vulnerable to the 2026-06-25 data-loss bug.
    if (!publicationsLoaded) {
      setFeedbackMessage({
        type: 'error',
        text: 'Publication is still loading — please wait, then try again.',
      });
      return;
    }
    const docs = documentsData.files || [];
    const original = originalPublicationDocuments.current || [];
    if (original.length > 0 && docs.length === 0) {
      setFeedbackMessage({
        type: 'error',
        text:
          'Documents list is empty — refusing to delete all attached documents. ' +
          'Please reload the page and try again.',
      });
      return;
    }
    const wouldDeleteCount = original.filter(
      (o) => !docs.find((d) => d.id === o.id)
    ).length;
    if (original.length >= 3 && wouldDeleteCount > original.length / 2) {
      const ok = typeof window !== 'undefined'
        ? window.confirm(
            `This will delete ${wouldDeleteCount} of ${original.length} attached documents. Continue?`
          )
        : false;
      if (!ok) {
        setFeedbackMessage({ type: 'info', text: 'Save cancelled.' });
        return;
      }
    }

    setIsSaving(true);
    let uploaded = 0, updated = 0, deleted = 0, errors = 0;
    const defaultType = documentsData.documentType || '1';
    const successfullyDeletedIds = new Set();
    const successfullyPutById = new Map();
    try {
      for (const o of original) {
        if (!docs.find((d) => d.id === o.id)) {
          try {
            await axios.delete(`${EDIT_BASE(publicationId)}/documents/${o.id}`);
            deleted++;
            successfullyDeletedIds.add(o.id);
          } catch (err) { errors++; console.error(`Delete document ${o.id}:`, err); }
        }
      }
      // PUT metadata changes on existing documents
      for (const d of docs) {
        if (!d.id || !d.existing) continue;
        const orig = original.find((x) => x.id === d.id);
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
          successfullyPutById.set(d.id, d);
        } catch (err) { errors++; console.error('Document update:', err); }
      }
      // POST new documents. Track returned id so retry doesn't duplicate.
      let working = docs.slice();
      for (let i = 0; i < working.length; i++) {
        const d = working[i];
        if (d.id || d.existing) continue;
        const meta = d.metadata || {};
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
        try {
          const response = await axios.post(`${EDIT_BASE(publicationId)}/documents`, fd);
          const newId = response?.data?.id;
          if (newId) {
            working[i] = { ...d, id: newId, existing: true, file: null };
          }
          uploaded++;
        } catch (err) { errors++; console.error('Document upload:', err); }
      }
      setDocumentsData((prev) => ({ ...prev, files: working }));
      originalPublicationDocuments.current = rebuildBaseline({
        original,
        working,
        deletedIds: successfullyDeletedIds,
        putById: successfullyPutById,
      });

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

  if (!isRehydrated) return null;
  if (!isAuthenticated) return null;
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
        <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
          <Button variant="contained" onClick={loadPublication}>Retry</Button>
          <Button startIcon={<ArrowBackIcon />} onClick={() => router.back()}>Back</Button>
        </Box>
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
  const lastStepIndex = stepLabels.length - 1;

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
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }} sx={{ mb: 2 }}>
          <Box>
            <Typography variant="h5" fontWeight={600} gutterBottom>Edit DOCiD</Typography>
            <Typography variant="body2" color="text.secondary">
              DOCiD: <strong>{publicationData.document_docid}</strong> (handle will not change)
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<AutoAwesomeIcon />}
              onClick={() => runOpenAlexEnrichment({ titleFallback: false })}
              disabled={openAlexBusy}
            >
              {openAlexBusy ? 'Enriching…' : 'Enrich from OpenAlex'}
            </Button>
            {!hasRealDoi && (
              <Button
                variant="text"
                size="small"
                onClick={() => runOpenAlexEnrichment({ titleFallback: true })}
                disabled={openAlexBusy}
                title={publicationData?.doi
                  ? 'This publication has a DOCiD/Handle but no CrossRef DOI. OpenAlex needs a real DOI or a title.'
                  : 'No DOI on this publication — search OpenAlex by title instead.'}
              >
                Try title search
              </Button>
            )}
          </Stack>
        </Stack>
        {feedbackMessage && (
          <Alert severity={feedbackMessage.type} onClose={() => setFeedbackMessage(null)} sx={{ mt: 1 }}>
            {feedbackMessage.text}
          </Alert>
        )}
      </Paper>

      <Dialog
        open={openAlexDialogOpen}
        onClose={() => setOpenAlexDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>OpenAlex enrichment {openAlexResult?.review_status === 'accepted' && '(applied)'}</DialogTitle>
        <DialogContent dividers>
          {!openAlexResult && <Typography>No result.</Typography>}
          {openAlexResult?.status === 'not_found' && (
            <Alert severity="warning">No matching OpenAlex work was found for this publication.</Alert>
          )}
          {openAlexResult?.status === 'skipped' && (
            <Alert severity="info">{openAlexResult.message || 'Enrichment skipped.'}</Alert>
          )}
          {openAlexResult?.enrichment && (
            <Stack spacing={2}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Match</Typography>
                <Typography variant="body2">
                  Method: <strong>{openAlexResult.match_method || openAlexResult.provenance?.matchedBy}</strong>
                  {' · '}
                  Confidence: <strong>{openAlexResult.provenance?.confidence}</strong>
                  {' · '}
                  Status: <strong>{openAlexResult.review_status || openAlexResult.provenance?.status}</strong>
                </Typography>
                {openAlexResult.enrichment.openalex_id && (
                  <Typography variant="body2">
                    OpenAlex Work:{' '}
                    <a href={`https://openalex.org/${openAlexResult.enrichment.openalex_id}`} target="_blank" rel="noopener noreferrer">
                      {openAlexResult.enrichment.openalex_id}
                    </a>
                  </Typography>
                )}
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Citation count</Typography>
                <Typography>{openAlexResult.enrichment.citation_count ?? '—'}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Open access</Typography>
                <Typography>
                  {openAlexResult.enrichment.open_access_status || '—'}
                  {openAlexResult.enrichment.open_access_url && (
                    <>
                      {' · '}
                      <a href={openAlexResult.enrichment.open_access_url} target="_blank" rel="noopener noreferrer">
                        OA link
                      </a>
                    </>
                  )}
                </Typography>
              </Box>
              {openAlexResult.enrichment.topics?.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Topics</Typography>
                  <Typography variant="body2">
                    {openAlexResult.enrichment.topics.map((t) => t.name).filter(Boolean).join(' · ')}
                  </Typography>
                </Box>
              )}
              {openAlexResult.conflicts?.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Conflicts with current DOCiD data</Typography>
                  <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                    {openAlexResult.conflicts.map((c, i) => (
                      <Alert
                        key={i}
                        severity={c.severity === 'high' ? 'error' : c.severity === 'medium' ? 'warning' : 'info'}
                        sx={{ py: 0 }}
                      >
                        <strong>{c.field}:</strong>{' '}
                        DOCiD={String(c.docidValue ?? '—')} · OpenAlex={String(c.openAlexValue ?? '—')}
                      </Alert>
                    ))}
                  </Stack>
                </Box>
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAlexDialogOpen(false)}>Close</Button>
          {openAlexResult?.review_status === 'pending_review' && (
            <>
              <Button
                color="error"
                startIcon={<CancelIcon />}
                onClick={rejectOpenAlexCandidate}
                disabled={openAlexBusy}
              >
                Reject
              </Button>
              <Button
                variant="contained"
                startIcon={<CheckCircleIcon />}
                onClick={acceptOpenAlexCandidate}
                disabled={openAlexBusy}
              >
                Accept &amp; Apply
              </Button>
            </>
          )}
          {openAlexResult?.review_status === 'accepted' && (
            <Button
              color="warning"
              startIcon={<CancelIcon />}
              onClick={undoOpenAlexCandidate}
              disabled={openAlexBusy}
              title="Revert the OpenAlex fields on this publication back to their values before this enrichment was applied."
            >
              Undo
            </Button>
          )}
        </DialogActions>
      </Dialog>

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
        <Button variant="contained" disabled={activeStep === lastStepIndex} onClick={() => setActiveStep((p) => Math.min(lastStepIndex, p + 1))}>Next</Button>
      </Stack>

      {/* Step 0 — Details (+ inline Local Contexts picker for IK / Cultural Heritage) */}
      {activeStep === 0 && (
        <Stack spacing={3}>
          <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 }, borderRadius: 2 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>DOCiD™ Details</Typography>
            <Stack spacing={2}>
              <TextField label="Title" fullWidth value={documentTitle} onChange={(e) => setDocumentTitle(e.target.value)} />
              <RichTextEditor label="Description" value={documentDescription} onChange={setDocumentDescription} />
              <TextField label="Avatar URL" fullWidth value={avatarUrl} onChange={(e) => setAvatarUrl(e.target.value)} />
              <Box>
                <Button variant="contained" startIcon={<SaveIcon />} onClick={handleSaveTopLevel} disabled={isSaving}>
                  {isSaving ? 'Saving...' : 'Save Details'}
                </Button>
              </Box>
            </Stack>
          </Paper>
          {showLocalContextsStep && (
            <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 }, borderRadius: 2 }}>
              <LocalContextsForm
                value={localContexts}
                onChange={setLocalContexts}
                disabled={isSaving}
              />
              <Box mt={2}>
                <Button variant="contained" startIcon={<SaveIcon />} onClick={saveLocalContexts} disabled={isSaving}>
                  {isSaving ? 'Saving...' : 'Save Local Contexts'}
                </Button>
              </Box>
            </Paper>
          )}
        </Stack>
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
            loadGeneration={loadGeneration}
          />
          <Box mt={2}>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={savePublicationFiles}
              disabled={isSaving || !publicationsLoaded}
            >
              {isSaving ? 'Saving...' : (publicationsLoaded ? 'Save Publications' : 'Loading...')}
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
            loadGeneration={loadGeneration}
          />
          <Box mt={2}>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={savePublicationDocuments}
              disabled={isSaving || !publicationsLoaded}
            >
              {isSaving ? 'Saving...' : (publicationsLoaded ? 'Save Documents' : 'Loading...')}
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

      {/* Resource-type-change confirm dialog (deferred detach) */}
      <Dialog open={lcDialogOpen} onClose={() => setLcDialogOpen(false)}>
        <DialogTitle>Detach Local Contexts?</DialogTitle>
        <DialogContent>
          <Typography variant="body2">
            Changing the resource type away from Indigenous Knowledge / Cultural Heritage will detach
            the {(localContexts || []).filter((p) => !p._legacy).length} attached project(s) when you save.
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Legacy item-level attachments (if any) are preserved.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setLcDialogOpen(false); setLcDialogTargetType(null); }}>Cancel</Button>
          <Button
            variant="contained"
            color="warning"
            onClick={() => {
              pendingLcDetach.current = (localContexts || []).filter((p) => !p._legacy);
              setLocalContexts((prev) => (prev || []).filter((p) => p._legacy));
              setResourceTypeId(lcDialogTargetType);
              setLcDialogOpen(false);
              setLcDialogTargetType(null);
              if (activeStep === 7) setActiveStep(6);
            }}
          >
            Continue
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
