"use client";

import React, { useRef } from 'react';
import { TextField } from '@mui/material';

const pad = (n) => String(n).padStart(2, '0');

/** Today's date as YYYY-MM-DD in the user's local time zone. */
export const todayIso = () => {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};

/**
 * Returns an error message for a publication date value, or '' if it is
 * valid (or empty — the field is optional). The API accepts YYYY, YYYY-MM or
 * YYYY-MM-DD and rejects dates in the future.
 */
export const validatePublicationDate = (value) => {
  if (!value) return '';
  const m = /^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$/.exec(value);
  if (!m) return 'Enter a valid date';
  const year = Number(m[1]);
  const month = m[2] ? Number(m[2]) : null;
  const day = m[3] ? Number(m[3]) : null;
  if (month !== null && (month < 1 || month > 12)) return 'Enter a valid date';
  if (day !== null) {
    const last = new Date(year, month, 0).getDate();
    if (day < 1 || day > last) return 'Enter a valid date';
  }
  // Compare as strings at the same precision as the value (YYYY / YYYY-MM / YYYY-MM-DD).
  if (value > todayIso().slice(0, value.length)) {
    return 'Publication date cannot be in the future';
  }
  return '';
};

/**
 * Optional publication date picker (the browser's calendar).
 * value / onChange use YYYY-MM-DD ('' = not set).
 */
const PublicationDateField = ({
  value = '',
  onChange,
  label = 'Publication Date',
  helperText = 'Optional. The date the work was originally published.',
  ...props
}) => {
  const inputRef = useRef(null);
  // The calendar only understands full dates; older year / month-only values show as empty.
  const fullDate = /^\d{4}-\d{2}-\d{2}$/.test(value) ? value : '';
  const error = validatePublicationDate(fullDate);

  return (
    <TextField
      fullWidth
      type="date"
      label={label}
      value={fullDate}
      onChange={(e) => onChange?.(e.target.value)}
      // Open the calendar when clicking anywhere in the field, not just the icon.
      onClick={() => {
        try { inputRef.current?.showPicker?.(); } catch { /* not supported */ }
      }}
      inputRef={inputRef}
      InputLabelProps={{ shrink: true }}
      inputProps={{ max: todayIso() }}
      error={!!error}
      helperText={error || helperText}
      sx={{ '& input': { cursor: 'pointer' } }}
      {...props}
    />
  );
};

export default PublicationDateField;
