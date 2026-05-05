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
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Link,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Science as ScienceIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import RridSearchModal from '@/components/RridSearch/RridSearchModal';

const RridForm = ({ formData = { resources: [] }, updateFormData, allowedResourceTypes }) => {
  const theme = useTheme();
  const [isRridModalOpen, setIsRridModalOpen] = useState(false);
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
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
          <Tooltip title="What is an RRID? Click for details." arrow>
            <IconButton
              size="small"
              onClick={() => setInfoDialogOpen(true)}
              aria-label="About RRIDs"
              sx={{
                color: theme.palette.primary.main,
                '&:hover': { bgcolor: theme.palette.action.hover }
              }}
            >
              <InfoIcon fontSize="small" />
            </IconButton>
          </Tooltip>
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
        allowedResourceTypes={allowedResourceTypes}
      />

      {/* RRID info dialog */}
      <Dialog
        open={infoDialogOpen}
        onClose={() => setInfoDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <InfoIcon color="primary" />
          About RRIDs
        </DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" paragraph>
            An <strong>RRID</strong> (Research Resource Identifier) is a persistent
            unique identifier for a research resource — a software tool, antibody,
            cell line, organism, plasmid, biological sample, or core facility — used
            in published research. RRIDs make resources citable, searchable, and
            verifiable across studies.
          </Typography>
          <Typography variant="body2" paragraph>
            RRIDs are issued by the SciCrunch Resource Identification Initiative and
            take the form <code>RRID:SCR_xxxxxx</code> (software / facility),{' '}
            <code>RRID:AB_xxxxxx</code> (antibody), <code>RRID:CVCL_xxxx</code>{' '}
            (cell line), and similar prefixes.
          </Typography>
          <Typography variant="body2" paragraph>
            Click <strong>Add</strong> to search the SciCrunch resolver and attach
            one or more RRIDs to this DOCiD. Each RRID is resolved to its name,
            description and resource type before being saved.
          </Typography>
          <Typography variant="body2">
            Learn more:{' '}
            <Link href="https://scicrunch.org/resources" target="_blank" rel="noopener noreferrer">
              SciCrunch Resources
            </Link>
            {' · '}
            <Link href="https://www.rrids.org/" target="_blank" rel="noopener noreferrer">
              rrids.org
            </Link>
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInfoDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RridForm;
