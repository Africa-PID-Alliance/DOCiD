import Link from 'next/link';
import { Container, Typography, Button, Box } from '@mui/material';

export default function NotFound() {
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
        <Typography variant="h1" component="h2" sx={{ fontSize: '4rem', fontWeight: 'bold' }}>
          404
        </Typography>
        <Typography variant="h4" component="h2">
          Page Not Found
        </Typography>
        <Typography variant="body1" color="text.secondary">
          The page you are looking for does not exist.
        </Typography>
        <Link href="/" passHref style={{ textDecoration: 'none' }}>
          <Button variant="contained" sx={{ mt: 2 }}>
            Return Home
          </Button>
        </Link>
      </Box>
    </Container>
  );
}