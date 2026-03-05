"use client";

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  List,
  ListItem,
  ListItemText,
  Paper,
  CircularProgress,
  Alert,
  Chip,
  InputAdornment,
} from '@mui/material';
import { Search as SearchIcon, CheckCircle as CheckCircleIcon } from '@mui/icons-material';
import axios from 'axios';
import { useTheme } from '@mui/material/styles';

const ParentDocidSelector = ({ userId, selectedParent, onSelectParent }) => {
  const theme = useTheme();
  const [userDocids, setUserDocids] = useState([]);
  const [filteredDocids, setFilteredDocids] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState(null);

  useEffect(() => {
    if (!userId) return;

    const fetchUserDocids = async () => {
      setLoading(true);
      setFetchError(null);
      try {
        const response = await axios.get(`/api/publications/my-docids/${userId}`);
        setUserDocids(response.data);
        setFilteredDocids(response.data);
      } catch (error) {
        console.error('Failed to fetch user DOCiDs:', error);
        setFetchError('Failed to load your DOCiDs. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchUserDocids();
  }, [userId]);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredDocids(userDocids);
      return;
    }

    const lowerQuery = searchQuery.toLowerCase();
    const filtered = userDocids.filter(
      (docid) =>
        docid.document_title?.toLowerCase().includes(lowerQuery) ||
        docid.document_docid?.toLowerCase().includes(lowerQuery)
    );
    setFilteredDocids(filtered);
  }, [searchQuery, userDocids]);

  const handleSelectDocid = (docid) => {
    onSelectParent(docid);
  };

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
        Select Parent DOCiD
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Choose an existing DOCiD to create a new version of. The new version will be linked to this parent.
      </Typography>

      {fetchError && (
        <Alert severity="error" sx={{ mb: 2 }}>{fetchError}</Alert>
      )}

      {/* Selected parent display */}
      {selectedParent && (
        <Alert
          severity="success"
          sx={{ mb: 2 }}
          action={
            <Chip
              label="Change"
              size="small"
              onClick={() => onSelectParent(null)}
              variant="outlined"
              sx={{ cursor: 'pointer' }}
            />
          }
        >
          <Typography variant="subtitle2">
            Selected: {selectedParent.document_title}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {selectedParent.document_docid}
            {selectedParent.version_number && ` (v${selectedParent.version_number})`}
          </Typography>
        </Alert>
      )}

      {/* Search box */}
      <TextField
        fullWidth
        placeholder="Search your DOCiDs by title or identifier..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        sx={{ mb: 2 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon color="action" />
            </InputAdornment>
          ),
        }}
      />

      {/* DOCiD list */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : filteredDocids.length === 0 ? (
        <Alert severity="info">
          {userDocids.length === 0
            ? 'You have no published DOCiDs yet. Create one first via Assign DOCiD.'
            : 'No DOCiDs match your search.'}
        </Alert>
      ) : (
        <Paper variant="outlined" sx={{ maxHeight: 400, overflow: 'auto' }}>
          <List disablePadding>
            {filteredDocids.map((docid) => {
              const isSelected = selectedParent?.id === docid.id;
              return (
                <ListItem
                  key={docid.id}
                  onClick={() => handleSelectDocid(docid)}
                  sx={{
                    cursor: 'pointer',
                    borderBottom: `1px solid ${theme.palette.divider}`,
                    bgcolor: isSelected
                      ? theme.palette.action.selected
                      : 'transparent',
                    '&:hover': {
                      bgcolor: isSelected
                        ? theme.palette.action.selected
                        : theme.palette.action.hover,
                    },
                  }}
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle2" noWrap>
                          {docid.document_title}
                        </Typography>
                        {docid.version_number && (
                          <Chip label={`v${docid.version_number}`} size="small" color="primary" variant="outlined" />
                        )}
                        {isSelected && (
                          <CheckCircleIcon color="success" fontSize="small" />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box sx={{ display: 'flex', gap: 2, mt: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">
                          {docid.document_docid}
                        </Typography>
                        {docid.published && (
                          <Typography variant="caption" color="text.secondary">
                            Published: {new Date(docid.published).toLocaleDateString()}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              );
            })}
          </List>
        </Paper>
      )}
    </Box>
  );
};

export default ParentDocidSelector;
