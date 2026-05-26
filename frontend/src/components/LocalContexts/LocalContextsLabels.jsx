"use client";

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Skeleton,
  Chip,
  IconButton,
  Alert,
  Link as MuiLink,
  Stack,
} from '@mui/material';
import { OpenInNew as OpenInNewIcon } from '@mui/icons-material';
import axios from 'axios';

const TK_COLOR = '#8B4513';
const BC_COLOR = '#2E7D32';
const NOTICE_COLOR = '#1565C0';

/**
 * Renders TK Labels, BC Labels, and Notices from one or more Local Contexts
 * Hub projects attached to a DOCiD.
 *
 * Data sources:
 * - `publicationId` (saved attachments): GET /api/localcontexts/publications/<id>/projects-display
 *   returns { projects: [...], legacy: [...] }.
 * - `projectId` (demo / preview): GET /api/localcontexts/projects/<uuid>
 *   returns a single project payload. We wrap it in a 1-element array so the
 *   outer-loop renderer handles both modes identically.
 *
 * Per Local Contexts display rules:
 * - Label icons cannot be changed.
 * - Title and customized description must be easily accessible.
 * - Labels should be displayed prominently.
 */
const LocalContextsLabels = ({ projectId, publicationId }) => {
  const [projects, setProjects] = useState([]);
  const [legacy, setLegacy] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  // Per-card translation selection. Key = `${projectExternalId}::${itemUniqueId}`
  // to keep state stable even when the same item appears under two projects.
  const [selectedLang, setSelectedLang] = useState({});

  useEffect(() => {
    if (!projectId && !publicationId) {
      setIsLoading(false);
      return;
    }

    const fetchData = async () => {
      setIsLoading(true);
      setFetchError(null);
      try {
        if (publicationId) {
          const resp = await axios.get(
            `/api/localcontexts/publications/${publicationId}/projects-display`
          );
          setProjects(Array.isArray(resp.data?.projects) ? resp.data.projects : []);
          setLegacy(Array.isArray(resp.data?.legacy) ? resp.data.legacy : []);
        } else if (projectId) {
          const resp = await axios.get(`/api/localcontexts/projects/${projectId}`);
          // Normalize single-project response to the same shape /projects-display returns.
          const p = resp.data || {};
          setProjects([
            {
              project_external_id: p.unique_id || projectId,
              title: p.title,
              project_page: p.project_page,
              contributing_institutions: (p.created_by || [])
                .map((cb) => (cb.institution || {}).name)
                .filter(Boolean),
              tk_labels: p.tk_labels || [],
              bc_labels: p.bc_labels || [],
              notice: p.notice || [],
            },
          ]);
          setLegacy([]);
        }
      } catch (error) {
        console.error('Error fetching Local Contexts data:', error);
        setFetchError(error.response?.status === 404 ? 'Project not found' : 'Unable to load Local Contexts');
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [projectId, publicationId]);

  if (isLoading) {
    return (
      <Box>
        <Skeleton variant="text" width={280} height={32} />
        <Skeleton variant="rectangular" height={120} sx={{ mt: 1, borderRadius: 1 }} />
      </Box>
    );
  }
  if (fetchError) {
    return <Alert severity="warning">{fetchError}</Alert>;
  }
  if (projects.length === 0 && legacy.length === 0) {
    return null;
  }

  return (
    <Box>
      <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
        Local Contexts Labels and Notices
      </Typography>

      {projects.map((project) => (
        <ProjectPanel
          key={project.project_external_id}
          project={project}
          selectedLang={selectedLang}
          setSelectedLang={setSelectedLang}
        />
      ))}

      {legacy.length > 0 && (
        <Paper elevation={0} variant="outlined" sx={{ p: 2, mt: 2, borderRadius: 1 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Other Local Contexts items
          </Typography>
          <Stack spacing={1}>
            {legacy.map((item) => (
              <LegacyRow key={item.ctx_id} item={item} />
            ))}
          </Stack>
        </Paper>
      )}
    </Box>
  );
};

const ProjectPanel = ({ project, selectedLang, setSelectedLang }) => {
  const tk = project.tk_labels || [];
  const bc = project.bc_labels || [];
  const notices = project.notice || [];
  const institutions = project.contributing_institutions || [];

  return (
    <Paper
      elevation={0}
      variant="outlined"
      sx={{ p: 2, mb: 2, borderRadius: 1, opacity: project._stale ? 0.85 : 1 }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 2 }}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          {project.project_page ? (
            <MuiLink
              href={project.project_page}
              target="_blank"
              rel="noopener noreferrer"
              variant="subtitle1"
              fontWeight={600}
              sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}
            >
              {project.title}
              <OpenInNewIcon fontSize="inherit" />
            </MuiLink>
          ) : (
            <Typography variant="subtitle1" fontWeight={600}>{project.title}</Typography>
          )}
          {institutions.length > 0 && (
            <Typography variant="caption" color="text.secondary">
              {institutions.join(', ')}
            </Typography>
          )}
        </Box>
      </Box>

      {project._stale && (
        <Alert severity="info" sx={{ mt: 1 }} variant="outlined">
          Cached data — Local Contexts Hub temporarily unavailable.
        </Alert>
      )}

      <Stack spacing={1.5} sx={{ mt: 2 }}>
        {tk.map((item) => (
          <ItemCard
            key={`${project.project_external_id}::${item.unique_id}::tk`}
            project={project}
            item={item}
            category="TK Label"
            color={TK_COLOR}
            selectedLang={selectedLang}
            setSelectedLang={setSelectedLang}
          />
        ))}
        {bc.map((item) => (
          <ItemCard
            key={`${project.project_external_id}::${item.unique_id}::bc`}
            project={project}
            item={item}
            category="BC Label"
            color={BC_COLOR}
            selectedLang={selectedLang}
            setSelectedLang={setSelectedLang}
          />
        ))}
        {notices.map((item) => (
          <ItemCard
            key={`${project.project_external_id}::${item.unique_id}::notice`}
            project={project}
            item={item}
            category="Notice"
            color={NOTICE_COLOR}
            selectedLang={selectedLang}
            setSelectedLang={setSelectedLang}
          />
        ))}
      </Stack>
    </Paper>
  );
};

const ItemCard = ({ project, item, category, color, selectedLang, setSelectedLang }) => {
  const key = `${project.project_external_id}::${item.unique_id}`;
  const defaultLangTag = item.language_tag || 'en';
  // Labels carry their body text in `label_text`; Notices use `default_text`.
  // Normalize once so chip + displayText cannot drift.
  const baseText = item.label_text || item.default_text || '';
  const translations = Array.isArray(item.translations) ? item.translations : [];
  const seenTags = new Set();
  // Build a chip list: default first, then de-duplicated translations.
  // Translations with empty `translated_text` are dropped (no useless chips).
  const langChips = [
    { language_tag: defaultLangTag, language: item.language || 'Default', text: baseText, is_default: true },
  ];
  seenTags.add(defaultLangTag);
  for (const tr of translations) {
    if (!tr || !tr.language_tag || seenTags.has(tr.language_tag)) continue;
    const text = tr.translated_text || '';
    if (!text) continue;
    seenTags.add(tr.language_tag);
    langChips.push({
      language_tag: tr.language_tag,
      language: tr.language || tr.language_tag,
      text,
      is_default: false,
    });
  }
  const activeTag = selectedLang[key] || defaultLangTag;
  const activeChip = langChips.find((c) => c.language_tag === activeTag) || langChips[0];
  const displayText = activeChip?.text || baseText;

  return (
    <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
      {item.img_url && (
        // Local Contexts display rule: icons are served unmodified from the Hub.
        // eslint-disable-next-line @next/next/no-img-element
        <img src={item.img_url} alt={item.name} width={56} height={56} style={{ objectFit: 'contain' }} />
      )}
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ flexWrap: 'wrap' }}>
          <Typography variant="body2" fontWeight={600}>{item.name}</Typography>
          <Chip
            label={category}
            size="small"
            sx={{ bgcolor: color, color: 'white' }}
          />
          {item.community && (item.community.name || typeof item.community === 'string') && (
            <Typography variant="caption" color="text.secondary">
              {item.community.name || item.community}
            </Typography>
          )}
        </Stack>
        {langChips.length > 1 && (
          <Stack direction="row" spacing={0.5} sx={{ mt: 0.5, flexWrap: 'wrap' }}>
            {langChips.map((c) => (
              <Chip
                key={c.language_tag}
                label={c.language}
                size="small"
                variant={c.language_tag === activeTag ? 'filled' : 'outlined'}
                onClick={() => setSelectedLang((prev) => ({ ...prev, [key]: c.language_tag }))}
              />
            ))}
          </Stack>
        )}
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.75, whiteSpace: 'pre-wrap' }}>
          {displayText}
        </Typography>
        {(item.notice_page || item.label_page) && (
          <MuiLink
            href={item.notice_page || item.label_page}
            target="_blank"
            rel="noopener noreferrer"
            variant="caption"
            sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.25, mt: 0.5 }}
          >
            View on Local Contexts Hub <OpenInNewIcon fontSize="inherit" />
          </MuiLink>
        )}
      </Box>
    </Box>
  );
};

const LegacyRow = ({ item }) => (
  <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
    {item.image_url && (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={item.image_url} alt={item.title || ''} width={40} height={40} style={{ objectFit: 'contain' }} />
    )}
    <Box sx={{ flex: 1 }}>
      <Typography variant="body2" fontWeight={600}>{item.title}</Typography>
      {item.summary && (
        <Typography variant="caption" color="text.secondary">{item.summary}</Typography>
      )}
    </Box>
    <Chip label={item.context_type || 'Item'} size="small" variant="outlined" />
  </Box>
);

export default LocalContextsLabels;
