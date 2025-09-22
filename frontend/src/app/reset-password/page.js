import ResetPasswordPage from './ResetPasswordPage';

export const metadata = {
  title: 'Reset Password',
  description: 'Reset your DOCiD™ account password securely. Follow the steps to regain access to your account and continue managing your digital objects.',
  keywords: 'reset password, forgot password, account recovery, DOCiD login help, password assistance',
  openGraph: {
    title: 'Reset Password - DOCiD™',
    description: 'Reset your DOCiD™ account password securely. Follow the steps to regain access to your account and continue managing your digital objects.',
    type: 'website',
    siteName: 'DOCiD™',
    locale: 'en_US',
    images: [
      {
        url: '/assets/images/Logo2.png',
        width: 220,
        height: 88,
        alt: 'DOCiD Logo',
      },
    ],
  },
};

export default function Page() {
  return <ResetPasswordPage />;
} 