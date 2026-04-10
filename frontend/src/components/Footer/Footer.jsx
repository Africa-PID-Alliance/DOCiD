'use client';

import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import { useTenant } from '@/context/TenantContext';

const Footer = () => {
  const { t } = useTranslation('common');
  const tenant = useTenant();
  const currentYear = new Date().getFullYear();
  // Strip any leading "© " from the tenant config so we can always
  // render "© {year} {name}" in a consistent format.
  const entityName =
    (tenant?.footer_copyright || 'DOCiD™').replace(/^©\s*/, '').trim() ||
    'DOCiD™';
  const copyrightText = `© ${currentYear} ${entityName}`;

  return (
    <Box sx={{ padding: '20px 0', backgroundColor: '#141a3b', color: 'white', textAlign: 'center' }}>
      <Typography variant="body2" gutterBottom>
        {copyrightText}. {t('footer.all_rights_reserved')}
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
