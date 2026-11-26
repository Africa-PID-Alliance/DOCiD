"use client";

import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  Autocomplete,
  Box,
  Checkbox,
  FormControlLabel,
  FormHelperText,
  Link,
  Paper,
  TextField,
  Typography,
  useTheme,
} from '@mui/material';
import CopyrightIcon from '@mui/icons-material/Copyright';

// ---------------------------------------------------------------------------
// Data: licence catalogue + rights declaration, fetched once per page load.
// ---------------------------------------------------------------------------

let cachedRequest = null;

const fetchLicenseCatalogue = () => {
  if (!cachedRequest) {
    cachedRequest = axios
      .get('/api/publications/get-list-licenses')
      .then((res) => ({
        licenses: Array.isArray(res.data?.licenses) ? res.data.licenses : [],
        rightsDeclaration: res.data?.rights_declaration || null,
      }))
      .catch((err) => {
        cachedRequest = null; // allow a retry on the next mount
        throw err;
      });
  }
  return cachedRequest;
};

/** { licenses, rightsDeclaration, loading, error } */
export const useLicenses = () => {
  const [state, setState] = useState({
    licenses: [],
    rightsDeclaration: null,
    loading: true,
    error: '',
  });

  useEffect(() => {
    let cancelled = false;
    fetchLicenseCatalogue()
      .then((data) => {
        if (!cancelled) setState({ ...data, loading: false, error: '' });
      })
      .catch((err) => {
        console.error('Error fetching licences:', err);
        if (!cancelled) {
          setState((prev) => ({ ...prev, loading: false, error: 'Could not load licences. Please reload the page.' }));
        }
      });
    return () => { cancelled = true; };
  }, []);

  return state;
};

/** A file has a licence when its metadata carries a licence id or code. */
export const hasLicense = (file) => {
  const value = file?.metadata?.licenseId;
  return value !== undefined && value !== null && String(value).trim() !== '';
};

/** The uploader ticked the rights declaration on this file's card. */
export const isRightsDeclared = (file) => !!file?.metadata?.rightsDeclared;

const licenseLabel = (licence) =>
  licence ? (licence.short_name && licence.short_name !== licence.name
    ? `${licence.short_name} — ${licence.name}`
    : licence.name || licence.code) : '';

// ---------------------------------------------------------------------------
// LicenseSelect: required, searchable licence picker for one publication file.
// value / onChange use the licence id ('' = none chosen).
// ---------------------------------------------------------------------------

export const LicenseSelect = ({
  value = '',
  onChange,
  error = false,
  label = 'Licence',
}) => {
  const { licenses, loading, error: loadError } = useLicenses();

  const selected = licenses.find(
    (l) => String(l.id) === String(value) || (l.code && String(l.code) === String(value))
  ) || null;

  const helper = loadError
    || (error ? 'Choose a licence for this publication' : null);

  return (
    <Box>
      <Autocomplete
        options={licenses}
        loading={loading}
        value={selected}
        onChange={(_, licence) => onChange?.(licence ? licence.id : '')}
        getOptionLabel={licenseLabel}
        isOptionEqualToValue={(option, val) => option.id === val.id}
        autoHighlight
        openOnFocus
        noOptionsText="No matching licence"
        renderOption={(props, licence) => {
          const { key, ...rest } = props;
          return (
            <li key={key} {...rest}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {licence.short_name || licence.code}
                </Typography>
                {licence.name && licence.name !== licence.short_name && (
                  <Typography variant="caption" color="text.secondary">
                    {licence.name}
                  </Typography>
                )}
              </Box>
            </li>
          );
        }}
        renderInput={(params) => (
          <TextField
            {...params}
            label={label}
            placeholder="Search licence"
            required
            error={error || !!loadError}
          />
        )}
      />
      <FormHelperText error={error || !!loadError} sx={{ ml: 0.5 }}>
        {helper || (selected?.url ? (
          <>
            How others may reuse this publication.{' '}
            <Link href={selected.url} target="_blank" rel="noopener noreferrer">
              Read the {selected.short_name || 'licence'} terms
            </Link>
          </>
        ) : 'How others may reuse this publication.')}
      </FormHelperText>
    </Box>
  );
};

// ---------------------------------------------------------------------------
// LicenseAndRights: one box per publication file holding the licence picker
// and, right under it, the rights declaration for that licence.
// ---------------------------------------------------------------------------

export const LicenseAndRights = ({
  licenseId = '',
  onLicenseChange,
  declared = false,
  onDeclaredChange,
  showDeclaration = true,
  licenseError = false,
  declarationError = false,
}) => {
  const theme = useTheme();
  const { rightsDeclaration, loading, error: loadError } = useLicenses();

  const declarationText = rightsDeclaration?.text
    || (loading ? 'Loading rights declaration…' : '');

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        borderColor: (licenseError || declarationError) ? theme.palette.error.main : theme.palette.divider,
        bgcolor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.03)' : '#fafafa',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
        <CopyrightIcon fontSize="small" color="primary" />
        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
          Licence &amp; rights
        </Typography>
      </Box>

      <LicenseSelect value={licenseId} onChange={onLicenseChange} error={licenseError} />

      {showDeclaration && !loadError && declarationText && (
        <Box sx={{ mt: 1.5 }}>
          <FormControlLabel
            sx={{ alignItems: 'flex-start', m: 0 }}
            control={(
              <Checkbox
                size="small"
                checked={!!declared}
                onChange={(e) => onDeclaredChange?.(e.target.checked)}
                disabled={loading}
                sx={{ mt: -0.5 }}
              />
            )}
            label={(
              <Typography variant="body2" sx={{ color: theme.palette.text.primary }}>
                {declarationText}
                <Typography component="span" color="error"> *</Typography>
              </Typography>
            )}
          />
          {declarationError && (
            <FormHelperText error sx={{ ml: 4 }}>
              Please confirm the rights declaration for this publication
            </FormHelperText>
          )}
        </Box>
      )}
    </Paper>
  );
};
