"use client";

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useSelector } from 'react-redux';
import axios from 'axios';
import {
  Box, Container, Paper, Typography, TextField, Button, IconButton,
  Tabs, Tab, Divider, Alert, CircularProgress, Stack, Chip, Dialog,
  DialogTitle, DialogContent, DialogActions, MenuItem, useTheme,
} from '@mui/material';
import {
  Save as SaveIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Close as CloseIcon,
  ArrowBack as ArrowBackIcon,
  CloudUpload as UploadIcon,
} from '@mui/icons-material';

const API_BASE_EDIT = (publicationId) => `/api/publications/${publicationId}/edit`;

/**
 * Edit DOCiD page — full CRUD over an existing publication without re-minting.
 * Top-level Cordra handle never changes. New files/documents mint child handles.
 */
export default function EditDocidPage() {
  const params = useParams();
  const router = useRouter();
  const theme = useTheme();
  const publicationId = params?.id;
  const { user, isAuthenticated } = useSelector((state) => state.auth || {});
  const currentUserId = user?.id || user?.user_id || null;

  const [publicationData, setPublicationData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [activeTabIndex, setActiveTabIndex] = useState(0);
  const [feedbackMessage, setFeedbackMessage] = useState(null);

  // Top-level form
  const [documentTitle, setDocumentTitle] = useState('');
  const [documentDescription, setDocumentDescription] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');

  // Dialog state for add/edit entities
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState(null); // 'creator' | 'organization' | 'funder' | 'project' | 'file' | 'document'
  const [dialogMode, setDialogMode] = useState('add'); // 'add' | 'edit'
  const [dialogEntity, setDialogEntity] = useState({});
  const [dialogFile, setDialogFile] = useState(null);

  const loadPublication = useCallback(async () => {
    if (!publicationId || !currentUserId) return;
    setIsLoading(true);
    try {
      const response = await axios.get(
        `/api/publications/get-publication-for-edit/${publicationId}?user_id=${currentUserId}`
      );
      setPublicationData(response.data);
      setDocumentTitle(response.data.document_title || '');
      setDocumentDescription(response.data.document_description || '');
      setAvatarUrl(response.data.avatar || '');
      setFetchError(null);
    } catch (err) {
      setFetchError(err.response?.data?.message || 'Failed to load publication');
    } finally {
      setIsLoading(false);
    }
  }, [publicationId, currentUserId]);

  useEffect(() => { loadPublication(); }, [loadPublication]);

  // ---- Top-level save ----
  const handleSaveTopLevel = async () => {
    try {
      const formData = new FormData();
      formData.append('user_id', String(currentUserId));
      formData.append('documentTitle', documentTitle);
      formData.append('documentDescription', documentDescription);
      formData.append('avatar', avatarUrl);
      await axios.put(
        `/api/publications/update-publication/${publicationId}`,
        formData
      );
      setFeedbackMessage({ type: 'success', text: 'Publication details saved' });
      loadPublication();
    } catch (err) {
      setFeedbackMessage({ type: 'error', text: err.response?.data?.message || 'Save failed' });
    }
  };

  // ---- Entity dialog helpers ----
  const openAddDialog = (type) => {
    setDialogType(type);
    setDialogMode('add');
    setDialogEntity({});
    setDialogFile(null);
    setDialogOpen(true);
  };

  const openEditDialog = (type, entity) => {
    setDialogType(type);
    setDialogMode('edit');
    setDialogEntity({ ...entity });
    setDialogFile(null);
    setDialogOpen(true);
  };

  const closeDialog = () => {
    setDialogOpen(false);
    setDialogEntity({});
    setDialogFile(null);
  };

  const handleDialogSubmit = async () => {
    const entityEndpoint = {
      creator: 'creators',
      organization: 'organizations',
      funder: 'funders',
      project: 'projects',
      file: 'files',
      document: 'documents',
    }[dialogType];

    const isFileUpload = (dialogType === 'file' || dialogType === 'document');

    try {
      if (dialogMode === 'add') {
        if (isFileUpload) {
          if (!dialogFile) {
            setFeedbackMessage({ type: 'error', text: 'Please select a file to upload' });
            return;
          }
          const formData = new FormData();
          formData.append('user_id', String(currentUserId));
          formData.append('title', dialogEntity.title || '');
          formData.append('description', dialogEntity.description || '');
          formData.append('publication_type_id', dialogEntity.publication_type_id || '1');
          formData.append('file', dialogFile);
          await axios.post(
            `${API_BASE_EDIT(publicationId)}/${entityEndpoint}`,
            formData
          );
        } else {
          await axios.post(
            `${API_BASE_EDIT(publicationId)}/${entityEndpoint}`,
            { user_id: currentUserId, ...dialogEntity }
          );
        }
        setFeedbackMessage({ type: 'success', text: `${dialogType} added` });
      } else {
        // Edit (PUT)
        await axios.put(
          `${API_BASE_EDIT(publicationId)}/${entityEndpoint}/${dialogEntity.id}`,
          { user_id: currentUserId, ...dialogEntity }
        );
        setFeedbackMessage({ type: 'success', text: `${dialogType} updated` });
      }
      closeDialog();
      loadPublication();
    } catch (err) {
      setFeedbackMessage({ type: 'error', text: err.response?.data?.error || `${dialogMode} ${dialogType} failed` });
    }
  };

  const handleEntityDelete = async (entityType, entityId, label) => {
    if (!confirm(`Delete this ${entityType} (${label})?`)) return;
    const endpoint = {
      creator: 'creators',
      organization: 'organizations',
      funder: 'funders',
      project: 'projects',
      file: 'files',
      document: 'documents',
    }[entityType];
    try {
      await axios.delete(
        `${API_BASE_EDIT(publicationId)}/${endpoint}/${entityId}`,
        { data: { user_id: currentUserId } }
      );
      setFeedbackMessage({ type: 'success', text: `${entityType} deleted` });
      loadPublication();
    } catch (err) {
      setFeedbackMessage({ type: 'error', text: err.response?.data?.error || 'Delete failed' });
    }
  };

  // ---- Render ----
  if (!isAuthenticated) {
    return (
      <Container sx={{ py: 6 }}>
        <Alert severity="warning">You must be signed in to edit.</Alert>
      </Container>
    );
  }

  if (isLoading) {
    return (
      <Container sx={{ py: 6, textAlign: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (fetchError) {
    return (
      <Container sx={{ py: 6 }}>
        <Alert severity="error">{fetchError}</Alert>
        <Button sx={{ mt: 2 }} startIcon={<ArrowBackIcon />} onClick={() => router.back()}>Back</Button>
      </Container>
    );
  }

  if (!publicationData) return null;

  const creators = publicationData.publication_creators || [];
  const organizations = publicationData.publication_organizations || [];
  const funders = publicationData.publication_funders || [];
  const projects = publicationData.publication_projects || [];
  const files = publicationData.publications_files || [];
  const documents = publicationData.publication_documents || [];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Button startIcon={<ArrowBackIcon />} onClick={() => router.push(`/docid/${publicationData.document_docid}`)} sx={{ mb: 2 }}>
        Back to DOCiD
      </Button>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" fontWeight={600} gutterBottom>Edit DOCiD</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          DOCiD: <strong>{publicationData.document_docid}</strong> (handle will not change)
        </Typography>

        {feedbackMessage && (
          <Alert severity={feedbackMessage.type} onClose={() => setFeedbackMessage(null)} sx={{ mb: 2 }}>
            {feedbackMessage.text}
          </Alert>
        )}
      </Paper>

      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTabIndex} onChange={(_, newIndex) => setActiveTabIndex(newIndex)} variant="scrollable" scrollButtons="auto">
          <Tab label="Details" />
          <Tab label={`Creators (${creators.length})`} />
          <Tab label={`Organizations (${organizations.length})`} />
          <Tab label={`Funders (${funders.length})`} />
          <Tab label={`Projects (${projects.length})`} />
          <Tab label={`Files (${files.length})`} />
          <Tab label={`Documents (${documents.length})`} />
        </Tabs>
      </Paper>

      {/* Tab 0: Details */}
      {activeTabIndex === 0 && (
        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <TextField label="Title" fullWidth value={documentTitle} onChange={(e) => setDocumentTitle(e.target.value)} />
            <TextField label="Description (HTML allowed)" fullWidth multiline minRows={6} value={documentDescription} onChange={(e) => setDocumentDescription(e.target.value)} />
            <TextField label="Avatar URL" fullWidth value={avatarUrl} onChange={(e) => setAvatarUrl(e.target.value)} />
            <Box>
              <Button variant="contained" startIcon={<SaveIcon />} onClick={handleSaveTopLevel}>Save Details</Button>
            </Box>
          </Stack>
        </Paper>
      )}

      {/* Tab 1: Creators */}
      {activeTabIndex === 1 && (
        <EntityListPanel
          entityLabel="Creator"
          items={creators}
          onAdd={() => openAddDialog('creator')}
          onEdit={(item) => openEditDialog('creator', item)}
          onDelete={(item) => handleEntityDelete('creator', item.id, `${item.given_name || ''} ${item.family_name || ''}`.trim())}
          renderRow={(item) => (
            <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
              <Typography fontWeight={600}>{item.given_name} {item.family_name}</Typography>
              {item.affiliation && <Chip label={item.affiliation} size="small" />}
              {item.identifier && <Chip label={item.identifier} size="small" component="a" href={item.identifier} target="_blank" clickable />}
            </Stack>
          )}
        />
      )}

      {/* Tab 2: Organizations */}
      {activeTabIndex === 2 && (
        <EntityListPanel
          entityLabel="Organization"
          items={organizations}
          onAdd={() => openAddDialog('organization')}
          onEdit={(item) => openEditDialog('organization', item)}
          onDelete={(item) => handleEntityDelete('organization', item.id, item.name)}
          renderRow={(item) => (
            <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
              <Typography fontWeight={600}>{item.name}</Typography>
              {item.type && <Chip label={item.type} size="small" />}
              {item.identifier && <Chip label={item.identifier} size="small" component="a" href={item.identifier} target="_blank" clickable />}
            </Stack>
          )}
        />
      )}

      {/* Tab 3: Funders */}
      {activeTabIndex === 3 && (
        <EntityListPanel
          entityLabel="Funder"
          items={funders}
          onAdd={() => openAddDialog('funder')}
          onEdit={(item) => openEditDialog('funder', item)}
          onDelete={(item) => handleEntityDelete('funder', item.id, item.name)}
          renderRow={(item) => (
            <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
              <Typography fontWeight={600}>{item.name}</Typography>
              {item.type && <Chip label={item.type} size="small" />}
              {item.identifier && <Chip label={item.identifier} size="small" />}
            </Stack>
          )}
        />
      )}

      {/* Tab 4: Projects */}
      {activeTabIndex === 4 && (
        <EntityListPanel
          entityLabel="Project"
          items={projects}
          onAdd={() => openAddDialog('project')}
          onEdit={(item) => openEditDialog('project', item)}
          onDelete={(item) => handleEntityDelete('project', item.id, item.title)}
          renderRow={(item) => (
            <Stack>
              <Typography fontWeight={600}>{item.title}</Typography>
              {item.identifier && <Typography variant="caption" color="text.secondary">{item.identifier}</Typography>}
            </Stack>
          )}
        />
      )}

      {/* Tab 5: Files */}
      {activeTabIndex === 5 && (
        <EntityListPanel
          entityLabel="File"
          items={files}
          onAdd={() => openAddDialog('file')}
          onDelete={(item) => handleEntityDelete('file', item.id, item.title)}
          renderRow={(item) => (
            <Stack>
              <Typography fontWeight={600}>{item.title}</Typography>
              {item.handle_identifier && <Typography variant="caption" color="primary">Handle: {item.handle_identifier}</Typography>}
              {item.file_url && (
                <Typography variant="caption" component="a" href={item.file_url} target="_blank" sx={{ color: theme.palette.primary.main }}>
                  {item.file_url}
                </Typography>
              )}
            </Stack>
          )}
          hideEdit
        />
      )}

      {/* Tab 6: Documents */}
      {activeTabIndex === 6 && (
        <EntityListPanel
          entityLabel="Document"
          items={documents}
          onAdd={() => openAddDialog('document')}
          onDelete={(item) => handleEntityDelete('document', item.id, item.title)}
          renderRow={(item) => (
            <Stack>
              <Typography fontWeight={600}>{item.title}</Typography>
              {item.handle_identifier && <Typography variant="caption" color="primary">Handle: {item.handle_identifier}</Typography>}
              {item.file_url && (
                <Typography variant="caption" component="a" href={item.file_url} target="_blank" sx={{ color: theme.palette.primary.main }}>
                  {item.file_url}
                </Typography>
              )}
            </Stack>
          )}
          hideEdit
        />
      )}

      {/* Entity dialog */}
      <EntityDialog
        open={dialogOpen}
        onClose={closeDialog}
        onSubmit={handleDialogSubmit}
        dialogType={dialogType}
        dialogMode={dialogMode}
        entity={dialogEntity}
        onEntityChange={setDialogEntity}
        fileObj={dialogFile}
        onFileChange={setDialogFile}
      />
    </Container>
  );
}

function EntityListPanel({ entityLabel, items, onAdd, onEdit, onDelete, renderRow, hideEdit }) {
  return (
    <Paper sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">{entityLabel}s</Typography>
        <Button startIcon={<AddIcon />} onClick={onAdd} variant="contained">Add {entityLabel}</Button>
      </Stack>
      <Divider sx={{ mb: 2 }} />
      {items.length === 0 ? (
        <Typography variant="body2" color="text.secondary">No {entityLabel.toLowerCase()}s yet.</Typography>
      ) : (
        <Stack spacing={1.5}>
          {items.map((item) => (
            <Paper key={item.id} variant="outlined" sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box flex={1} minWidth={0}>{renderRow(item)}</Box>
              <Stack direction="row" spacing={0.5}>
                {!hideEdit && onEdit && (
                  <IconButton size="small" onClick={() => onEdit(item)} aria-label={`Edit ${entityLabel}`}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                )}
                <IconButton size="small" onClick={() => onDelete(item)} aria-label={`Delete ${entityLabel}`} color="error">
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Stack>
            </Paper>
          ))}
        </Stack>
      )}
    </Paper>
  );
}

function EntityDialog({ open, onClose, onSubmit, dialogType, dialogMode, entity, onEntityChange, fileObj, onFileChange }) {
  const update = (field) => (e) => onEntityChange({ ...entity, [field]: e.target.value });
  const isFileType = dialogType === 'file' || dialogType === 'document';

  const renderFields = () => {
    switch (dialogType) {
      case 'creator':
        return (
          <>
            <TextField label="Family Name*" fullWidth margin="dense" value={entity.family_name || ''} onChange={update('family_name')} />
            <TextField label="Given Name" fullWidth margin="dense" value={entity.given_name || ''} onChange={update('given_name')} />
            <TextField label="Affiliation" fullWidth margin="dense" value={entity.affiliation || ''} onChange={update('affiliation')} />
            <TextField label="Identifier (e.g. ORCID URL)" fullWidth margin="dense" value={entity.identifier || ''} onChange={update('identifier')} />
            <TextField label="Identifier Type" select fullWidth margin="dense" value={entity.identifier_type || 'orcid'} onChange={update('identifier_type')}>
              <MenuItem value="orcid">ORCID</MenuItem>
              <MenuItem value="isni">ISNI</MenuItem>
              <MenuItem value="viaf">VIAF</MenuItem>
              <MenuItem value="">Other</MenuItem>
            </TextField>
          </>
        );
      case 'organization':
        return (
          <>
            <TextField label="Name*" fullWidth margin="dense" value={entity.name || ''} onChange={update('name')} />
            <TextField label="Type*" fullWidth margin="dense" value={entity.type || ''} onChange={update('type')} placeholder="e.g. Education, Government, Research" />
            <TextField label="Other Name" fullWidth margin="dense" value={entity.other_name || ''} onChange={update('other_name')} />
            <TextField label="Country" fullWidth margin="dense" value={entity.country || ''} onChange={update('country')} />
            <TextField label="ROR/Identifier URL" fullWidth margin="dense" value={entity.identifier || ''} onChange={update('identifier')} />
            <TextField label="Identifier Type" select fullWidth margin="dense" value={entity.identifier_type || 'ror'} onChange={update('identifier_type')}>
              <MenuItem value="ror">ROR</MenuItem>
              <MenuItem value="isni">ISNI</MenuItem>
              <MenuItem value="ringgold">Ringgold</MenuItem>
              <MenuItem value="">Other</MenuItem>
            </TextField>
          </>
        );
      case 'funder':
        return (
          <>
            <TextField label="Name*" fullWidth margin="dense" value={entity.name || ''} onChange={update('name')} />
            <TextField label="Type*" fullWidth margin="dense" value={entity.type || ''} onChange={update('type')} placeholder="e.g. Grantor, Corporation" />
            <TextField label="Funder Type ID" select fullWidth margin="dense" value={entity.funder_type_id || 1} onChange={update('funder_type_id')}>
              <MenuItem value={1}>Grantor</MenuItem>
              <MenuItem value={2}>Investor</MenuItem>
              <MenuItem value={3}>Corporation</MenuItem>
            </TextField>
            <TextField label="Country" fullWidth margin="dense" value={entity.country || ''} onChange={update('country')} />
            <TextField label="ROR URL" fullWidth margin="dense" value={entity.identifier || ''} onChange={update('identifier')} />
          </>
        );
      case 'project':
        return (
          <>
            <TextField label="Title*" fullWidth margin="dense" value={entity.title || ''} onChange={update('title')} />
            <TextField label="Description" fullWidth multiline minRows={3} margin="dense" value={entity.description || ''} onChange={update('description')} />
            <TextField label="RAiD/Identifier URL" fullWidth margin="dense" value={entity.identifier || ''} onChange={update('identifier')} />
          </>
        );
      case 'file':
      case 'document':
        return (
          <>
            <TextField label="Title*" fullWidth margin="dense" value={entity.title || ''} onChange={update('title')} />
            <TextField label="Description" fullWidth multiline minRows={3} margin="dense" value={entity.description || ''} onChange={update('description')} />
            <TextField label="Publication Type ID" type="number" fullWidth margin="dense" value={entity.publication_type_id || 1} onChange={update('publication_type_id')} />
            <Button variant="outlined" component="label" startIcon={<UploadIcon />} sx={{ mt: 2 }}>
              {fileObj ? fileObj.name : 'Select file to upload'}
              <input type="file" hidden onChange={(e) => onFileChange(e.target.files?.[0] || null)} />
            </Button>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              A new Cordra child handle will be minted on upload.
            </Typography>
          </>
        );
      default:
        return null;
    }
  };

  const titleText = dialogMode === 'add' ? `Add ${dialogType}` : `Edit ${dialogType}`;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {titleText}
        <IconButton onClick={onClose} size="small"><CloseIcon /></IconButton>
      </DialogTitle>
      <DialogContent dividers>{renderFields()}</DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={onSubmit}>{dialogMode === 'add' ? 'Add' : 'Save'}</Button>
      </DialogActions>
    </Dialog>
  );
}
