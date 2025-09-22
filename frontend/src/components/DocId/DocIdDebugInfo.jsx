'use client';

import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { formatDocIdForDisplay, formatDocIdForUrl } from '@/utils/docidUtils';

/**
 * Debug component to display DOCiD formatting information
 * Helps developers understand how DOCiD identifiers are being handled
 */
export const DocIdDebugInfo = ({ docId }) => {
  if (!docId) return null;
  
  const formattedForUrl = formatDocIdForUrl(docId);
  const formattedForDisplay = formatDocIdForDisplay(docId);
  
  return (
    <Paper sx={{ p: 2, mt: 2, bgcolor: '#f5f5f5', color: '#333' }}>
      <Typography variant="subtitle2" fontWeight="bold">DOCiD Debug Info</Typography>
      <Box sx={{ mt: 1 }}>
        <Typography variant="body2">
          <strong>Raw DOCiD:</strong> {docId}
        </Typography>
        <Typography variant="body2">
          <strong>URL Format:</strong> {formattedForUrl}
        </Typography>
        <Typography variant="body2">
          <strong>Display Format:</strong> {formattedForDisplay}
        </Typography>
      </Box>
    </Paper>
  );
};

export default DocIdDebugInfo;
