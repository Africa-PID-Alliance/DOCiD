"use client";

import React from 'react';
import {
  Fingerprint,
  LibraryBooks,
  Description,
  Person,
  Business,
  AttachMoney,
  Folder
} from '@mui/icons-material';

const icons = {
  1: Fingerprint,
  2: LibraryBooks,
  3: Description,
  4: Person,
  5: Business,
  6: AttachMoney,
  7: Folder
};

const CustomStepIcon = ({ active, completed, icon }) => {
  const Icon = icons[icon];

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

export default CustomStepIcon; 