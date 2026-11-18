'use client';

import React, { useState } from 'react';
import {
  Box, Typography, Button, Chip, Tooltip, Link, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Stack,
} from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import { Edit as EditIcon, Lock as LockIcon } from '@mui/icons-material';

/** Small green ORCID badge shown next to values that come from ORCID (read-only). */
export function OrcidBadge({ title = 'Synced from ORCID (edit on orcid.org)' }) {
  return (
    <Tooltip title={title}>
      <Chip
        size="small"
        icon={<LockIcon sx={{ fontSize: '12px !important', color: '#fff !important' }} />}
        label="ORCID"
        sx={{ height: 18, fontSize: 10, fontWeight: 600, bgcolor: '#A6CE39', color: '#fff', ml: 1, '& .MuiChip-label': { px: 0.75 } }}
      />
    </Tooltip>
  );
}

function renderValue(value, emptyText) {
  if (value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0)) {
    return <Typography sx={{ color: 'text.secondary' }}>{emptyText}</Typography>;
  }
  if (Array.isArray(value)) {
    return (
      <Stack spacing={0.5} sx={{ minWidth: 0 }}>
        {value.map((item, i) => (
          <Typography key={i} variant="body2" sx={{ color: 'text.primary', wordBreak: 'break-word' }}>
            {item.url ? <Link href={item.url} target="_blank" rel="noopener noreferrer">{item.text}</Link> : item.text}
          </Typography>
        ))}
      </Stack>
    );
  }
  if (typeof value === 'object' && value.url) {
    return (
      <Link href={value.url} target="_blank" rel="noopener noreferrer" sx={{ wordBreak: 'break-all' }}>
        {value.text || value.url}
      </Link>
    );
  }
  return <Typography sx={{ color: 'text.primary', wordBreak: 'break-word' }}>{String(value)}</Typography>;
}

/**
 * fields: [{ key, label, orcidValue, userValue, multiline }]
 *  - orcidValue present  -> shown with ORCID badge, not editable (ORCID is source of truth)
 *  - otherwise           -> userValue shown, editable via the pencil dialog
 */
export default function OrcidProfileSection({
  title, description, fields, onSave, emptyText = 'No data available', labelWidth = 170,
}) {
  const theme = useTheme();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState({});
  const [saving, setSaving] = useState(false);

  const isFromOrcid = (f) => {
    const val = f.orcidValue;
    return !(val === null || val === undefined || val === '' || (Array.isArray(val) && val.length === 0));
  };
  const editable = fields.filter((f) => !isFromOrcid(f) && f.key);

  const openEditor = () => {
    setDraft(Object.fromEntries(editable.map((f) => [f.key, f.userValue || ''])));
    setOpen(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave?.(draft);
      setOpen(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ p: 2, backgroundColor: 'background.paper', borderRadius: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="subtitle1" sx={{ color: 'primary.main', fontWeight: 500 }}>
          {title}
        </Typography>
        {editable.length > 0 && (
          <Tooltip title="Edit fields not provided by ORCID">
            <Button
              onClick={openEditor}
              sx={{
                minWidth: 'auto', p: 1,
                color: theme.palette.mode === 'dark' ? theme.palette.common.white : '#1565c0',
                '&:hover': { backgroundColor: alpha(theme.palette.mode === 'dark' ? theme.palette.common.white : '#1565c0', 0.1) },
              }}
            >
              <EditIcon fontSize="small" />
            </Button>
          </Tooltip>
        )}
      </Box>

      {description && (
        <Typography sx={{ color: 'text.primary', mb: 3, lineHeight: 1.6 }}>{description}</Typography>
      )}

      {fields.map((field, index) => {
        const fromOrcid = isFromOrcid(field);
        return (
          <Box key={field.key || index} sx={{ display: 'flex', mb: index !== fields.length - 1 ? 2 : 0, alignItems: 'flex-start' }}>
            <Typography sx={{ color: 'primary.main', width: `${labelWidth}px`, flexShrink: 0 }}>
              {field.label}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', minWidth: 0, flex: 1 }}>
              <Box sx={{ minWidth: 0 }}>{renderValue(fromOrcid ? field.orcidValue : field.userValue, emptyText)}</Box>
              {fromOrcid && <OrcidBadge />}
            </Box>
          </Box>
        );
      })}

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{title}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Fields synced from ORCID are managed on orcid.org and can't be edited here.
          </Typography>
          <Stack spacing={2}>
            {editable.map((f) => (
              <TextField
                key={f.key}
                label={String(f.label).replace(/:$/, '')}
                value={draft[f.key] ?? ''}
                onChange={(e) => setDraft((d) => ({ ...d, [f.key]: e.target.value }))}
                multiline={!!f.multiline}
                minRows={f.multiline ? 2 : undefined}
                fullWidth
                size="small"
              />
            ))}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave} disabled={saving}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
