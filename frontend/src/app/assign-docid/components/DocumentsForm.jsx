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
  Alert,
  Tooltip,
  Modal,
  TextField,
  CircularProgress,
  useTheme
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  VideoFile as VideoIcon,
  AudioFile as AudioIcon,
  Dataset as DatasetIcon,
  Image as ImageIcon,
  Gif as GifIcon,
  Article as ArticleIcon,
  Book as BookIcon,
  Description as DocumentIcon,
  Visibility as PreviewIcon,
  Close as CloseIcon,
  Cancel as CancelIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const documentTypes = [
  { id: 1, type: 'Video', extensions: '.mp4, .mov, .avi, .mkv', icon: VideoIcon, enabled: true },
  { id: 2, type: 'Audio', extensions: '.mp3, .wav, .ogg, .m4a', icon: AudioIcon, enabled: true },
  { id: 3, type: 'Datasets', extensions: '.csv, .xlsx, .json, .xml', icon: DatasetIcon, enabled: true },
  { id: 4, type: 'Image', extensions: '.jpg, .jpeg, .png, .webp', icon: ImageIcon, enabled: true },
  { id: 5, type: 'Gif', extensions: '.gif', icon: GifIcon, enabled: true },
  { id: 6, type: 'Article', extensions: '.pdf, .doc, .docx', icon: ArticleIcon, enabled: false },
  { id: 7, type: 'Book Chapter', extensions: '.pdf, .doc, .docx', icon: BookIcon, enabled: false },
  { id: 8, type: 'Chapter', extensions: '.pdf, .doc, .docx', icon: BookIcon, enabled: false },
  { id: 9, type: 'Proceeding', extensions: '.pdf, .doc, .docx', icon: DocumentIcon, enabled: false },
  { id: 10, type: 'Monograph', extensions: '.pdf, .doc, .docx', icon: BookIcon, enabled: false },
  { id: 11, type: 'Preprint', extensions: '.pdf, .doc, .docx', icon: ArticleIcon, enabled: false },
  { id: 12, type: 'Edited Book', extensions: '.pdf, .doc, .docx', icon: BookIcon, enabled: false },
  { id: 13, type: 'Seminar', extensions: '.pdf, .doc, .docx', icon: DocumentIcon, enabled: false },
  { id: 14, type: 'Research Chapter', extensions: '.pdf, .doc, .docx', icon: BookIcon, enabled: false },
  { id: 15, type: 'Review Article', extensions: '.pdf, .doc, .docx', icon: ArticleIcon, enabled: false },
  { id: 16, type: 'Book Review', extensions: '.pdf, .doc, .docx', icon: BookIcon, enabled: false },
  { id: 17, type: 'Conference Abstract', extensions: '.pdf, .doc, .docx', icon: DocumentIcon, enabled: false },
  { id: 18, type: 'Letter to Editor', extensions: '.pdf, .doc, .docx', icon: ArticleIcon, enabled: false },
  { id: 19, type: 'Editorial', extensions: '.pdf, .doc, .docx', icon: ArticleIcon, enabled: false },
  { id: 20, type: 'Other Book Content', extensions: '.pdf, .doc, .docx', icon: BookIcon, enabled: false },
  { id: 21, type: 'Correction Erratum', extensions: '.pdf, .doc, .docx', icon: DocumentIcon, enabled: false }
];

