'use client';

import { useEffect } from 'react';
import { Button, Container, Typography, Box } from '@mui/material';

export default function Error({ error, reset }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <Container>
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '50vh',
          textAlign: 'center',
          gap: 2,
        }}
      >
        <Typography variant="h4" component="h2">
          Something went wrong!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          An error occurred while loading this page.
        </Typography>
        <Button
          variant="contained"
          onClick={() => reset()}
          sx={{ mt: 2 }}
        >
          Try again
        </Button>
      </Box>
    </Container>
  );
}