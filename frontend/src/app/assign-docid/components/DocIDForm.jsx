"use client";

import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Button,
  IconButton,
  Paper,
  Divider,
  CircularProgress,
  useTheme
} from '@mui/material';
import { 
  VpnKey, 
  CloudUpload, 
  Delete, 
  FormatBold, 
  FormatItalic, 
  FormatUnderlined, 
  StrikethroughS,
  FormatColorText, 
  BorderColor,
  FormatListNumbered, 
  FormatListBulleted,
  Link as LinkIcon,
  Subscript, 
  Superscript,
  FormatAlignLeft, 
  FormatAlignCenter, 
  FormatAlignRight, 
  FormatAlignJustify
} from '@mui/icons-material';
import Image from 'next/image';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Heading from '@tiptap/extension-heading';
import TextStyle from '@tiptap/extension-text-style';
import FontFamily from '@tiptap/extension-font-family';
import TextAlign from '@tiptap/extension-text-align';
import Link from '@tiptap/extension-link';
import Underline from '@tiptap/extension-underline';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const fontFamilies = [
  { value: 'Inter', label: 'Inter' },
  { value: 'Arial', label: 'Arial' },
  { value: 'Georgia', label: 'Georgia' },
  { value: 'Times New Roman', label: 'Times New Roman' },
  { value: 'Helvetica', label: 'Helvetica' },
];

