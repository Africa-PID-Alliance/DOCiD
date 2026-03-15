"use client";

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Modal,
  TextField,
  IconButton,
  Paper,
  Grid,
  Divider,
  useTheme
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import CloseIcon from '@mui/icons-material/Close';

const CreatorsNationalIdForm = ({ formData = { creators: [] }, updateFormData }) => {
  const theme = useTheme();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [creators, setCreators] = useState(formData?.creators || []);
  const [newCreator, setNewCreator] = useState({
    name: '',
    nationalIdNumber: '',
    country: ''
  });
  const [errors, setErrors] = useState({});

  const handleModalOpen = () => {
    setIsModalOpen(true);
    setNewCreator({ name: '', nationalIdNumber: '', country: '' });
    setErrors({});
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setNewCreator({ name: '', nationalIdNumber: '', country: '' });
    setErrors({});
  };

  const handleInputChange = (field) => (event) => {
    setNewCreator((prev) => ({ ...prev, [field]: event.target.value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!newCreator.name.trim()) newErrors.name = 'Name is required';
    if (!newCreator.nationalIdNumber.trim()) newErrors.nationalIdNumber = 'National ID Number is required';
    if (!newCreator.country.trim()) newErrors.country = 'Country is required';
    return newErrors;
  };

  const handleAddCreator = () => {
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    const updatedCreators = [...creators, newCreator];
    setCreators(updatedCreators);
    updateFormData({ ...formData, creators: updatedCreators });
    handleModalClose();
  };

  const handleRemoveCreator = (index) => {
    const updatedCreators = creators.filter((_, i) => i !== index);
    setCreators(updatedCreators);
    updateFormData({ ...formData, creators: updatedCreators });
  };

  const readOnlyInputSx = {
    bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5'
  };

  const readOnlyFieldSx = {
    '& .MuiOutlinedInput-root': {
      '& fieldset': {
        borderColor:
          theme.palette.mode === 'dark'
            ? 'rgba(255, 255, 255, 0.23)'
            : theme.palette.divider
      }
    }
  };

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2
        }}
      >
        <Typography
          variant="h6"
          sx={{
            color: theme.palette.text.primary,
            fontWeight: 600,
            fontSize: '1.25rem'
          }}
        >
          Creators (National ID)
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleModalOpen}
          sx={{
            bgcolor: theme.palette.mode === 'dark' ? '#2e7d32' : '#4caf50',
            color: '#fff',
            '&:hover': {
              bgcolor: theme.palette.mode === 'dark' ? '#1b5e20' : '#388e3c'
            }
          }}
        >
          Add
        </Button>
      </Box>

      <Divider sx={{ mb: 3 }} />

      {creators && creators.length > 0 ? (
        <Box sx={{ width: '100%' }}>
          {creators.map((creator, index) => (
            <Paper
              key={index}
              elevation={1}
              sx={{
                mb: 2,
                borderRadius: 1,
                p: 3,
                position: 'relative',
                bgcolor: theme.palette.background.paper,
                border: `1px solid ${
                  theme.palette.mode === 'dark'
                    ? 'rgba(255, 255, 255, 0.23)'
                    : theme.palette.divider
                }`
              }}
            >
              <Box
                sx={{
                  mb: 3,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <Typography variant="h6" sx={{ color: theme.palette.primary.main }}>
                  Creator {index + 1}
                </Typography>
                <IconButton
                  onClick={() => handleRemoveCreator(index)}
                  sx={{
                    color: theme.palette.error.main,
                    '&:hover': { bgcolor: theme.palette.action.hover }
                  }}
                >
                  <DeleteIcon />
                </IconButton>
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Name"
                    value={creator.name}
                    InputProps={{ readOnly: true, sx: readOnlyInputSx }}
                    sx={readOnlyFieldSx}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="National ID Number"
                    value={creator.nationalIdNumber}
                    InputProps={{ readOnly: true, sx: readOnlyInputSx }}
                    sx={readOnlyFieldSx}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Country"
                    value={creator.country}
                    InputProps={{ readOnly: true, sx: readOnlyInputSx }}
                    sx={readOnlyFieldSx}
                  />
                </Grid>
              </Grid>
            </Paper>
          ))}
        </Box>
      ) : (
        <Typography
          variant="body2"
          sx={{ textAlign: 'center', py: 4, color: theme.palette.text.secondary }}
        >
          No creators added yet
        </Typography>
      )}

      {/* Add Creator Modal */}
      <Modal open={isModalOpen} onClose={handleModalClose} aria-labelledby="add-national-id-creator-modal">
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '90%',
            maxWidth: 600,
            bgcolor: theme.palette.background.paper,
            borderRadius: 1,
            boxShadow: 24,
            overflow: 'hidden'
          }}
        >
          <Box
            sx={{
              bgcolor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.main,
              p: 2,
              color: '#fff',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <Typography variant="h6" component="h2">
              Add Creator (National ID)
            </Typography>
            <IconButton onClick={handleModalClose} sx={{ color: '#fff' }}>
              <CloseIcon />
            </IconButton>
          </Box>

          <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Name"
                  value={newCreator.name}
                  onChange={handleInputChange('name')}
                  required
                  error={!!errors.name}
                  helperText={errors.name}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="National ID Number"
                  value={newCreator.nationalIdNumber}
                  onChange={handleInputChange('nationalIdNumber')}
                  required
                  error={!!errors.nationalIdNumber}
                  helperText={errors.nationalIdNumber}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Country"
                  value={newCreator.country}
                  onChange={handleInputChange('country')}
                  required
                  error={!!errors.country}
                  helperText={errors.country}
                />
              </Grid>
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  onClick={handleAddCreator}
                  fullWidth
                  sx={{ mt: 1 }}
                >
                  Add Creator
                </Button>
              </Grid>
            </Grid>
          </Box>
        </Box>
      </Modal>
    </Box>
  );
};

export default CreatorsNationalIdForm;
