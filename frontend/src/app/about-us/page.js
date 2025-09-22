import AboutDocid from './AboutDocid';

export const metadata = {
  title: 'About DOCiD™',
  description: 'Learn about DOCiD™ and our mission to advance digital object identification in Africa. Discover how we are pioneering hybrid digital object identification systems.',
  keywords: 'about DOCiD, Africa PID Alliance, digital object identifiers, scholarly infrastructure, hybrid identification, research infrastructure',
  openGraph: {
    title: 'About DOCiD™ - Africa PID Alliance',
    description: 'Learn about DOCiD™ and our mission to advance digital object identification in Africa. Discover how we are pioneering hybrid digital object identification systems.',
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
  return <AboutDocid/>;
} 