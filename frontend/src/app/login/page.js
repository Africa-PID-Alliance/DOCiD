import LoginPage from './LoginPage';

export const metadata = {
  title: 'Login',
  description: 'Sign in to your DOCiD™ account to manage your digital object identifiers and documents',
  keywords: 'login, sign in, DOCiD authentication, user access, document management',
  openGraph: {
    title: 'Login to DOCiD™',
    description: 'Sign in to your DOCiD™ account to manage your digital object identifiers and documents',
    type: 'website',
    siteName: 'DOCiD™',
    locale: 'en_US',
    images: [
      {
        url: '/assets/images/logo2.png',
        width: 220,
        height: 88,
        alt: 'DOCiD Logo',
      },
    ],
  },
};

export default function Page() {
  return <LoginPage />;
} 