import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';

const Footer = () => {
  const { t } = useTranslation('common');
  return (
    <Box sx={{ padding: '20px 0', backgroundColor:"#141a3b", color: 'white', textAlign: 'center' }}>
      <Typography variant="body2" gutterBottom>
        &copy; {new Date().getFullYear()} DOCiD™. {t('footer.all_rights_reserved')}
      </Typography>
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
        <Link href="https://africapidalliance.org/privacy-policy" color="inherit" underline="hover">
          {t('footer.terms_and_conditions')}
        </Link>
        <Link href="https://africapidalliance.org/privacy-policy" color="inherit" underline="hover">
          {t('footer.privacy_policy')}
        </Link>
      </Box>
    </Box>
  );
};

export default Footer;