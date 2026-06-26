"use client";

import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Grid,
  Paper,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Modal,
  Tooltip,
  TextField,
  Collapse,
  Fade,
  CircularProgress,
  useTheme
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Description as FileIcon,
  Visibility as PreviewIcon,
  Close as CloseIcon,
  Add as AddIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { useSelector } from 'react-redux';

const PublicationsForm = ({ formData, updateFormData, loadGeneration = 0 }) => {
  const theme = useTheme();
  const { t } = useTranslation();
  const { user } = useSelector((state) => state.auth);
  
  // Initialize state from props if available
  const [selectedType, setSelectedType] = useState(formData?.publicationType || '');
  const [uploadedFiles, setUploadedFiles] = useState(formData?.files || []);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [selectedFileUrl, setSelectedFileUrl] = useState('');
  const [selectedFileName, setSelectedFileName] = useState('');
  const [selectedIdentifier, setSelectedIdentifier] = useState('');
  const [generatedIdentifier, setGeneratedIdentifier] = useState('');
  // crossrefTitle state removed in edit-docid fork (L1): CrossRef UI is gone.
  const [publicationTypes, setPublicationTypes] = useState([]);
  const [isLoadingTypes, setIsLoadingTypes] = useState(true);
  const [isLoadingIdentifiers, setIsLoadingIdentifiers] = useState(false);
  const [fileMetadata, setFileMetadata] = useState({
    title: '',
    description: ''
  });
  const [loadingIdentifiers, setLoadingIdentifiers] = useState({});
  const [findingError, setFindingError] = useState(false);
  const [findingErrorText, setFindingErrorText] = useState('');
  
  // Get account type name from Redux store
  const accountTypeName = user?.account_type_name || '';
  
  console.log('PublicationsForm - user:', user);
  console.log('PublicationsForm - accountTypeName:', accountTypeName);

  // Edit-docid: APA Handle iD is always minted server-side on save (the
  // Cordra child handle is our internal resolvable id). CrossRef is exposed
  // as a *tagging* mechanism for files that already have an external DOI —
  // the user looks the DOI up via api.crossref.org and we store it on the
  // row alongside the always-minted handle. DataCite / DOI remain hidden
  // because we don't yet mint either.
  const identifiers = useMemo(() => [
    { label: 'APA Handle iD', value: 1 },
    { label: 'CrossRef',      value: 3 },
  ], []);

  // Seed local state from parent at controlled moments only — namely each
  // time the parent successfully (re)loads the publication from the server.
  // The parent bumps `loadGeneration` after every successful load, including
  // post-save refresh, so we re-seed once per generation and ignore
  // incidental parent re-renders in between (tab switches, stepper nav,
  // sibling-state updates). This is the fix for the 2026-06-25 incident
  // where a passive sync effect overwrote local state and the downstream
  // diff-on-save then DELETEd the missing rows from the DB. See
  // /Users/ekariz/.claude/plans/next-we-need-to-mutable-matsumoto.md
  const lastSeededGeneration = useRef(-1);
  useEffect(() => {
    if (!formData) return;
    if (lastSeededGeneration.current === loadGeneration) return;
    setSelectedType(formData.publicationType || '');
    setUploadedFiles(formData.files || []);
    lastSeededGeneration.current = loadGeneration;
  }, [loadGeneration, formData]);

  // Fetch publication types
  useEffect(() => {
    const fetchData = async () => {
      try {
        const publicationTypesRes = await axios.get('/api/publications/get-list-publication-types');
        console.log("publication types", publicationTypesRes.data);
        setPublicationTypes(publicationTypesRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setIsLoadingTypes(false);
      }
    };
    fetchData();
  }, []);

  const handleTypeChange = (event) => {
    const newType = event.target.value;
    setSelectedType(newType);
    updateFormData({
      publicationType: newType,
      files: uploadedFiles
    });
  };

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    const newFiles = files.map(file => {
      // Create a blob URL for preview
      const url = URL.createObjectURL(file);
      
      return {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified,
        url: url,
        // Store the actual File object
        file: file,
        metadata: {
          title: '',
          description: '',
          identifier: '',
          identifierType: '',
          generated_identifier: ''
        }
      };
    });

    const updatedFiles = [...uploadedFiles, ...newFiles];
    setUploadedFiles(updatedFiles);

    // Preserve ALL fields on already-loaded rows (especially id, existing,
    // publicationType). The previous serializableFiles.map() cherry-picked
    // a fixed subset and silently dropped id/existing/publicationType from
    // existing rows — which then caused savePublicationFiles' diff loop to
    // DELETE every baseline row from the DB. Codex round-2 catch.
    updateFormData({
      publicationType: selectedType,
      files: updatedFiles,
    });
  };

  const handleRemoveFile = (index) => {
    if (uploadedFiles[index].url) {
      URL.revokeObjectURL(uploadedFiles[index].url);
    }
    const updatedFiles = uploadedFiles.filter((_, i) => i !== index);
    setUploadedFiles(updatedFiles);
    updateFormData({
      publicationType: selectedType,
      files: updatedFiles
    });
  };

  const handlePreview = (file) => {
    setSelectedFileUrl(file.url);
    setSelectedFileName(file.name);
    setPreviewOpen(true);
  };

  const handleClosePreview = () => {
    setPreviewOpen(false);
  };

  const handleMetadataChange = (index, field, value) => {
    const updatedFiles = [...uploadedFiles];
    updatedFiles[index].metadata[field] = value;
    setUploadedFiles(updatedFiles);
    updateFormData({
      publicationType: selectedType,
      files: updatedFiles
    });
  };

  // Per-file map of in-flight CrossRef errors, keyed by file index. Per-file
  // (not global) so two files' lookups can fail/succeed independently.
  const [crossrefErrors, setCrossrefErrors] = useState({});

  // Single in-place file-object replacement helper. Preserves every other
  // field on the row so callers can't accidentally drop `id`, `existing`,
  // `file`, `externalIdentifier`, etc. (See PublicationsForm.jsx:148-156 for
  // the data-loss-fix the 2026-06-25 incident motivated — keep that pattern.)
  const mutateFile = (index, patch) => {
    const next = [...uploadedFiles];
    next[index] = { ...next[index], ...patch };
    if (patch.metadata) {
      next[index].metadata = { ...next[index].metadata, ...patch.metadata };
    }
    setUploadedFiles(next);
    updateFormData({ publicationType: selectedType, files: next });
  };

  const handleIdentifierChange = (index, value) => {
    setSelectedIdentifier(value);
    setFindingError(false);
    setCrossrefErrors((e) => ({ ...e, [index]: '' }));

    if (value === 3) {
      // CrossRef path — clear any minted-handle placeholder so the user is
      // explicitly prompted to look up the external DOI. The DOI itself
      // lives in `file.externalIdentifier` (string) once the lookup runs.
      mutateFile(index, {
        externalIdentifierType: 'DOI',
        metadata: { identifier: 3, identifierType: 3, generated_identifier: '' },
      });
      return;
    }

    // value === 1 (APA Handle iD). Drop any previously-tagged external DOI
    // — the backend will mint a fresh handle on save.
    mutateFile(index, {
      externalIdentifier: '',
      externalIdentifierType: '',
      metadata: { identifier: 1, identifierType: 1, generated_identifier: 'pending' },
    });
  };

  // Per-file Crossref title-search. Stores the search query in
  // `file.metadata.crossrefTitle` so multiple files have independent inputs.
  const generateCrossref = async (index) => {
    const file = uploadedFiles[index];
    const query = (file?.metadata?.crossrefTitle || '').trim();
    if (!query) return;
    setLoadingIdentifiers((prev) => ({ ...prev, [index]: true }));
    setCrossrefErrors((e) => ({ ...e, [index]: '' }));
    try {
      const response = await axios.get(
        `/api/crossref/search/?query=${encodeURIComponent(query)}`
      );
      const hitRaw = response?.data?.data?.[0]?.DOI;
      if (!hitRaw) {
        setCrossrefErrors((e) => ({ ...e, [index]: 'No DOI found for that title.' }));
        return;
      }
      // Client-side shape check before storing — same rule the backend
      // applies (`^10\.\d+/.+`). Defends against an upstream API returning
      // a malformed DOI; without this we'd succeed in the UI but get a
      // 400 mid-save which is the worse UX.
      const hit = String(hitRaw).trim().replace(/^https?:\/\/(dx\.)?doi\.org\//i, '');
      if (!/^10\.\d+\/.+/.test(hit)) {
        setCrossrefErrors((e) => ({
          ...e,
          [index]:
            `CrossRef returned an unexpected identifier ("${hitRaw}"). ` +
            `Try a different title or paste the DOI manually.`,
        }));
        return;
      }
      mutateFile(index, {
        externalIdentifier: hit,
        externalIdentifierType: 'DOI',
      });
    } catch (err) {
      console.error('CrossRef search failed:', err);
      setCrossrefErrors((e) => ({
        ...e,
        [index]: 'CrossRef lookup failed — try again or switch back to APA Handle iD.',
      }));
    } finally {
      setLoadingIdentifiers((prev) => ({ ...prev, [index]: false }));
    }
  };

  const cancelCrossref = (index) => {
    mutateFile(index, {
      externalIdentifier: '',
      externalIdentifierType: '',
      metadata: { crossrefTitle: '' },
    });
    setCrossrefErrors((e) => ({ ...e, [index]: '' }));
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleAddAnotherPublication = () => {
    // Don't reset the selectedType - this was causing the upload section to disappear
    // setSelectedType('');
    const fileInput = document.getElementById('file-upload');
    if (fileInput) {
      // Clear the input value so the same files can be selected again if needed
      fileInput.value = '';
      fileInput.click();
    }
  };

  // Cleanup URLs when component unmounts or when files change
  useEffect(() => {
    const cleanup = () => {
      uploadedFiles.forEach(file => {
        if (file.url) {
          URL.revokeObjectURL(file.url);
        }
      });
    };

    return cleanup;
  }, [uploadedFiles]);

  return (
    <Box>
      <Typography 
        variant="h6" 
        sx={{ 
          color: theme.palette.text.primary,
          fontWeight: 600,
          fontSize: '1.25rem'
        }}
      >
        {t('assign_docid.publications_form.title')}
      </Typography>

      <Typography 
        variant="body1" 
        sx={{ 
          mb: 3,
          color: theme.palette.text.secondary,
          fontWeight: 400,
          fontSize: '1rem'
        }}
      >
        {t('assign_docid.publications_form.subtitle')}
      </Typography>
      <Grid container spacing={3}>
        {/* Publication Type Select */}
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel sx={{ color: theme.palette.text.primary }}>{t('assign_docid.publications_form.publication_type')}</InputLabel>
            <Select
              value={selectedType}
              onChange={handleTypeChange}
              label={t('assign_docid.publications_form.publication_type')}
              disabled={isLoadingTypes}
              sx={{
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: theme.palette.primary.main
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: theme.palette.primary.main
                }
              }}
            >
              {isLoadingTypes ? (
                <MenuItem disabled>
                  <CircularProgress size={20} sx={{ mr: 1 }} />
                  {t('assign_docid.publications_form.loading_types')}
                </MenuItem>
              ) : (
                publicationTypes.map((type) => (
                  <MenuItem key={type.id} value={type.id}>
                    {type.publication_type_name}
                  </MenuItem>
                ))
              )}
            </Select>
          </FormControl>
        </Grid>

        {/* File Upload Section */}
        {selectedType && (
          <Grid item xs={12}>
            <Paper 
              variant="outlined" 
              sx={{ 
                p: 3,
                border: `2px dashed ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider}`,
                bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f8f9fa',
                textAlign: 'center'
              }}
            >
              <input
                type="file"
                multiple
                id="file-upload"
                style={{ display: 'none' }}
                onChange={handleFileUpload}
                accept=".pdf,.doc,.docx,.ppt,.pptx"
              />
              <label htmlFor="file-upload">
                <Button
                  component="span"
                  variant="contained"
                  startIcon={<UploadIcon />}
                  sx={{
                    bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.main,
                    color: '#fff',
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    py: 1,
                    px: 4,
                    '&:hover': {
                      bgcolor: theme.palette.mode === 'dark' ? '#1c2552' : theme.palette.primary.dark
                    }
                  }}
                >
                  {t('assign_docid.publications_form.upload_files')}
                </Button>
              </label>
              <Typography variant="body2" sx={{ mt: 2, color: theme.palette.text.secondary }}>
                {t('assign_docid.publications_form.supported_formats')}
              </Typography>
            </Paper>
          </Grid>
        )}

        {/* Uploaded Files and Video Links List with Metadata */}
        {uploadedFiles.map((file, index) => (
          <Grid item xs={12} key={index}>
            <Paper sx={{
              p: 3,
              mb: 2,
              bgcolor: theme.palette.background.paper,
              border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider}`
            }}>
              {/* File Header */}
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <FileIcon sx={{ mr: 2, color: theme.palette.primary.main }} />
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 500, color: theme.palette.text.primary }}>
                    {file.name}
                  </Typography>
                  <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                    {formatFileSize(file.size)}
                  </Typography>
                  {file.externalIdentifier && file.externalIdentifierType === 'DOI' && (
                    <Typography variant="caption" sx={{ display: 'block', color: theme.palette.text.secondary }}>
                      DOI:&nbsp;
                      <a
                        href={`https://doi.org/${file.externalIdentifier}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: theme.palette.primary.main, textDecoration: 'none' }}
                      >
                        {file.externalIdentifier}
                      </a>
                    </Typography>
                  )}
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    startIcon={<PreviewIcon />}
                    onClick={() => handlePreview(file)}
                    variant="outlined"
                    size="small"
                    sx={{
                      borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider,
                      color: theme.palette.text.primary,
                      '&:hover': {
                        borderColor: theme.palette.primary.main,
                        bgcolor: theme.palette.action.hover
                      }
                    }}
                  >
                    {t('assign_docid.publications_form.preview')}
                  </Button>
                  <Button
                    startIcon={<DeleteIcon />}
                    onClick={() => handleRemoveFile(index)}
                    variant="outlined"
                    color="error"
                    size="small"
                  >
                    {t('assign_docid.publications_form.remove')}
                  </Button>
                </Box>
              </Box>

              {/* Metadata Fields */}
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label={t('assign_docid.publications_form.title_field')}
                    value={file.metadata.title}
                    onChange={(e) => handleMetadataChange(index, 'title', e.target.value)}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider
                        },
                        '&:hover fieldset': {
                          borderColor: theme.palette.primary.main
                        },
                        '&.Mui-focused fieldset': {
                          borderColor: theme.palette.primary.main
                        }
                      }
                    }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label={t('assign_docid.publications_form.description_field')}
                    multiline
                    rows={3}
                    value={file.metadata.description}
                    onChange={(e) => handleMetadataChange(index, 'description', e.target.value)}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider
                        },
                        '&:hover fieldset': {
                          borderColor: theme.palette.primary.main
                        },
                        '&.Mui-focused fieldset': {
                          borderColor: theme.palette.primary.main
                        }
                      }
                    }}
                  />
                </Grid>
                <Grid item xs={6}>
                  <FormControl fullWidth>
                    <InputLabel>{t('assign_docid.publications_form.identifier_type')}</InputLabel>
                    <Select
                      value={file.metadata.identifierType}
                      onChange={(e) => handleIdentifierChange(index, e.target.value)}
                      label={t('assign_docid.publications_form.identifier_type')}
                    >
                      {identifiers.map((type) => (
                        <MenuItem 
                          key={type.value} 
                          value={type.value}
                          disabled={type.disabled}
                          sx={{
                            '&.Mui-disabled': {
                              opacity: 0.6,
                              color: 'text.disabled'
                            }
                          }}
                        >
                          {type.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  {loadingIdentifiers[index] && (
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mt: 1 }}>
                      <CircularProgress size={20} sx={{ mr: 1 }} />
                      <Typography variant="body2">{t('assign_docid.publications_form.generating_identifier')}</Typography>
                    </Box>
                  )}
                  {findingError && (
                    <Typography color="error" variant="body2" sx={{ mt: 1 }}>
                      {findingErrorText}
                    </Typography>
                  )}
                </Grid>
                <Grid item xs={6}>
                  {file.metadata.identifierType === 3 ? (
                    <Box>
                      {!file.externalIdentifier ? (
                        <>
                          <TextField
                            fullWidth
                            label={t('assign_docid.publications_form.crossref_title_search')}
                            value={file.metadata.crossrefTitle || ''}
                            onChange={(e) =>
                              handleMetadataChange(index, 'crossrefTitle', e.target.value)
                            }
                            sx={{ mb: 1 }}
                          />
                          <Button
                            variant="contained"
                            onClick={() => generateCrossref(index)}
                            fullWidth
                            disabled={
                              !(file.metadata.crossrefTitle || '').trim() ||
                              !!loadingIdentifiers[index]
                            }
                          >
                            {t('assign_docid.publications_form.search_crossref')}
                          </Button>
                        </>
                      ) : (
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <TextField
                            fullWidth
                            value={file.externalIdentifier}
                            label={t('assign_docid.publications_form.generated_crossref_doi')}
                            InputProps={{ readOnly: true }}
                          />
                          <Button
                            variant="outlined"
                            color="error"
                            onClick={() => cancelCrossref(index)}
                          >
                            <CancelIcon />
                          </Button>
                        </Box>
                      )}
                      {crossrefErrors[index] && (
                        <Typography color="error" variant="body2" sx={{ mt: 1 }}>
                          {crossrefErrors[index]}
                        </Typography>
                      )}
                    </Box>
                  ) : (
                    <TextField
                      fullWidth
                      label={t('assign_docid.publications_form.generated_identifier')}
                      value={file.metadata.generated_identifier || ''}
                      InputProps={{ readOnly: true }}
                    />
                  )}
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        ))}

        {/* Add Another Publication button */}
        {selectedType && uploadedFiles.length > 0 && (
          <Grid item xs={12}>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={handleAddAnotherPublication}
              sx={{
                mt: 2,
                borderColor: theme.palette.mode === 'dark' ? 'rgba(76, 175, 80, 0.23)' : '#4caf50',
                color: '#4caf50',
                '&:hover': {
                  borderColor: '#388e3c',
                  bgcolor: theme.palette.action.hover
                }
              }}
            >
              {t('assign_docid.publications_form.add_another_publication')}
            </Button>
          </Grid>
        )}
      </Grid>

      {/* Preview Modal */}
      <Modal
        open={previewOpen}
        onClose={handleClosePreview}
        aria-labelledby="file-preview-modal"
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <Box
          sx={{
            position: 'relative',
            bgcolor: theme.palette.background.paper,
            boxShadow: 24,
            p: 0,
            width: '90vw',
            height: '90vh',
            borderRadius: 1,
            overflow: 'hidden'
          }}
        >
          <Box sx={{ 
            p: 2, 
            bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.main,
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <Typography variant="h6" component="h2">
              {selectedFileName}
            </Typography>
            <IconButton
              onClick={handleClosePreview}
              sx={{ color: '#fff' }}
            >
              <CloseIcon />
            </IconButton>
          </Box>
          <Box sx={{ height: 'calc(90vh - 64px)', width: '100%' }}>
            <iframe
              src={selectedFileUrl}
              title="File Preview"
              width="100%"
              height="100%"
              style={{ border: 'none' }}
            />
          </Box>
        </Box>
      </Modal>
    </Box>
  );
};

export default PublicationsForm; 