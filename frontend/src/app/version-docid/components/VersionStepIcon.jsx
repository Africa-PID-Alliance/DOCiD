"use client";

import React from 'react';
import {
  Link as LinkIcon,
  Fingerprint,
  LibraryBooks,
  Description,
  Person,
  Business,
  AttachMoney,
  Folder
} from '@mui/icons-material';

const versionStepIcons = {
  1: LinkIcon,        // Select Parent DOCiD
  2: Fingerprint,     // DOCiD
  3: LibraryBooks,    // Publications
  4: Description,     // Documents
  5: Person,          // Creators
  6: Business,        // Organizations
  7: AttachMoney,     // Funders
  8: Folder           // Projects
};

const VersionStepIcon = ({ active, completed, icon }) => {
  const Icon = versionStepIcons[icon];

  if (!Icon) return null;

  return (
    <div
      style={{
        backgroundColor: active || completed ? '#1565c0' : 'transparent',
        color: active || completed ? '#fff' : '#1565c0',
        width: '40px',
        height: '40px',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: active || completed ? 'none' : '2px solid #1565c0',
        transition: 'all 0.3s ease-in-out',
      }}
    >
      <Icon style={{
        fontSize: '1.5rem',
        transition: 'all 0.3s ease-in-out',
        transform: active ? 'scale(1.1)' : 'scale(1)'
      }} />
    </div>
  );
};

export default VersionStepIcon;
