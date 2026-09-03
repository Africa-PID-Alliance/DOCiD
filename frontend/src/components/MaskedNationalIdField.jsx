"use client";

import React, { useRef, useEffect } from 'react';
import { TextField, InputAdornment, Tooltip, IconButton } from '@mui/material';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';

export const maskWithAsterisks = (value = '') => {
  const id = String(value);
  if (id.length <= 2) return id;
  return `${id[0]}${'*'.repeat(id.length - 2)}${id[id.length - 1]}`;
};

const nationalIdVisibilityAdornment = (isVisible, onToggle) => (
  <InputAdornment position="end">
    <Tooltip title={isVisible ? 'Hide ID' : 'View ID'}>
      <IconButton
        aria-label={isVisible ? 'Hide ID' : 'View ID'}
        onClick={onToggle}
        edge="end"
        size="small"
      >
        {isVisible ? <VisibilityOff /> : <Visibility />}
      </IconButton>
    </Tooltip>
  </InputAdornment>
);

const MaskedNationalIdField = ({
  value = '',
  onChange,
  revealed,
  onToggleReveal,
  showToggle = true,
  readOnly = false,
  InputProps: extraInputProps,
  ...textFieldProps
}) => {
  const inputRef = useRef(null);
  const caretRef = useRef(null);
  const canToggle = showToggle && typeof onToggleReveal === 'function';

  useEffect(() => {
    if (caretRef.current == null || !inputRef.current) return;
    const displayedLength = revealed ? value.length : maskWithAsterisks(value).length;
    const caret = Math.min(caretRef.current, displayedLength);
    inputRef.current.setSelectionRange(caret, caret);
    caretRef.current = null;
  });

  const emitChange = (nextValue) => {
    onChange?.({ target: { value: nextValue } });
  };

  const applyEdit = (start, end, insert = '') => {
    const nextValue = value.slice(0, start) + insert + value.slice(end);
    caretRef.current = start + insert.length;
    emitChange(nextValue);
  };

  const handlePaste = (event) => {
    if (revealed || readOnly) return;
    event.preventDefault();
    const pasted = event.clipboardData?.getData('text') ?? '';
    const start = event.target.selectionStart ?? value.length;
    const end = event.target.selectionEnd ?? value.length;
    applyEdit(start, end, pasted);
  };

  const handleBeforeInput = (event) => {
    if (revealed || readOnly) return;

    const inputType = event.nativeEvent.inputType || '';
    if (inputType === 'insertFromPaste' || inputType === 'insertFromDrop') {
      event.preventDefault();
      return;
    }

    const start = event.target.selectionStart ?? value.length;
    const end = event.target.selectionEnd ?? value.length;
    const isInsert = inputType.startsWith('insert');
    const isDelete = [
      'deleteContentBackward',
      'deleteContentForward',
      'deleteByCut',
      'deleteContent'
    ].includes(inputType);

    if (!isInsert && !isDelete) return;

    event.preventDefault();

    if (isInsert) {
      applyEdit(start, end, event.nativeEvent.data ?? '');
      return;
    }

    if (inputType === 'deleteContentForward') {
      if (start === end) {
        applyEdit(start, end + 1);
      } else {
        applyEdit(start, end);
      }
      return;
    }

    if (start === end && start > 0) {
      applyEdit(start - 1, end);
    } else {
      applyEdit(start, end);
    }
  };

  const handleChange = (event) => {
    if (revealed) {
      onChange?.(event);
      return;
    }
    if (readOnly) return;

    const nextDisplayed = event.target.value;
    const selectionEnd = event.target.selectionEnd ?? nextDisplayed.length;

    if (!nextDisplayed) {
      caretRef.current = 0;
      emitChange('');
      return;
    }

    if (!nextDisplayed.includes('*')) {
      caretRef.current = selectionEnd;
      emitChange(nextDisplayed);
      return;
    }

    const lengthDiff = nextDisplayed.length - value.length;
    if (lengthDiff > 0) {
      const insertAt = Math.max(selectionEnd - lengthDiff, 0);
      const inserted = nextDisplayed.slice(insertAt, insertAt + lengthDiff);
      caretRef.current = insertAt + lengthDiff;
      emitChange(value.slice(0, insertAt) + inserted + value.slice(insertAt));
      return;
    }

    if (lengthDiff < 0) {
      const deleteAt = selectionEnd;
      caretRef.current = deleteAt;
      emitChange(value.slice(0, deleteAt) + value.slice(deleteAt - lengthDiff));
    }
  };

  return (
    <TextField
      {...textFieldProps}
      inputRef={inputRef}
      type="text"
      value={revealed ? value : maskWithAsterisks(value)}
      autoComplete="off"
      spellCheck={false}
      onChange={handleChange}
      onPaste={handlePaste}
      onBeforeInput={handleBeforeInput}
      InputProps={{
        readOnly,
        ...extraInputProps,
        endAdornment: canToggle
          ? nationalIdVisibilityAdornment(revealed, onToggleReveal)
          : extraInputProps?.endAdornment
      }}
    />
  );
};

export default MaskedNationalIdField;
