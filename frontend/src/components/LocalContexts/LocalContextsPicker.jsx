"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  TextField,
  InputAdornment,
  Paper,
  List,
  ListItemButton,
  ListItemText,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  IconButton,
  Stack,
  Chip,
  Typography,
  Link as MuiLink,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import axios from 'axios';

const MIN_SEARCH_CHARS = 3;
const SEARCH_DEBOUNCE_MS = 300;

/**
 * LocalContextsPicker — researcher-facing autocomplete for attaching LC
 * Hub projects to a DOCiD. Stacked layout: search box top, attached list
 * middle, helper footer bottom.
 *
 * Selected-array shape (the controlled value):
 *   [{ external_id, title, project_type, project_page,
 *      contributing_institutions: [string] }, ...]
 *
 * Backend deliberately derives label/notice counts and context_type per item
 * at attach time — the picker only carries the project identifier.
 */
export default function LocalContextsPicker({ value = [], onChange, disabled = false }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const debounceRef = useRef(null);

  const selectedIds = new Set((value || []).map((p) => p.external_id));

  const runSearch = useCallback(async (q) => {
    setIsSearching(true);
    setSearchError(null);
    try {
      const resp = await axios.get(
        `/api/localcontexts/projects/search?q=${encodeURIComponent(q)}&limit=8`
      );
      setResults(Array.isArray(resp.data?.results) ? resp.data.results : []);
    } catch (err) {
      if (err.response?.status === 429) {
        setSearchError('Too many searches — please pause for a moment.');
      } else if (err.response?.status === 400) {
        setSearchError(err.response.data?.error || 'Invalid search.');
      } else {
        setSearchError('Search unavailable. Please try again.');
      }
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    const trimmed = query.trim();
    if (trimmed.length < MIN_SEARCH_CHARS) {
      setResults([]);
      setSearchError(null);
      setIsSearching(false);
      return undefined;
    }
    debounceRef.current = setTimeout(() => {
      runSearch(trimmed);
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(debounceRef.current);
  }, [query, runSearch]);

  const handleSelect = (project) => {
    if (selectedIds.has(project.unique_id)) return;
    const newEntry = {
      external_id: project.unique_id,
      title: project.title,
      project_type: project.project_type || 'Other',
      project_page: project.project_page,
      contributing_institutions: project.contributing_institutions || [],
    };
    const next = [...(value || []), newEntry];
    onChange?.(next);
    setQuery('');
    setResults([]);
  };

  const handleRemove = (externalId) => {
    const next = (value || []).filter((p) => p.external_id !== externalId);
    onChange?.(next);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Search */}
      <Box sx={{ position: 'relative' }}>
        <TextField
          fullWidth
          size="small"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search Local Contexts Hub by project title"
          disabled={disabled}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                {isSearching ? <CircularProgress size={16} /> : <SearchIcon fontSize="small" />}
              </InputAdornment>
            ),
          }}
          helperText={query && query.trim().length < MIN_SEARCH_CHARS ? `Type at least ${MIN_SEARCH_CHARS} characters.` : ' '}
        />
        {searchError && (
          <Alert severity="warning" sx={{ mt: 1 }}>{searchError}</Alert>
        )}
        {results.length > 0 && (
          <Paper
            elevation={3}
            sx={{
              position: 'absolute',
              top: 'calc(100% - 4px)',
              left: 0,
              right: 0,
              zIndex: 10,
              maxHeight: 360,
              overflowY: 'auto',
            }}
          >
            <List dense disablePadding>
              {results.map((r) => {
                const alreadySelected = selectedIds.has(r.unique_id);
                const institutionLine = (r.contributing_institutions || []).join(', ');
                return (
                  <ListItemButton
                    key={r.unique_id}
                    disabled={alreadySelected}
                    onClick={() => handleSelect(r)}
                  >
                    <ListItemText
                      primary={r.title}
                      secondary={
                        <Stack direction="row" spacing={1} sx={{ mt: 0.25, alignItems: 'center', flexWrap: 'wrap' }}>
                          {institutionLine && (
                            <Typography variant="caption" color="text.secondary">{institutionLine}</Typography>
                          )}
                          <Chip label={r.project_type || 'Other'} size="small" variant="outlined" />
                          {alreadySelected && (
                            <Chip label="Already added" size="small" color="default" />
                          )}
                        </Stack>
                      }
                    />
                  </ListItemButton>
                );
              })}
            </List>
          </Paper>
        )}
      </Box>

      {/* Attached list */}
      <Box>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Attached projects ({(value || []).length})
        </Typography>
        {(value || []).length === 0 ? (
          <Alert severity="info" variant="outlined">
            No Local Contexts projects attached yet. Search above to attach TK Labels, BC Labels, or Notices to this DOCiD.
          </Alert>
        ) : (
          <Stack spacing={1}>
            {value.map((p) => (
              <Card key={p.external_id} variant="outlined">
                <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 1.25, '&:last-child': { pb: 1.25 } }}>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="body2" fontWeight={600} noWrap>{p.title}</Typography>
                    <Stack direction="row" spacing={1} sx={{ mt: 0.5, alignItems: 'center', flexWrap: 'wrap' }}>
                      {(p.contributing_institutions || []).length > 0 && (
                        <Typography variant="caption" color="text.secondary">
                          {(p.contributing_institutions || []).join(', ')}
                        </Typography>
                      )}
                      <Chip label={p.project_type || 'Other'} size="small" variant="outlined" />
                      {p.project_page && (
                        <MuiLink href={p.project_page} target="_blank" rel="noopener noreferrer" variant="caption">
                          View on Hub ↗
                        </MuiLink>
                      )}
                    </Stack>
                  </Box>
                  <IconButton
                    size="small"
                    aria-label={`Remove ${p.title}`}
                    onClick={() => handleRemove(p.external_id)}
                    disabled={disabled}
                  >
                    <DeleteOutlineIcon fontSize="small" />
                  </IconButton>
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}
      </Box>

      {/* Helper footer */}
      <Typography variant="caption" color="text.secondary">
        Local Contexts Labels and Notices help communicate Indigenous cultural rights and protocols associated with this record.{' '}
        <MuiLink href="https://localcontexts.org/labels/" target="_blank" rel="noopener noreferrer">
          Learn more ↗
        </MuiLink>
      </Typography>
    </Box>
  );
}
