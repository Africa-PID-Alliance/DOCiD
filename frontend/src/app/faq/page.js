import FaqPage from './FaqPage';

export const metadata = {
  title: 'Frequently Asked Questions – DOCiD™',
  description: 'Find answers to common questions about DOCiD™ (Digital Object Container Identifier), the persistent identifier and Handle framework developed by the Africa PID Alliance.',
  keywords: 'DOCiD FAQ, Digital Object Container Identifier, Africa PID Alliance, persistent identifiers, FAIR, CARE, open science, African research',
  openGraph: {
    title: 'FAQs – DOCiD™',
    description: 'Frequently Asked Questions about DOCiD™ and the Africa PID Alliance.',
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
  return <FaqPage />;
}