const MenuBar = ({ editor }) => {
  const theme = useTheme();
  const { t } = useTranslation();
  if (!editor) {
    return null;
  }

  return (
    <Box sx={{ 
      mb: 1, 
      display: 'flex',
      flexDirection: 'column',
      gap: 1,
      borderBottom: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.15)' : '#e0e0e0'}`,
      pb: 1
    }}>
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
        {/* Font Family Selector */}
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <Select
            value={editor.getAttributes('textStyle').fontFamily || 'Inter'}
            onChange={(e) => editor.chain().focus().setFontFamily(e.target.value).run()}
            sx={{ height: '32px' }}
          >
            {fontFamilies.map((font) => (
              <MenuItem 
                key={font.value} 
                value={font.value}
                sx={{ fontFamily: font.value }}
              >
                {font.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Divider orientation="vertical" flexItem />

        {/* Heading Options */}
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <Select
            value={editor.isActive('paragraph') ? 'paragraph' : editor.isActive('heading') ? `h${editor.getAttributes('heading').level}` : 'paragraph'}
            onChange={(e) => {
              if (e.target.value === 'paragraph') {
                editor.chain().focus().setParagraph().run();
              } else {
                editor.chain().focus().toggleHeading({ level: parseInt(e.target.value.slice(1)) }).run();
              }
            }}
            sx={{ height: '32px' }}
          >
            <MenuItem value="paragraph">{t('assign_docid.docid_form.editor.paragraph')}</MenuItem>
            <MenuItem value="h1">{t('assign_docid.docid_form.editor.heading_1')}</MenuItem>
            <MenuItem value="h2">{t('assign_docid.docid_form.editor.heading_2')}</MenuItem>
            <MenuItem value="h3">{t('assign_docid.docid_form.editor.heading_3')}</MenuItem>
            <MenuItem value="h4">{t('assign_docid.docid_form.editor.heading_4')}</MenuItem>
            <MenuItem value="h5">{t('assign_docid.docid_form.editor.heading_5')}</MenuItem>
          </Select>
        </FormControl>

        <Divider orientation="vertical" flexItem />

        {/* Basic Text Formatting */}
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleBold().run()}
            color={editor.isActive('bold') ? 'primary' : 'default'}
            sx={{
              bgcolor: editor.isActive('bold') ? 'action.selected' : 'transparent',
            }}
          >
            <FormatBold />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleItalic().run()}
            color={editor.isActive('italic') ? 'primary' : 'default'}
            sx={{
              bgcolor: editor.isActive('italic') ? 'action.selected' : 'transparent',
            }}
          >
            <FormatItalic />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.commands.toggleUnderline()}
            color={editor.isActive('underline') ? 'primary' : 'default'}
            sx={{
              bgcolor: editor.isActive('underline') ? 'action.selected' : 'transparent',
            }}
          >
            <FormatUnderlined />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleStrike().run()}
            color={editor.isActive('strike') ? 'primary' : 'default'}
            sx={{
              bgcolor: editor.isActive('strike') ? 'action.selected' : 'transparent',
            }}
          >
            <StrikethroughS />
          </IconButton>
        </Box>

        <Divider orientation="vertical" flexItem />

        {/* Color Controls - Disabled Placeholders */}
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            disabled
title={t('assign_docid.docid_form.editor.text_color')}
            sx={{ color: theme.palette.text.disabled }}
          >
            <FormatColorText />
          </IconButton>
          <IconButton
            size="small"
            disabled
title={t('assign_docid.docid_form.editor.highlight_color')}
            sx={{ color: theme.palette.text.disabled }}
          >
            <BorderColor />
          </IconButton>
        </Box>

        <Divider orientation="vertical" flexItem />

        {/* Lists */}
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            color={editor.isActive('bulletList') ? 'primary' : 'default'}
            sx={{
              bgcolor: editor.isActive('bulletList') ? 'action.selected' : 'transparent',
            }}
          >
            <FormatListBulleted />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            color={editor.isActive('orderedList') ? 'primary' : 'default'}
            sx={{
              bgcolor: editor.isActive('orderedList') ? 'action.selected' : 'transparent',
            }}
          >
            <FormatListNumbered />
          </IconButton>
        </Box>

        <Divider orientation="vertical" flexItem />

        {/* Link */}
        <IconButton
          size="small"
          onClick={() => {/* TODO: Implement link dialog */}}
          color={editor.isActive('link') ? 'primary' : 'default'}
          sx={{
            bgcolor: editor.isActive('link') ? 'action.selected' : 'transparent',
          }}
        >
          <LinkIcon />
        </IconButton>

        <Divider orientation="vertical" flexItem />

        {/* Subscript/Superscript */}
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleSubscript().run()}
            color={editor.isActive('subscript') ? 'primary' : 'default'}
            sx={{
              bgcolor: editor.isActive('subscript') ? 'action.selected' : 'transparent',
            }}
          >
            <Subscript />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleSuperscript().run()}
            color={editor.isActive('superscript') ? 'primary' : 'default'}
            sx={{
              bgcolor: editor.isActive('superscript') ? 'action.selected' : 'transparent',
            }}
          >
            <Superscript />
          </IconButton>
        </Box>

        <Divider orientation="vertical" flexItem />

        {/* Text Alignment */}
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().setTextAlign('left').run()}
            color={editor.isActive({ textAlign: 'left' }) ? 'primary' : 'default'}
            sx={{
              bgcolor: editor.isActive({ textAlign: 'left' }) ? 'action.selected' : 'transparent',
            }}
          >
            <FormatAlignLeft />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().setTextAlign('center').run()}
            color={editor.isActive({ textAlign: 'center' }) ? 'primary' : 'default'}
            sx={{
              bgcolor: editor.isActive({ textAlign: 'center' }) ? 'action.selected' : 'transparent',
            }}
          >
            <FormatAlignCenter />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().setTextAlign('right').run()}
            color={editor.isActive({ textAlign: 'right' }) ? 'primary' : 'default'}
            sx={{
              bgcolor: editor.isActive({ textAlign: 'right' }) ? 'action.selected' : 'transparent',
            }}
          >
            <FormatAlignRight />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().setTextAlign('justify').run()}
            color={editor.isActive({ textAlign: 'justify' }) ? 'primary' : 'default'}
            sx={{
              bgcolor: editor.isActive({ textAlign: 'justify' }) ? 'action.selected' : 'transparent',
            }}
          >
            <FormatAlignJustify />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
};

