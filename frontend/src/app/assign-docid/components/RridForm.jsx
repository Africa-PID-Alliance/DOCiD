"use client";

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  IconButton,
  Paper,
  Divider,
  Chip,
  useTheme,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Science as ScienceIcon,
} from '@mui/icons-material';
import RridSearchModal from '@/components/RridSearch/RridSearchModal';

const RridForm = ({ formData = { resources: [] }, updateFormData }) => {
  const theme = useTheme();
  const [isRridModalOpen, setIsRridModalOpen] = useState(false);
  const [researchResources, setResearchResources] = useState(formData?.resources || []);

  const handleAddResource = (selectedRridData) => {
    const isDuplicate = researchResources.some(
      (existingResource) => existingResource.rrid === selectedRridData.rrid
    );
    if (isDuplicate) return;

    const updatedResources = [...researchResources, selectedRridData];
    setResearchResources(updatedResources);
    updateFormData({ resources: updatedResources });
  };

  const handleRemoveResource = (resourceIndex) => {
    const updatedResources = researchResources.filter((_, index) => index !== resourceIndex);
    setResearchResources(updatedResources);
    updateFormData({ resources: updatedResources });
  };

  const getResourceTypeLabel = (resourceTypeValue) => {
    const typeLabels = {
      core_facility: 'Core Facility',
      software: 'Software',
      antibody: 'Antibody',
      cell_line: 'Cell Line',
    };
    return typeLabels[resourceTypeValue] || resourceTypeValue || 'Resource';
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ScienceIcon sx={{ color: theme.palette.primary.main }} />
          <Typography variant="h6" sx={{ color: theme.palette.text.primary }}>
            Research Resources (RRID)
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setIsRridModalOpen(true)}
          sx={{
            bgcolor: theme.palette.mode === 'dark' ? '#2e7d32' : '#4caf50',
            color: '#fff',
            '&:hover': {
              bgcolor: theme.palette.mode === 'dark' ? '#1b5e20' : '#388e3c'
            }
          }}
        >
          Add
        </Button>
      </Box>

      <Divider sx={{ mb: 3, bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider }} />

      {/* Resources List */}
      {researchResources.length > 0 ? (
        <Box sx={{ width: '100%' }}>
          {researchResources.map((resource, index) => (
            <Paper
              key={resource.rrid}
              elevation={1}
              sx={{
                mb: 2,
                borderRadius: 1,
                p: 3,
                position: 'relative',
                bgcolor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider}`
              }}
            >
              <Box sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                mb: 1
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                  <Typography variant="subtitle1" fontWeight={600}>
                    {resource.rridName || resource.rrid}
                  </Typography>
                  <Chip label={resource.rrid} size="small" variant="outlined" color="primary" />
                  <Chip label={getResourceTypeLabel(resource.rridResourceType)} size="small" />
                </Box>
                <IconButton
                  onClick={() => handleRemoveResource(index)}
                  sx={{
                    color: theme.palette.error.main,
                    '&:hover': {
                      bgcolor: theme.palette.action.hover
                    }
                  }}
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
              {resource.rridDescription && (
                <Typography variant="body2" color="text.secondary">
                  {resource.rridDescription.length > 200
                    ? `${resource.rridDescription.substring(0, 200)}...`
                    : resource.rridDescription}
                </Typography>
              )}
            </Paper>
          ))}
        </Box>
      ) : (
        <Typography
          color="text.secondary"
          sx={{ textAlign: 'center', py: 2, fontStyle: 'italic' }}
        >
          No research resources added yet
        </Typography>
      )}

      {/* RRID Search Modal */}
      <RridSearchModal
        open={isRridModalOpen}
        onClose={() => setIsRridModalOpen(false)}
        collectOnly
        onSelectRrid={handleAddResource}
      />
    </Box>
  );
};

export default RridForm;
