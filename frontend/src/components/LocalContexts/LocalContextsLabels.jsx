"use client";

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Skeleton,
  Chip,
  Collapse,
  IconButton,
  useTheme,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';
import axios from 'axios';

/**
 * Renders TK Labels, BC Labels, and Notices from a Local Contexts Hub project.
 *
 * Per Local Contexts display rules:
 * - Label icons cannot be changed
 * - Title and customized description must be easily accessible
 * - Labels should be displayed prominently
 */
const LocalContextsLabels = ({ projectId, publicationId }) => {
  const theme = useTheme();
  const [labelData, setLabelData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [expandedLabelIds, setExpandedLabelIds] = useState(new Set());

  useEffect(() => {
    if (!projectId && !publicationId) {
      setIsLoading(false);
      return;
    }

    const fetchLabels = async () => {
      setIsLoading(true);
      setFetchError(null);

      try {
        if (projectId) {
          const response = await axios.get(`/api/localcontexts/projects/${projectId}`);
          setLabelData(response.data);
        } else if (publicationId) {
          const response = await axios.get(`/api/localcontexts/publications/${publicationId}/contexts`);
          setLabelData(response.data);
        }
      } catch (error) {
        console.error('Error fetching Local Contexts labels:', error);
        setFetchError(error.response?.status === 404 ? 'Project not found' : 'Unable to load labels');
      } finally {
        setIsLoading(false);
      }
    };

    fetchLabels();
  }, [projectId, publicationId]);

  const toggleLabelExpanded = (labelUniqueId) => {
    setExpandedLabelIds((previousIds) => {
      const updatedIds = new Set(previousIds);
      if (updatedIds.has(labelUniqueId)) {
        updatedIds.delete(labelUniqueId);
      } else {
        updatedIds.add(labelUniqueId);
      }
      return updatedIds;
    });
  };

  const getLabelCategoryColor = (category) => {
    switch (category) {
      case 'tk': return '#8B4513';
      case 'bc': return '#2E7D32';
      case 'notice': return '#1565C0';
      default: return theme.palette.primary.main;
    }
  };

  const getLabelCategoryName = (category) => {
    switch (category) {
      case 'tk': return 'TK Label';
      case 'bc': return 'BC Label';
      case 'notice': return 'Notice';
      default: return 'Label';
    }
  };

  const renderLabelCard = (label, category) => {
    const isExpanded = expandedLabelIds.has(label.unique_id);
    const categoryColor = getLabelCategoryColor(category);
    const labelText = label.label_text || label.default_text || '';
    const shouldTruncate = labelText.length > 120;

    return (
      <Paper
        key={label.unique_id}
        elevation={1}
        sx={{
          p: 2,
          mb: 1.5,
          borderRadius: 2,
          border: `1px solid ${theme.palette.divider}`,
          borderLeft: `4px solid ${categoryColor}`,
          bgcolor: theme.palette.background.paper,
        }}
      >
        <Box display="flex" gap={2} alignItems="flex-start">
          {/* Label icon — cannot be modified per LC rules */}
          <Box
            component="img"
            src={label.svg_url || label.img_url}
            alt={label.name}
            sx={{
              width: 56,
              height: 56,
              borderRadius: 1,
              flexShrink: 0,
              objectFit: 'contain',
            }}
          />

          <Box flex={1} minWidth={0}>
            {/* Label name and category */}
            <Box display="flex" alignItems="center" gap={1} flexWrap="wrap" mb={0.5}>
              <Typography variant="subtitle2" fontWeight={700}>
                {label.name}
              </Typography>
              <Chip
                label={getLabelCategoryName(category)}
                size="small"
                sx={{
                  bgcolor: categoryColor,
                  color: '#fff',
                  fontSize: '0.7rem',
                  height: 20,
                }}
              />
            </Box>

            {/* Community name */}
            {label.community?.name && (
              <Typography variant="caption" color="text.secondary" display="block" mb={0.5}>
                {label.community.name}
              </Typography>
            )}

            {/* Label text — must be easily accessible per LC rules */}
            {labelText && (
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.5 }}>
                  {shouldTruncate && !isExpanded
                    ? `${labelText.substring(0, 120)}...`
                    : labelText}
                </Typography>
                {shouldTruncate && (
                  <IconButton
                    size="small"
                    onClick={() => toggleLabelExpanded(label.unique_id)}
                    sx={{ mt: 0.5, p: 0.25 }}
                  >
                    {isExpanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                  </IconButton>
                )}
              </Box>
            )}

            {/* Link to label page on Local Contexts Hub */}
            {label.label_page && (
              <Typography
                variant="caption"
                component="a"
                href={label.label_page}
                target="_blank"
                rel="noopener noreferrer"
                sx={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 0.5,
                  mt: 0.5,
                  color: theme.palette.primary.main,
                  textDecoration: 'none',
                  '&:hover': { textDecoration: 'underline' },
                }}
              >
                View on Local Contexts Hub
                <OpenInNewIcon sx={{ fontSize: 12 }} />
              </Typography>
            )}
          </Box>
        </Box>
      </Paper>
    );
  };

  // Loading state
  if (isLoading) {
    return (
      <Box>
        {[1, 2].map((skeletonIndex) => (
          <Paper key={skeletonIndex} elevation={1} sx={{ p: 2, mb: 1.5, borderRadius: 2 }}>
            <Box display="flex" gap={2}>
              <Skeleton variant="rounded" width={56} height={56} />
              <Box flex={1}>
                <Skeleton width="40%" height={24} />
                <Skeleton width="60%" height={16} sx={{ mt: 0.5 }} />
                <Skeleton width="90%" height={16} sx={{ mt: 0.5 }} />
              </Box>
            </Box>
          </Paper>
        ))}
      </Box>
    );
  }

  // Error state
  if (fetchError) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
        {fetchError}
      </Typography>
    );
  }

  // No data
  if (!labelData) return null;

  // Collect all labels and notices
  const tkLabels = labelData.tk_labels || [];
  const bcLabels = labelData.bc_labels || [];
  const notices = labelData.notice ? [labelData.notice] : [];
  const totalLabelCount = tkLabels.length + bcLabels.length + notices.length;

  if (totalLabelCount === 0) return null;

  return (
    <Box>
      {/* Project title if available */}
      {labelData.title && (
        <Typography variant="body2" color="text.secondary" mb={1.5}>
          Project: {labelData.title}
        </Typography>
      )}

      {/* TK Labels */}
      {tkLabels.map((label) => renderLabelCard(label, 'tk'))}

      {/* BC Labels */}
      {bcLabels.map((label) => renderLabelCard(label, 'bc'))}

      {/* Notices */}
      {notices.map((notice) => renderLabelCard(notice, 'notice'))}
    </Box>
  );
};

export default LocalContextsLabels;
