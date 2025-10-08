'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Card,
  CardContent,
  Typography,
  Box,
  useTheme,
  useMediaQuery
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useDispatch } from 'react-redux';
import { setLanguage } from '@/redux/slices/authSlice';

const languages = [
  { 
    code: 'en', 
    name: 'English',
    selectText: 'Select this as your preferred language'
  },
  { 
    code: 'fr', 
    name: 'Français',
    selectText: 'Sélectionner comme langue préférée'
  },
  { 
    code: 'sw', 
    name: 'Kiswahili',
    selectText: 'Chagua hii kama lugha unayopendelea'
  },
  { 
    code: 'ar', 
    name: 'العربية',
    selectText: 'اختر هذه كلغتك المفضلة'
  },
  { 
    code: 'pt', 
    name: 'Português',
    selectText: 'Selecionar como idioma preferido'
  },
  { 
    code: 'de', 
    name: 'Deutsch',
    selectText: 'Als bevorzugte Sprache auswählen'
  }
];

export default function LanguageSelectionModal() {
  const { t, i18n } = useTranslation();
  const dispatch = useDispatch();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [open, setOpen] = useState(false);

  useEffect(() => {
    // Check if user has previously selected a language (i18next stores this automatically)
    const storedLanguage = localStorage.getItem('i18nextLng');
    
    // Show modal only if no language is stored in localStorage
    if (!storedLanguage) {
      setOpen(true);
    }
  }, []);

  const handleLanguageSelect = (languageCode) => {
    // Set the language (i18next automatically stores this in localStorage as 'i18nextLng')
    i18n.changeLanguage(languageCode);
    
    // Dispatch to Redux store if needed
    dispatch(setLanguage(languageCode));
    
    // Close the modal
    setOpen(false);
  };

  const handleClose = () => {
    // If user closes without selecting, default to English
    if (!localStorage.getItem('i18nextLng')) {
      i18n.changeLanguage('en');
    }
    setOpen(false);
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          background: 'white',
          color: 'text.primary',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)'
        }
      }}
    >
      <DialogTitle sx={{ textAlign: 'center', pb: 1, pt: 2 }}>
        <Typography variant="h6" component="h1" sx={{ fontWeight: 'bold', mb: 0.5, color: 'primary.main' }}>
          {t('language_modal.welcome')}
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          {t('language_modal.select_language')}
        </Typography>
      </DialogTitle>
      
      <DialogContent sx={{ px: 2, py: 0.5 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {languages.map((language) => (
            <Card
              key={language.code}
              sx={{
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                background: 'white',
                border: '1px solid #e0e0e0',
                width: '100%',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  border: '1px solid #1976d2',
                  boxShadow: '0 4px 12px rgba(25, 118, 210, 0.15)'
                }
              }}
              onClick={() => handleLanguageSelect(language.code)}
            >
              <CardContent sx={{ textAlign: 'center', py: 1.5, px: 1.5 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: 'text.primary', mb: 0.5 }}>
                  {language.name}
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                  {language.selectText}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      </DialogContent>
      
      <DialogActions sx={{ justifyContent: 'center', pb: 1.5, pt: 0.5 }}>
        <Button
          onClick={handleClose}
          variant="outlined"
          size="small"
          sx={{
            color: 'text.secondary',
            borderColor: '#e0e0e0',
            fontSize: '0.8rem',
            py: 0.5,
            px: 2,
            '&:hover': {
              borderColor: '#1976d2',
              color: '#1976d2',
              background: 'rgba(25, 118, 210, 0.04)'
            }
          }}
        >
          {t('language_modal.continue_english')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
