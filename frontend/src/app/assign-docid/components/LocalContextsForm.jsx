"use client";

import React from 'react';
import { Box, Typography, Divider } from '@mui/material';
import LocalContextsPicker from '@/components/LocalContexts/LocalContextsPicker';

/**
 * LocalContextsForm — thin wizard-step wrapper around the shared
 * LocalContextsPicker. Used by both assign-docid and edit-docid.
 *
 * Reads/writes the picker selection on `value` / `onChange` so the parent
 * controls form state (matching the other wizard steps).
 */
export default function LocalContextsForm({ value = [], onChange, disabled = false }) {
  return (
    <Box sx={{ p: { xs: 2, sm: 3 } }}>
      <Typography variant="h6" sx={{ mb: 1 }}>
        Local Contexts Labels and Notices
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Attach TK/BC Labels and Notices that apply to this record. Visible only for
        Indigenous Knowledge and Cultural Heritage records.
      </Typography>
      <Divider sx={{ mb: 2 }} />
      <LocalContextsPicker value={value} onChange={onChange} disabled={disabled} />
    </Box>
  );
}
