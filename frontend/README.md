# DOCiD Frontend

A Next.js-based frontend application for the DOCiD (Document Identifier) platform - a comprehensive publication and document identifier management system.

## Overview

DOCiD Frontend provides a modern web interface for managing scholarly publications, persistent identifiers (PIDs), and metadata management with extensive integration to external services including Crossref, CSTR, CORDRA, ROR, ORCID, and Local Contexts.

## Features

- **Publication Management**: Create, edit, and manage scholarly publications
- **Persistent Identifiers**: Handle DOIs, DocIDs, Handles, and other PIDs
- **Authentication**: Social login integration (Google, ORCID, GitHub)
- **External Services**: Seamless integration with research infrastructure
- **Multilingual Support**: i18n with multiple language options
- **Comments System**: Hierarchical commenting on publications
- **Responsive Design**: Mobile-friendly interface

## Tech Stack

- **Framework**: Next.js 15.2.2
- **UI Library**: Material-UI (MUI)
- **State Management**: Redux Toolkit
- **Styling**: CSS Modules, SCSS
- **Authentication**: JWT-based with social auth
- **API Integration**: RESTful API client

## Prerequisites

- Node.js 18.x or higher
- npm or yarn
- Backend API running (DOCiD Backend)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd docid-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env.local
```

Edit `.env.local` with your configuration:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:5001/api/v1
# Add other required environment variables
```

## Development

Run the development server:

```bash
npm run dev
# or
./run.sh
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Production Deployment

### Building for Production

1. Create production build package:
```bash
./deploy.sh
```

This creates a timestamped deployment package (e.g., `docid-frontend-YYYYMMDD_HHMMSS.zip`).

### Deploying to Server

1. Upload the deployment package to your server
2. Extract the package:
```bash
unzip docid-frontend-*.zip
```
3. Run the deployment script:
```bash
./deploy-server.sh
```

Or manually:
```bash
npm ci --omit=dev
npm start
```

### PM2 Deployment

For production, we recommend using PM2:

```bash
pm2 start ecosystem.config.js
```

## Project Structure

```
├── src/
│   ├── app/              # Next.js app directory
│   │   ├── api/          # API routes
│   │   ├── assign-docid/ # DocID assignment pages
│   │   ├── login/        # Authentication pages
│   │   └── ...
│   ├── components/       # Reusable components
│   ├── redux/           # Redux store and slices
│   └── utils/           # Utility functions
├── public/              # Static assets
│   ├── locales/        # i18n translation files
│   └── docs/           # Documentation
├── deploy.sh           # Build deployment package
└── deploy-server.sh    # Server deployment script
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## API Integration

The frontend connects to the DOCiD backend API. Default endpoints:
- Development: `http://localhost:5001/api/v1`
- Production: `https://docid.africapidalliance.org/api/v1`

## Environment Variables

Key environment variables:

- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL
- `NEXT_PUBLIC_GOOGLE_CLIENT_ID` - Google OAuth client ID
- `NEXT_PUBLIC_ORCID_CLIENT_ID` - ORCID OAuth client ID
- `NEXT_PUBLIC_GITHUB_CLIENT_ID` - GitHub OAuth client ID

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions, please create an issue in the GitHub repository.

## Developers

- Steve Gaikia <steveggaita@gmail.com>
- Erastus Kariuki <ekariz@gmail.com>

## Acknowledgments

- Africa PID Alliance
- DOCiD Development Team