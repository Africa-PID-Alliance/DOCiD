import MyAccountPage from './MyAccountPage';

export const metadata = {
  title: 'My Account',
  description: 'Manage your DOCiD™ account settings, profile information, and preferences. Update your personal details and security settings.',
  keywords: 'account settings, user profile, DOCiD account, profile management, security settings',
  openGraph: {
    title: 'My Account - DOCiD™',
    description: 'Manage your DOCiD™ account settings, profile information, and preferences. Update your personal details and security settings.',
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
  return <MyAccountPage />;
} 