"use client";

import React from 'react';
import { Box, Typography } from '@mui/material';

const CodeBlock = ({ code, language }) => {
  return (
    <Box
      component="pre"
      sx={{
        backgroundColor: 'grey.900',
        color: 'grey.100',
        p: 3,
        borderRadius: 1,
        overflow: 'auto',
        '& code': {
          fontFamily: 'monospace',
          fontSize: '14px',
          lineHeight: 1.5,
          display: 'block',
          whiteSpace: 'pre',
        }
      }}
    >
      <code>
        {code}
      </code>
    </Box>
  );
};

export default CodeBlock; 