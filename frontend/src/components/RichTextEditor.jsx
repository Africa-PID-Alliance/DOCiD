"use client";

import React, { useEffect } from 'react';
import {
  Box,
  FormControl,
  Select,
  MenuItem,
  Typography,
  IconButton,
  Paper,
  Divider,
  useTheme,
} from '@mui/material';
import {
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
  FormatAlignJustify,
} from '@mui/icons-material';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Heading from '@tiptap/extension-heading';
import TextStyle from '@tiptap/extension-text-style';
import FontFamily from '@tiptap/extension-font-family';
import TextAlign from '@tiptap/extension-text-align';
import Link from '@tiptap/extension-link';
import Underline from '@tiptap/extension-underline';
import { useTranslation } from 'react-i18next';

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

        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleBold().run()}
            color={editor.isActive('bold') ? 'primary' : 'default'}
            sx={{ bgcolor: editor.isActive('bold') ? 'action.selected' : 'transparent' }}
          >
            <FormatBold />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleItalic().run()}
            color={editor.isActive('italic') ? 'primary' : 'default'}
            sx={{ bgcolor: editor.isActive('italic') ? 'action.selected' : 'transparent' }}
          >
            <FormatItalic />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.commands.toggleUnderline()}
            color={editor.isActive('underline') ? 'primary' : 'default'}
            sx={{ bgcolor: editor.isActive('underline') ? 'action.selected' : 'transparent' }}
          >
            <FormatUnderlined />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleStrike().run()}
            color={editor.isActive('strike') ? 'primary' : 'default'}
            sx={{ bgcolor: editor.isActive('strike') ? 'action.selected' : 'transparent' }}
          >
            <StrikethroughS />
          </IconButton>
        </Box>

        <Divider orientation="vertical" flexItem />

        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton size="small" disabled title={t('assign_docid.docid_form.editor.text_color')} sx={{ color: theme.palette.text.disabled }}>
            <FormatColorText />
          </IconButton>
          <IconButton size="small" disabled title={t('assign_docid.docid_form.editor.highlight_color')} sx={{ color: theme.palette.text.disabled }}>
            <BorderColor />
          </IconButton>
        </Box>

        <Divider orientation="vertical" flexItem />

        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            color={editor.isActive('bulletList') ? 'primary' : 'default'}
            sx={{ bgcolor: editor.isActive('bulletList') ? 'action.selected' : 'transparent' }}
          >
            <FormatListBulleted />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            color={editor.isActive('orderedList') ? 'primary' : 'default'}
            sx={{ bgcolor: editor.isActive('orderedList') ? 'action.selected' : 'transparent' }}
          >
            <FormatListNumbered />
          </IconButton>
        </Box>

        <Divider orientation="vertical" flexItem />

        <IconButton
          size="small"
          onClick={() => {/* TODO: Implement link dialog */}}
          color={editor.isActive('link') ? 'primary' : 'default'}
          sx={{ bgcolor: editor.isActive('link') ? 'action.selected' : 'transparent' }}
        >
          <LinkIcon />
        </IconButton>

        <Divider orientation="vertical" flexItem />

        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleSubscript().run()}
            color={editor.isActive('subscript') ? 'primary' : 'default'}
            sx={{ bgcolor: editor.isActive('subscript') ? 'action.selected' : 'transparent' }}
          >
            <Subscript />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleSuperscript().run()}
            color={editor.isActive('superscript') ? 'primary' : 'default'}
            sx={{ bgcolor: editor.isActive('superscript') ? 'action.selected' : 'transparent' }}
          >
            <Superscript />
          </IconButton>
        </Box>

        <Divider orientation="vertical" flexItem />

        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().setTextAlign('left').run()}
            color={editor.isActive({ textAlign: 'left' }) ? 'primary' : 'default'}
            sx={{ bgcolor: editor.isActive({ textAlign: 'left' }) ? 'action.selected' : 'transparent' }}
          >
            <FormatAlignLeft />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().setTextAlign('center').run()}
            color={editor.isActive({ textAlign: 'center' }) ? 'primary' : 'default'}
            sx={{ bgcolor: editor.isActive({ textAlign: 'center' }) ? 'action.selected' : 'transparent' }}
          >
            <FormatAlignCenter />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().setTextAlign('right').run()}
            color={editor.isActive({ textAlign: 'right' }) ? 'primary' : 'default'}
            sx={{ bgcolor: editor.isActive({ textAlign: 'right' }) ? 'action.selected' : 'transparent' }}
          >
            <FormatAlignRight />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().setTextAlign('justify').run()}
            color={editor.isActive({ textAlign: 'justify' }) ? 'primary' : 'default'}
            sx={{ bgcolor: editor.isActive({ textAlign: 'justify' }) ? 'action.selected' : 'transparent' }}
          >
            <FormatAlignJustify />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
};

const RichTextEditor = ({ value, onChange, label = 'Description', minHeight = 200 }) => {
  const theme = useTheme();

  const editor = useEditor({
    extensions: [
      StarterKit.configure({ heading: false }),
      TextStyle.configure({ types: ['textStyle'] }),
      FontFamily.configure({ types: ['textStyle'] }),
      Heading.configure({ levels: [1, 2, 3, 4, 5] }),
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Link.configure({ openOnClick: false }),
      Underline.configure(),
    ],
    content: value || '',
    onUpdate: ({ editor: ed }) => {
      onChange?.(ed.getHTML());
    },
  });

  // Reactively sync external value changes (e.g. async API hydration) into the
  // editor without firing onUpdate (which would re-trigger setState → loop).
  useEffect(() => {
    if (!editor) return;
    const incoming = value || '';
    if (incoming !== editor.getHTML()) {
      editor.commands.setContent(incoming, false);
    }
  }, [value, editor]);

  return (
    <Box>
      {label && (
        <Typography variant="caption" sx={{ color: theme.palette.text.secondary, ml: 0.5, mb: 0.5, display: 'block' }}>
          {label}
        </Typography>
      )}
      <Paper
        variant="outlined"
        sx={{
          p: 2,
          backgroundColor: theme.palette.background.paper,
          border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : theme.palette.divider}`,
          '&:hover': { borderColor: theme.palette.primary.main },
        }}
      >
        <MenuBar editor={editor} />
        <EditorContent
          editor={editor}
          style={{
            minHeight: `${minHeight}px`,
            '& .ProseMirror': {
              minHeight: `${minHeight}px`,
              outline: 'none',
              fontSize: '1.1rem',
              color: theme.palette.text.primary,
              padding: '16px 8px',
            },
          }}
        />
      </Paper>
    </Box>
  );
};

export default RichTextEditor;
