import ClientWrapper from './ClientWrapper';
import { Providers } from './providers';

export const metadata = {
  title: {
    default: 'DOCiD™ APP',
    template: '%s | DOCiD™ APP'
  },
  description: 'DOCiD™ is a Document Identification System for managing and tracking digital objects',
  keywords: 'DOCiD, document management, digital objects, identification system',
  authors: [{ name: 'Africa PID Alliance' }],
  openGraph: {
    title: 'DOCiD™ APP',
    description: 'DOCiD™ is a Document Identification System for managing and tracking digital objects',
    type: 'website',
    siteName: 'DOCiD™',
    locale: 'en_US',
  },
  robots: {
    index: true,
    follow: true,
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
  },
  icons: {
    icon: '/favicon.ico',
  },
  verification: {
    google: 'google-site-verification',
  },
  alternates: {
    canonical: 'https://docid.africa',
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body suppressHydrationWarning={true}>
        <ClientWrapper>
          {children}
        </ClientWrapper>
      </body>
    </html>
  );
} 