const DocumentsForm = ({ formData, updateFormData }) => {
  const theme = useTheme();
  const { t } = useTranslation();
  // Initialize state from props if available
  const [selectedType, setSelectedType] = useState(formData?.documentType || '');
  const [uploadedFiles, setUploadedFiles] = useState(formData?.files || []);
  const [error, setError] = useState('');
  const [previewOpen, setPreviewOpen] = useState(false);
  const [selectedFileUrl, setSelectedFileUrl] = useState('');
  const [selectedFileName, setSelectedFileName] = useState('');
  const [selectedIdentifier, setSelectedIdentifier] = useState('');
  const [generatedIdentifier, setGeneratedIdentifier] = useState('');
  const [crossrefTitle, setCrossrefTitle] = useState('');
  const [loadingIdentifiers, setLoadingIdentifiers] = useState({});
  const [findingError, setFindingError] = useState(false);
  const [findingErrorText, setFindingErrorText] = useState('');
  const [cstrIdentifier, setCstrIdentifier] = useState('');

  // Effect to sync state with parent when formData changes
  useEffect(() => {
    if (formData) {
      if (formData.documentType !== selectedType) {
        setSelectedType(formData.documentType || '');
      }
      if (formData.files !== uploadedFiles) {
        setUploadedFiles(formData.files || []);
      }
    }
  }, [formData]);

  const getAcceptedFileTypes = (typeId) => {
    const documentType = documentTypes.find(dt => dt.id === typeId)?.type;
    if (!documentType) return '*/*';

    const typeMap = {
      'Video': 'video/*',
      'Audio': 'audio/*',
      'Datasets': '.csv,.xlsx,.json,.xml',
      'Image': 'image/*',
      'Gif': 'image/gif'
    };
    return typeMap[documentType] || '*/*';
  };

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
      label: 'CSTR',
      value: 4,
      disabled: true
    },
    {
      label: 'DOI',
      value: 5,
      disabled: true
    },
    {
      label: 'ARK Keys',
      value: 6,
      disabled: true
    },
    {
      label: 'ArXiv iD',
      value: 7,
      disabled: true
    },
    {
      label: 'Handle iD',
      value: 8,
      disabled: true
    },
    {
      label: 'Hand iD',
      value: 9,
      disabled: true
    },
    {
      label: 'dPID',
      value: 10,
      disabled: true
    },
    
  ]

  const getFileIcon = (type) => {
    const iconMap = {
      'Video': VideoIcon,
      'Audio': AudioIcon,
      'Datasets': DatasetIcon,
      'Image': ImageIcon,
      'Gif': GifIcon
    };
    const Icon = iconMap[type] || DatasetIcon;
    return <Icon />;
  };

  const handleTypeChange = (event) => {
    const newType = event.target.value;
    setSelectedType(newType);
    updateFormData({
      documentType: newType,
      files: uploadedFiles
    });
  };

  const validateFile = (file, typeId) => {
    const maxSize = 100 * 1024 * 1024; // 100MB max size
    if (file.size > maxSize) {
      return t('assign_docid.documents_form.file_size_error');
    }

    // Get the document type name from the ID
    const documentType = documentTypes.find(dt => dt.id === typeId)?.type;
    if (!documentType) {
      return 'Invalid document type';
    }

    const typeValidationMap = {
      'Video': file.type.startsWith('video/'),
      'Audio': file.type.startsWith('audio/'),
      'Datasets': ['.csv', '.xlsx', '.json', '.xml'].some(ext => 
        file.name.toLowerCase().endsWith(ext)),
      'Image': file.type.startsWith('image/') && !file.type.includes('gif'),
      'Gif': file.type === 'image/gif'
    };

    if (!typeValidationMap[documentType]) {
      return t('assign_docid.documents_form.invalid_type_error', { type: documentType });
    }

    return null;
  };

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    setError('');

    for (const file of files) {
      const validationError = validateFile(file, selectedType);
      if (validationError) {
        setError(validationError);
        return;
      }
    }

    const newFiles = files.map(file => ({
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: file.lastModified,
      file: file,
      url: URL.createObjectURL(file),
      metadata: {
        title: '',
        description: '',
        identifier: '',
        identifierType: '',
        generated_identifier: ''
      }
    }));

    const updatedFiles = [...uploadedFiles, ...newFiles];
    setUploadedFiles(updatedFiles);
    updateFormData({
      documentType: selectedType,
      files: updatedFiles
    });
  };

  const handleRemoveFile = (index) => {
    if (uploadedFiles[index].url) {
      URL.revokeObjectURL(uploadedFiles[index].url);
    }
    const updatedFiles = uploadedFiles.filter((_, i) => i !== index);
    setUploadedFiles(updatedFiles);
    updateFormData({
      documentType: selectedType,
      files: updatedFiles
    });
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handlePreview = (fileData) => {
    setSelectedFileUrl(fileData.url);
    setSelectedFileName(fileData.name);
    setPreviewOpen(true);
  };

  const handleClosePreview = () => {
    if (selectedFileUrl) {
      URL.revokeObjectURL(selectedFileUrl);
    }
    setPreviewOpen(false);
    setSelectedFileUrl('');
  };

  const handleMetadataChange = (index, field, value) => {
    const updatedFiles = [...uploadedFiles];
    updatedFiles[index].metadata[field] = value;
    setUploadedFiles(updatedFiles);
    updateFormData({
      documentType: selectedType,
      files: updatedFiles
    });
  };

  const handleIdentifierChange = async (index, value) => {
    console.log('handleIdentifierChange called with:', { index, value });
    setSelectedIdentifier(value);
    const selectedType = identifiers.find(type => type.value === value)?.label;
    console.log('Selected identifier type:', selectedType);
    
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
        const identifierValue = response.data.id;
        handleMetadataChange(index, 'identifier', value);
        handleMetadataChange(index, 'identifierType', value);
        handleMetadataChange(index, 'generated_identifier', identifierValue);
      } catch (error) {
        console.error('Error generating APA Handle iD:', error);
        setFindingError(true);
        setFindingErrorText(t('assign_docid.documents_form.errors.failed_apa_handle'));
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
        console.error('Error fetching Data Cite:', error);
        setFindingError(true);
        setFindingErrorText(t('assign_docid.documents_form.errors.failed_datacite'));
      } finally {
        setLoadingIdentifiers(prev => ({ ...prev, [index]: false }));
      }
    } else if (value === 3) { // Crossref
      // Reset states for CrossRef search
      setGeneratedIdentifier('');
      setCrossrefTitle('');
      setFindingError(false);
      handleMetadataChange(index, 'identifier', value);
      handleMetadataChange(index, 'identifierType', value);
      handleMetadataChange(index, 'generated_identifier', '');
    } else if (value === 4) { // CSTR PID
      console.log('CSTR PID selected, resetting states');
      setGeneratedIdentifier('');
      setCstrIdentifier('');
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
        setFindingErrorText(t('assign_docid.documents_form.errors.no_results_crossref'));
        return;
      }

      const identifierValue = response.data.data[0]?.DOI;
      if (identifierValue) {
        handleMetadataChange(index, 'generated_identifier', identifierValue);
        setGeneratedIdentifier(identifierValue);
      } else {
        setFindingError(true);
        setFindingErrorText(t('assign_docid.documents_form.errors.no_doi_crossref'));
      }
    } catch (error) {
      console.error('Error searching CrossRef:', error);
      setFindingError(true);
      setFindingErrorText(t('assign_docid.documents_form.errors.failed_crossref'));
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

  const generateCstr = async (index) => {
    if (!cstrIdentifier.trim()) return;
    
    console.log('Generating CSTR with identifier:', cstrIdentifier);
    setLoadingIdentifiers(prev => ({ ...prev, [index]: true }));
    setFindingError(false);

    try {
      const response = await axios.get(
        `/api/cstr/detail?identifier=${encodeURIComponent(cstrIdentifier)}`
      );

      console.log('CSTR API Response:', response.data);

      if (!response.data.data || !response.data.data.alternative_identifiers) {
        setFindingError(true);
        setFindingErrorText(t('assign_docid.documents_form.errors.no_results_cstr'));
        return;
      }

      const identifierValue = response.data.data.alternative_identifiers[0].identifier;
      console.log('Generated CSTR identifier:', identifierValue);
      
      if (identifierValue) {
        handleMetadataChange(index, 'generated_identifier', identifierValue);
        setGeneratedIdentifier(identifierValue);
      } else {
        setFindingError(true);
        setFindingErrorText(t('assign_docid.documents_form.errors.no_identifier_cstr'));
      }
    } catch (error) {
      console.error('Error searching CSTR:', error);
      setFindingError(true);
      setFindingErrorText(t('assign_docid.documents_form.errors.failed_cstr'));
    } finally {
      setLoadingIdentifiers(prev => ({ ...prev, [index]: false }));
    }
  };

  const cancelCstr = (index) => {
    setGeneratedIdentifier('');
    setCstrIdentifier('');
    handleMetadataChange(index, 'identifier', '');
    handleMetadataChange(index, 'identifierType', '');
    handleMetadataChange(index, 'generated_identifier', '');
  };

  const handleAddAnotherDocument = () => {
    // Don't reset the selectedType - this was causing the upload section to disappear
    // setSelectedType('');
    const fileInput = document.getElementById('document-upload');
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
        {t('assign_docid.documents_form.title')}
      </Typography>

      <Typography 
        variant="body1" 
        sx={{ 
          mb: 3,
          color: theme.palette.text.primary,
          fontWeight: 400,
          fontSize: '1rem'
        }}
      >
        {t('assign_docid.documents_form.subtitle')}
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>{t('assign_docid.documents_form.document_type')}</InputLabel>
            <Select
              value={selectedType}
              onChange={handleTypeChange}
              label={t('assign_docid.documents_form.document_type')}
              sx={{
                '& .MuiSelect-select': {
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }
              }}
            >
              {documentTypes.map(({ id, type, extensions, icon: Icon, enabled }) => (
                <MenuItem 
                  key={id} 
                  value={id}
                  disabled={!enabled}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    opacity: enabled ? 1 : 0.5,
                    '&.Mui-disabled': {
                      opacity: 0.5
                    }
                  }}
                >
                  <Icon sx={{ color: enabled ? '#1565c0' : '#9e9e9e' }} />
                  <Box>
                    <Typography>{type}</Typography>
                    <Typography variant="caption" color="textSecondary">
                      {t('assign_docid.documents_form.supported')} {extensions}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {error && (
          <Grid item xs={12}>
            <Alert severity="error">{error}</Alert>
          </Grid>
        )}

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
                id="document-upload"
                style={{ display: 'none' }}
                onChange={handleFileUpload}
                accept={getAcceptedFileTypes(selectedType)}
              />
              <label htmlFor="document-upload">
                <Button
                  component="span"
                  variant="contained"
                  startIcon={<UploadIcon />}
                  sx={{
                    bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.main,
                    color: 'white',
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    py: 1.5,
                    px: 4,
                   '&:hover': {
                      bgcolor: theme.palette.mode === 'dark' ? '#1c2552' : theme.palette.primary.dark
                    }
                  }}
                >
                  {t('assign_docid.documents_form.upload_files', { type: selectedType })}
                </Button>
              </label>
              <Typography variant="body2" sx={{ mt: 2, color: theme.palette.text.secondary }}>
                {t('assign_docid.documents_form.max_file_size')}
              </Typography>
            </Paper>
          </Grid>
        )}

        {uploadedFiles.map((file, index) => (
          <Grid item xs={12} key={index}>
            <Paper sx={{ p: 3, mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                {getFileIcon(selectedType)}
                <Box sx={{ flexGrow: 1, ml: 2 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                    {file.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {formatFileSize(file.size)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    startIcon={<PreviewIcon />}
                    onClick={() => handlePreview(file)}
                    variant="outlined"
                    size="small"
                  >
                    {t('assign_docid.documents_form.preview')}
                  </Button>
                  <Button
                    startIcon={<DeleteIcon />}
                    onClick={() => handleRemoveFile(index)}
                    variant="outlined"
                    color="error"
                    size="small"
                  >
                    {t('assign_docid.documents_form.remove')}
                  </Button>
                </Box>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label={t('assign_docid.documents_form.title_field')}
                    value={file.metadata.title}
                    onChange={(e) => handleMetadataChange(index, 'title', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label={t('assign_docid.documents_form.description_field')}
                    multiline
                    rows={3}
                    value={file.metadata.description}
                    onChange={(e) => handleMetadataChange(index, 'description', e.target.value)}
                  />
                </Grid>
                <Grid item xs={6}>
                  <FormControl fullWidth>
                    <InputLabel>{t('assign_docid.documents_form.identifier_type')}</InputLabel>
                    <Select
                      value={file.metadata.identifierType}
                      onChange={(e) => handleIdentifierChange(index, e.target.value)}
                      label={t('assign_docid.documents_form.identifier_type')}
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
                      <Typography variant="body2">{t('assign_docid.documents_form.generating_identifier')}</Typography>
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
                          label={t('assign_docid.documents_form.crossref_title_search')}
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
                            {t('assign_docid.documents_form.search_crossref')}
                          </Button>
                        ) : (
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <TextField
                              fullWidth
                              value={file.metadata.generated_identifier}
                              label={t('assign_docid.documents_form.generated_crossref_doi')}
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
                    ) : file.metadata.identifierType && identifiers.find(type => 
                      type.value === file.metadata.identifierType)?.label === 'CSTR PID' ? (
                        <Box>
                          <TextField
                            fullWidth
                            label={t('assign_docid.documents_form.cstr_identifier')}
                            value={cstrIdentifier}
                            onChange={(e) => setCstrIdentifier(e.target.value)}
                            sx={{ mb: 1 }}
                          />
                          {!file.metadata.generated_identifier ? (
                            <Button
                              variant="contained"
                              onClick={() => generateCstr(index)}
                              fullWidth
                              disabled={!cstrIdentifier.trim() || loadingIdentifiers[index]}
                            >
                              {t('assign_docid.documents_form.search_cstr')}
                            </Button>
                          ) : (
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <TextField
                                fullWidth
                                value={file.metadata.generated_identifier}
                                label={t('assign_docid.documents_form.generated_cstr_identifier')}
                                InputProps={{ readOnly: true }}
                              />
                              <Button
                                variant="outlined"
                                color="error"
                                onClick={() => cancelCstr(index)}
                              >
                                <CancelIcon />
                              </Button>
                            </Box>
                          )}
                        </Box>
                      ) : (
                        <TextField
                          fullWidth
                          label={t('assign_docid.documents_form.generated_identifier')}
                          value={file.metadata.generated_identifier || ''}
                          InputProps={{ readOnly: true }}
                        />
                      )}
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        ))}

        {uploadedFiles.length > 0 && (
          <Grid item xs={12}>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={handleAddAnotherDocument}
                  sx={{
                mt: 2,
                borderColor: '#4caf50',
                color: '#4caf50',
                '&:hover': {
                  borderColor: '#388e3c',
                  bgcolor: 'rgba(76, 175, 80, 0.04)'
                }
              }}
            >
              {t('assign_docid.documents_form.add_another_document')}
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
            bgcolor: 'background.paper',
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
            bgcolor: '#1565c0', 
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <Typography variant="h6" component="h2">
              {selectedFileName}
            </Typography>
            <IconButton
              onClick={handleClosePreview}
              sx={{ color: 'white' }}
            >
              <CloseIcon />
            </IconButton>
          </Box>
          <Box sx={{ height: 'calc(90vh - 64px)', width: '100%' }}>
            {selectedType === 'Image' || selectedType === 'Gif' ? (
              <Box
                component="img"
                src={selectedFileUrl}
                alt={selectedFileName}
                sx={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain'
                }}
              />
            ) : selectedType === 'Video' ? (
              <video
                src={selectedFileUrl}
                controls
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain'
                }}
              />
            ) : selectedType === 'Audio' ? (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <audio
                  src={selectedFileUrl}
                  controls
                  style={{ width: '100%', maxWidth: '500px' }}
                />
              </Box>
            ) : (
              <iframe
                src={selectedFileUrl}
                title="File Preview"
                width="100%"
                height="100%"
                style={{ border: 'none' }}
              />
            )}
          </Box>
        </Box>
      </Modal>
    </Box>
  );
};

export default DocumentsForm; 