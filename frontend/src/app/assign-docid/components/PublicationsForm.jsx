"use client";

import React, { useState, useEffect } from 'react';
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

const PublicationsForm = ({ formData, updateFormData }) => {
  const theme = useTheme();
  const { t } = useTranslation();
  // Initialize state from props if available
  const [selectedType, setSelectedType] = useState(formData?.publicationType || '');
  const [uploadedFiles, setUploadedFiles] = useState(formData?.files || []);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [selectedFileUrl, setSelectedFileUrl] = useState('');
  const [selectedFileName, setSelectedFileName] = useState('');
  const [selectedIdentifier, setSelectedIdentifier] = useState('');
  const [generatedIdentifier, setGeneratedIdentifier] = useState('');
  const [crossrefTitle, setCrossrefTitle] = useState('');
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

  const identifiers = [
    {
      label: 'APA Handle iD',
      value: 1
    },
    {
      label: 'Datacite',
      value: 2
    },
    {
      label: 'CrossRef',
      value: 3
    },
    {
      label: 'DOI',
      value: 4,
      disabled: true
    }
  ]

  // Effect to sync state with parent when formData changes
  useEffect(() => {
    if (formData) {
      if (formData.publicationType !== selectedType) {
        setSelectedType(formData.publicationType || '');
      }
      if (formData.files !== uploadedFiles) {
        setUploadedFiles(formData.files || []);
      }
    }
  }, [formData]);

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
    
    // Create a serializable version for the form data update
    const serializableFiles = updatedFiles.map(file => ({
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: file.lastModified,
      url: file.url,
      // Don't include the actual file object in the serializable version
      file: file.file,
      metadata: file.metadata
    }));

    updateFormData({
      publicationType: selectedType,
      files: serializableFiles
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

  const handleIdentifierChange = async (index, value) => {
    setSelectedIdentifier(value);
    const selectedType = identifiers.find(type => type.value === value)?.label;
    
    if (value === 1) { // APA Handle iD
      setLoadingIdentifiers(prev => ({ ...prev, [index]: true }));
      setFindingError(false);
      setCrossrefTitle('');
      setGeneratedIdentifier('');

      try {
        const response = await axios.post(
          '/api/cordoi/assign-identifier/apa-handle',
          {}, // Modify this object if the API requires specific data in the request body
          {
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
            },
          }
        );
        console.log('Identifier APA', response)
        const identifierValue = response.data.id;
        handleMetadataChange(index, 'identifier', value);
        handleMetadataChange(index, 'identifierType', value);
        handleMetadataChange(index, 'generated_identifier', identifierValue);
      } catch (error) {
        console.error('Error generating APA Handle iD:', error);
        setFindingError(true);
        setFindingErrorText(t('assign_docid.publications_form.errors.failed_apa_handle'));
      } finally {
        setLoadingIdentifiers(prev => ({ ...prev, [index]: false }));
      }
    } else if (value === 2) { // Datacite
      setLoadingIdentifiers(prev => ({ ...prev, [index]: true }));
      setFindingError(false);
      setCrossrefTitle('');
      setGeneratedIdentifier('');

      try {
        const response = await axios.get('/api/datacite/get-doi');
        const identifierValue = response.data.doi;
        handleMetadataChange(index, 'identifier', value);
        handleMetadataChange(index, 'identifierType', value);
        handleMetadataChange(index, 'generated_identifier', identifierValue);
      } catch (error) {
        console.error('Error fetching Datacite:', error);
        setFindingError(true);
        setFindingErrorText(t('assign_docid.publications_form.errors.failed_datacite'));
      } finally {
        setLoadingIdentifiers(prev => ({ ...prev, [index]: false }));
      }
    } else if (value === 3) { // CrossRef
      // Reset states for CrossRef search
      setGeneratedIdentifier('');
      setCrossrefTitle('');
      setFindingError(false);
      handleMetadataChange(index, 'identifier', value);
      handleMetadataChange(index, 'identifierType', value);
      handleMetadataChange(index, 'generated_identifier', '');
    }
  };

  const generateCrossref = async (index) => {
    if (!crossrefTitle.trim()) return;
    
    setLoadingIdentifiers(prev => ({ ...prev, [index]: true }));
    setFindingError(false);

    try {
      const response = await axios.get(
        `/api/crossref/search/?query=${encodeURIComponent(crossrefTitle)}`
      );

      if (!response.data.data || response.data.data.length === 0) {
        setFindingError(true);
        setFindingErrorText(t('assign_docid.publications_form.errors.no_results_crossref'));
        return;
      }

      const identifierValue = response.data.data[0]?.DOI;
      if (identifierValue) {
        handleMetadataChange(index, 'generated_identifier', identifierValue);
        setGeneratedIdentifier(identifierValue);
      } else {
        setFindingError(true);
        setFindingErrorText(t('assign_docid.publications_form.errors.no_doi_crossref'));
      }
    } catch (error) {
      console.error('Error searching CrossRef:', error);
      setFindingError(true);
      setFindingErrorText(t('assign_docid.publications_form.errors.failed_crossref'));
    } finally {
      setLoadingIdentifiers(prev => ({ ...prev, [index]: false }));
    }
  };

  const cancelCrossref = (index) => {
    setGeneratedIdentifier('');
    setCrossrefTitle('');
    handleMetadataChange(index, 'identifier', '');
    handleMetadataChange(index, 'identifierType', '');
    handleMetadataChange(index, 'generated_identifier', '');
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

        {/* Uploaded Files List with Metadata */}
        {uploadedFiles.map((file, index) => (
          <Grid item xs={12} key={index}>
            <Paper sx={{ 
              p: 3, 
              mb: 2,
              bgcolor: theme.palette.background.paper,
              border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider}`
            }}>
              {/* File Info */}
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <FileIcon sx={{ mr: 2, color: theme.palette.primary.main }} />
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="subtitle1" sx={{ 
                    fontWeight: 500,
                    color: theme.palette.text.primary
                  }}>
                    {file.name}
                  </Typography>
                  <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                    {formatFileSize(file.size)}
                  </Typography>
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
                  {file.metadata.identifierType && identifiers.find(type => 
                    type.value === file.metadata.identifierType)?.label === 'CrossRef' ? (
                      <Box>
                        <TextField
                          fullWidth
                          label={t('assign_docid.publications_form.crossref_title_search')}
                          value={crossrefTitle}
                          onChange={(e) => setCrossrefTitle(e.target.value)}
                          sx={{ mb: 1 }}
                        />
                        {!file.metadata.generated_identifier ? (
                          <Button
                            variant="contained"
                            onClick={() => generateCrossref(index)}
                            fullWidth
                            disabled={!crossrefTitle.trim() || loadingIdentifiers[index]}
                          >
                            {t('assign_docid.publications_form.search_crossref')}
                          </Button>
                        ) : (
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <TextField
                              fullWidth
                              value={file.metadata.generated_identifier}
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

        {/* Add Another Publication Button */}
        {uploadedFiles.length > 0 && (
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