const DocIDForm = ({ formData, updateFormData }) => {
  const theme = useTheme();
  const { t } = useTranslation();
  const [isGenerated, setIsGenerated] = useState(false);
  const [thumbnail, setThumbnail] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [resourceTypes, setResourceTypes] = useState([]);
  const [isLoadingTypes, setIsLoadingTypes] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: false,
      }),
      TextStyle.configure({ types: ['textStyle'] }),
      FontFamily.configure({
        types: ['textStyle'],
      }),
      Heading.configure({
        levels: [1, 2, 3, 4, 5]
      }),
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      Link.configure({
        openOnClick: false,
      }),
      Underline.configure()
    ],
    content: formData?.description || '',
    onUpdate: ({ editor }) => {
      const html = editor.getHTML();
      handleInputChange({ target: { name: 'description', value: html } });
    },
  });

  useEffect(() => {
    if (formData?.generatedId) {
      setIsGenerated(true);
    }
  }, [formData]);

  // Cleanup preview URL when component unmounts
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // Fetch resource types
  useEffect(() => {
    const fetchResourceTypes = async () => {
      try {
        const response = await axios.get('/api/publications/get-list-resource-types');
        setResourceTypes(response.data);
      } catch (error) {
        console.error('Error fetching resource types:', error);
      } finally {
        setIsLoadingTypes(false);
      }
    };
    fetchResourceTypes();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    const updatedData = {
      ...formData,
      [name]: value
    };
    updateFormData(updatedData);
  };

  const handleThumbnailChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Create preview URL
      const objectUrl = URL.createObjectURL(file);
      setPreviewUrl(objectUrl);
      setThumbnail(file);
      updateFormData({
        ...formData,
        thumbnail: file
      });
    }
  };

  const handleRemoveThumbnail = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setThumbnail(null);
    updateFormData({
      ...formData,
      thumbnail: null
    });
  };

  const generateDocId = async () => {
    const normalizedDescriptionContent = formData.description === "<p><br></p>" ? "" : formData.description;

    if (!formData.title) {
      alert(t('assign_docid.docid_form.alerts.enter_title'));
      return;
    }
    if (!normalizedDescriptionContent) {
      alert(t('assign_docid.docid_form.alerts.enter_description'));
      return;
    }

    setIsGenerating(true);
    try {
      const url = '/api/cordoi/assign-doi/container-id';
      const payload = {
        title: formData.title,
        description: formData.description
      };

      const response = await axios.post(url, payload, {
        headers: {
          "Content-Type": "application/json"
        }
      });
console.log(response.data);
      const docId = response.data.data.id;
      const updatedData = {
        ...formData,
        generatedId: docId
      };
      
      updateFormData(updatedData);
      setIsGenerated(true);
    } catch (error) {
      console.error('Error generating DOCiD:', error);
      alert(t('assign_docid.docid_form.alerts.failed_generate'));
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Box>
      <Typography 
        variant="h6" 
        sx={{ 
          mb: 1,
          color: theme.palette.text.primary,
          fontWeight: 600,
          fontSize: '1.25rem'
        }}
      >
        {t('assign_docid.docid_form.title')}
      </Typography>
      <Typography
        variant="body2"
        sx={{ 
          mb: 3,
          color: theme.palette.text.secondary,
          fontWeight: 400,
          fontSize: '1rem'
        }}
      >
        {t('assign_docid.docid_form.subtitle')}
      </Typography>
      <Grid container spacing={3}>
        {/* Resource Type - First */}
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel 
              sx={{ 
                fontSize: '1.1rem',
                fontWeight: 600,
                color: theme.palette.text.primary
              }}
            >
              {t('assign_docid.docid_form.resource_type')}
            </InputLabel>
            <Select
              name="resourceType"
              value={formData.resourceType}
              onChange={handleInputChange}
              label="Resource Type"
              required
              sx={{
                fontSize: '1.1rem',
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
                  {t('assign_docid.docid_form.loading_types')}
                </MenuItem>
              ) : (
                resourceTypes.map((type) => (
                  <MenuItem key={type.id} value={type.id}>
                    {type.resource_type}
                  </MenuItem>
                ))
              )}
            </Select>
          </FormControl>
        </Grid>

        {/* Title - Second */}
        <Grid item xs={12}>
          <TextField
            fullWidth
label={t('assign_docid.docid_form.title_field')}
            name="title"
            required
            value={formData.title}
            onChange={handleInputChange}
            variant="outlined"
            sx={{
              '& .MuiInputLabel-root': {
                fontSize: '1.1rem',
                fontWeight: 600,
                color: theme.palette.text.primary
              },
              '& .MuiOutlinedInput-root': {
                fontSize: '1.1rem',
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

        {/* Description - Third - Now using TipTap */}
        <Grid item xs={12}>
          <Typography
            sx={{
              fontSize: '1.1rem',
              fontWeight: 600,
              color: theme.palette.text.primary,
              mb: 1
            }}
          >
            {t('assign_docid.docid_form.description')}
          </Typography>
          <Paper
            variant="outlined"
            sx={{
              p: 2,
              backgroundColor: theme.palette.background.paper,
              border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider}`,
              '&:hover': {
                borderColor: theme.palette.primary.main
              }
            }}
          >
            <MenuBar editor={editor} />
            <EditorContent 
              editor={editor}
              style={{
                minHeight: '200px',
                '& .ProseMirror': {
                  minHeight: '200px',
                  outline: 'none',
                  fontSize: '1.1rem',
                  color: theme.palette.text.primary,
                  padding: '16px 8px'
                },
                '& .ProseMirror p.isEditorEmpty:firstChild::before': {
                  content: 'attr(data-placeholder)',
                  color: theme.palette.text.disabled,
                  float: 'left',
                  height: 0,
                  pointerEvents: 'none'
                }
              }}
            />
          </Paper>
        </Grid>

        {/* Generate DOCiD Button - Only show if not generated */}
        {!isGenerated && (
        <Grid item xs={12} sx={{ mt: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <Button
              variant="contained"
              startIcon={!isGenerating && <VpnKey />}
              onClick={generateDocId}
              disabled={isGenerating}
              sx={{
                bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.main,
                color: '#fff',
                fontSize: '1.1rem',
                fontWeight: 600,
                py: 1.5,
                px: 4,
                '&:hover': {
                  bgcolor: theme.palette.mode === 'dark' ? '#1c2552' : theme.palette.primary.dark
                }
              }}
            >
              {isGenerating ? (
                <>
                  {t('assign_docid.docid_form.generating')} <CircularProgress size={20} thickness={2} sx={{ ml: 1, color: 'inherit' }} />
                </>
              ) : (
                t('assign_docid.docid_form.generate_button')
              )}
            </Button>
          </Box>
        </Grid>
        )}

        {/* Generated DOCiD Field - Show when generated */}
        {isGenerated && (
          <>
        <Grid item xs={12}>
            <TextField
              fullWidth
label={t('assign_docid.docid_form.generated_docid')}
              value={formData.generatedId}
              InputProps={{
                readOnly: true,
              }}
              variant="outlined"
              sx={{
                '& .MuiInputLabel-root': {
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  color: theme.palette.text.primary
                },
                '& .MuiOutlinedInput-root': {
                  fontSize: '1.1rem',
                  bgcolor: theme.palette.action.hover,
                  '& fieldset': {
                    borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.primary.main
                  },
                  '&:hover fieldset': {
                    borderColor: theme.palette.primary.main
                  }
                }
              }}
            />
            </Grid>

            {/* Thumbnail Upload - Only show after ID generation */}
            <Grid item xs={12}>
              <Typography
                variant="subtitle1"
                sx={{
                  mb: 2,
                  color: theme.palette.text.secondary,
                  fontWeight: 500
                }}
              >
                {t('assign_docid.docid_form.upload_thumbnail')}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Button
                  component="label"
                  variant="outlined"
                  startIcon={<CloudUpload />}
                  sx={{
                    borderColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider,
                    color: theme.palette.text.primary,
                    '&:hover': {
                      borderColor: theme.palette.primary.main,
                      bgcolor: theme.palette.action.hover
                    }
                  }}
                >
                  {t('assign_docid.docid_form.choose_image')}
                  <input
                    type="file"
                    hidden
                    accept="image/*"
                    onChange={handleThumbnailChange}
                  />
                </Button>
                {thumbnail && (
                  <Typography variant="body2" sx={{ color: theme.palette.text.primary }}>
                    {thumbnail.name}
                  </Typography>
                )}
              </Box>

              {/* Image Preview */}
              {previewUrl && (
                <Box sx={{ mt: 2, position: 'relative', width: 'fit-content' }}>
                  <Paper 
                    elevation={2}
                    sx={{ 
                      p: 1,
                      borderRadius: 2,
                      position: 'relative',
                      width: 'fit-content',
                      bgcolor: theme.palette.background.paper
                    }}
                  >
                    <Box
                      sx={{
                        width: '200px',
                        height: '200px',
                        position: 'relative',
                        overflow: 'hidden',
                        borderRadius: 1
                      }}
                    >
                      <Image
                        src={previewUrl}
                        alt="Thumbnail preview"
                        fill
                        style={{ objectFit: 'cover' }}
                      />
                    </Box>
                    <IconButton
                      onClick={handleRemoveThumbnail}
                      sx={{
                        position: 'absolute',
                        top: -16,
                        right: -16,
                        bgcolor: theme.palette.background.paper,
                        boxShadow: theme.shadows[1],
                        '&:hover': {
                          bgcolor: theme.palette.action.hover
                        }
                      }}
                    >
                      <Delete />
                    </IconButton>
                  </Paper>
                </Box>
          )}
        </Grid>
          </>
        )}
      </Grid>
    </Box>
  );
};

export default DocIDForm; 