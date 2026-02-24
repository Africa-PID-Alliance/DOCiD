"use client";

import React, { useState, useRef, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  Tabs,
  Tab,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
  IconButton,
  Paper,
  Chip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Close as CloseIcon,
  Science as ScienceIcon,
} from '@mui/icons-material';
import axios from 'axios';

const RESOURCE_TYPES = [
  { value: 'core_facility', label: 'Core Facility' },
  { value: 'software', label: 'Software' },
  { value: 'antibody', label: 'Antibody' },
  { value: 'cell_line', label: 'Cell Line' },
];

const DEBOUNCE_DELAY_MS = 400;

const TabPanel = ({ children, value, index }) => (
  <div role="tabpanel" hidden={value !== index}>
    {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
  </div>
);

const RridSearchModal = ({
  open,
  onClose,
  entityType,
  entityId,
  onAttachSuccess,
}) => {
  // Search tab state
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [resourceType, setResourceType] = useState('core_facility');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState('');

  // Enter RRID tab state
  const [rridInput, setRridInput] = useState('');
  const [resolvedMetadata, setResolvedMetadata] = useState(null);
  const [resolveLoading, setResolveLoading] = useState(false);
  const [resolveError, setResolveError] = useState('');

  // Attach state
  const [attachLoading, setAttachLoading] = useState(null); // holds the RRID being attached
  const [attachError, setAttachError] = useState('');

  const debounceTimerRef = useRef(null);

  // Reset state when modal closes
  const handleClose = () => {
    setActiveTab(0);
    setSearchQuery('');
    setResourceType('core_facility');
    setSearchResults([]);
    setSearchLoading(false);
    setSearchError('');
    setRridInput('');
    setResolvedMetadata(null);
    setResolveLoading(false);
    setResolveError('');
    setAttachLoading(null);
    setAttachError('');
    onClose();
  };

  // Debounced search
  const handleSearchQueryChange = useCallback((event) => {
    const queryValue = event.target.value;
    setSearchQuery(queryValue);
    setSearchError('');

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    if (!queryValue.trim()) {
      setSearchResults([]);
      return;
    }

    debounceTimerRef.current = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const response = await axios.get('/api/rrid/search', {
          params: { q: queryValue, type: resourceType },
        });
        setSearchResults(response.data);
      } catch (error) {
        setSearchError(
          error.response?.data?.error || 'Failed to search RRID resources'
        );
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, DEBOUNCE_DELAY_MS);
  }, [resourceType]);

  // Re-search when resource type changes
  const handleResourceTypeChange = useCallback(async (event) => {
    const newType = event.target.value;
    setResourceType(newType);

    if (!searchQuery.trim()) return;

    setSearchLoading(true);
    setSearchError('');
    try {
      const response = await axios.get('/api/rrid/search', {
        params: { q: searchQuery, type: newType },
      });
      setSearchResults(response.data);
    } catch (error) {
      setSearchError(
        error.response?.data?.error || 'Failed to search RRID resources'
      );
    } finally {
      setSearchLoading(false);
    }
  }, [searchQuery]);

  // Resolve RRID
  const handleResolveRrid = async () => {
    if (!rridInput.trim()) return;

    setResolveLoading(true);
    setResolveError('');
    setResolvedMetadata(null);

    try {
      const response = await axios.get('/api/rrid/resolve', {
        params: { rrid: rridInput.trim() },
      });
      setResolvedMetadata(response.data);
    } catch (error) {
      setResolveError(
        error.response?.data?.error || 'Failed to resolve RRID'
      );
    } finally {
      setResolveLoading(false);
    }
  };

  // Attach RRID to entity
  const handleAttachRrid = async (rridValue) => {
    setAttachLoading(rridValue);
    setAttachError('');

    try {
      const response = await axios.post('/api/rrid/attach', {
        rrid: rridValue,
        entity_type: entityType,
        entity_id: entityId,
      });

      if (onAttachSuccess) {
        onAttachSuccess(response.data);
      }

      setAttachLoading(null);
    } catch (error) {
      const errorMessage =
        error.response?.data?.error || 'Failed to attach RRID';
      setAttachError(errorMessage);
      setAttachLoading(null);
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ScienceIcon color="primary" />
          <Typography variant="h6">Add Research Resource (RRID)</Typography>
        </Box>
        <IconButton onClick={handleClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        <Tabs
          value={activeTab}
          onChange={(event, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Search by Name" />
          <Tab label="Enter RRID" />
        </Tabs>

        {/* Search by Name tab */}
        <TabPanel value={activeTab} index={0}>
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField
              fullWidth
              label="Search RRID resources"
              placeholder="e.g. flow cytometry, microscopy..."
              value={searchQuery}
              onChange={handleSearchQueryChange}
              InputProps={{
                startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
              }}
              size="small"
            />
            <FormControl sx={{ minWidth: 160 }} size="small">
              <InputLabel>Type</InputLabel>
              <Select
                value={resourceType}
                label="Type"
                onChange={handleResourceTypeChange}
              >
                {RESOURCE_TYPES.map((resourceTypeOption) => (
                  <MenuItem key={resourceTypeOption.value} value={resourceTypeOption.value}>
                    {resourceTypeOption.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {searchLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
              <CircularProgress size={28} />
            </Box>
          )}

          {searchError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {searchError}
            </Alert>
          )}

          {attachError && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              {attachError}
            </Alert>
          )}

          {!searchLoading && searchResults.length > 0 && (
            <List disablePadding>
              {searchResults.map((result, resultIndex) => (
                <React.Fragment key={result.scicrunch_id}>
                  {resultIndex > 0 && <Divider />}
                  <ListItem
                    sx={{ px: 1, alignItems: 'flex-start' }}
                    secondaryAction={
                      <Button
                        size="small"
                        variant="contained"
                        disabled={attachLoading === result.rrid}
                        onClick={() => handleAttachRrid(result.rrid)}
                        sx={{ mt: 1 }}
                      >
                        {attachLoading === result.rrid ? (
                          <CircularProgress size={18} />
                        ) : (
                          'Attach'
                        )}
                      </Button>
                    }
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <Typography variant="subtitle2">{result.name}</Typography>
                          <Chip label={result.rrid} size="small" variant="outlined" />
                        </Box>
                      }
                      secondary={
                        <Typography variant="body2" color="text.secondary" sx={{ pr: 8 }}>
                          {result.description
                            ? result.description.length > 200
                              ? `${result.description.substring(0, 200)}...`
                              : result.description
                            : 'No description available'}
                        </Typography>
                      }
                    />
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          )}

          {!searchLoading && searchQuery && searchResults.length === 0 && !searchError && (
            <Typography color="text.secondary" sx={{ py: 3, textAlign: 'center' }}>
              No results found for &ldquo;{searchQuery}&rdquo;
            </Typography>
          )}
        </TabPanel>

        {/* Enter RRID tab */}
        <TabPanel value={activeTab} index={1}>
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField
              fullWidth
              label="Enter RRID"
              placeholder="e.g. RRID:SCR_012345 or SCR_012345"
              value={rridInput}
              onChange={(event) => {
                setRridInput(event.target.value);
                setResolveError('');
                setResolvedMetadata(null);
              }}
              size="small"
            />
            <Button
              variant="outlined"
              onClick={handleResolveRrid}
              disabled={resolveLoading || !rridInput.trim()}
            >
              {resolveLoading ? <CircularProgress size={20} /> : 'Resolve'}
            </Button>
          </Box>

          {resolveError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {resolveError}
            </Alert>
          )}

          {attachError && activeTab === 1 && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              {attachError}
            </Alert>
          )}

          {resolvedMetadata && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                {resolvedMetadata.name}
              </Typography>
              {resolvedMetadata.properCitation && (
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Citation: {resolvedMetadata.properCitation}
                </Typography>
              )}
              {resolvedMetadata.description && (
                <Typography variant="body2" gutterBottom>
                  {resolvedMetadata.description}
                </Typography>
              )}
              {resolvedMetadata.mentions !== undefined && (
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Mentions: {resolvedMetadata.mentions}
                </Typography>
              )}
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  size="small"
                  disabled={attachLoading !== null}
                  onClick={() => handleAttachRrid(rridInput.trim())}
                >
                  {attachLoading ? <CircularProgress size={18} /> : 'Attach RRID'}
                </Button>
              </Box>
            </Paper>
          )}
        </TabPanel>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default RridSearchModal;
