# DOCiD Platform

A comprehensive Document Identifier Management System providing persistent identifiers (PIDs) 

## Overview

DOCiD is a full-stack application that integrates with multiple external services including Crossref, CSTR, CORDRA, ROR, ORCID, and Local Contexts to provide a complete solution for managing scholarly publications and document identifiers.

## Project Structure

```
project/
├── backend/     # Flask REST API
│   ├── app/     # Application modules
│   ├── migrations/  # Database migrations
│   └── requirements.txt
├── frontend/    # Next.js Application
│   ├── src/     # React components
│   ├── public/  # Static assets
│   └── package.json
└── README.md
```

## Technology Stack

### Backend (Flask)
- **Framework**: Flask with PostgreSQL
- **Authentication**: JWT with social login integration
- **External Services**: Crossref, CORDRA, CSTR, ROR, ORCID
- **Persistent Identifiers**: DOI, DocID, Handle management

### Frontend (Next.js)
- **Framework**: Next.js 15.2.2
- **UI Library**: Material-UI (MUI)
- **State Management**: Redux Toolkit
- **Styling**: CSS Modules, SCSS

## Features

- **Publication Management**: Create, edit, and manage scholarly publications
- **Persistent Identifiers**: Handle DOIs, DocIDs, Handles, and other PIDs
- **Authentication**: Social login integration (Google, ORCID, GitHub)
- **External Services Integration**: Seamless integration with research infrastructure
- **Comments System**: Hierarchical commenting on publications
- **Multilingual Support**: i18n with multiple language options
- **API Documentation**: Swagger/OpenAPI via Flasgger

## Prerequisites

- Python 3.8+
- Node.js 18.x+
- PostgreSQL
- Redis (optional, for caching)

## Installation

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database:
```bash
python manage.py create-db
python manage.py seed-db
```

6. Run the backend:
```bash
python run.py
```

The API will be available at `http://localhost:5001`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

4. Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Production Deployment

### Backend
```bash
cd backend
gunicorn -c gunicorn.conf.py wsgi:app
```

### Frontend
```bash
cd frontend
npm run build
npm start
```

Or use PM2:
```bash
pm2 start ecosystem.config.js
```

## Environment Variables

### Backend (.env)
```
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/docid_db
SECRET_KEY=your_secret_key
CSTR_CLIENT_ID=cstr_client_id
CSTR_SECRET=cstr_secret
CROSSREF_API_URL=crossref_api_endpoint
CROSSREF_API_KEY=crossref_api_key
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:5001/api/v1
NEXT_PUBLIC_GOOGLE_CLIENT_ID=google_client_id
NEXT_PUBLIC_ORCID_CLIENT_ID=orcid_client_id
NEXT_PUBLIC_GITHUB_CLIENT_ID=github_client_id
```

## API Documentation

When the backend is running, API documentation is available at:
- Swagger UI: `http://localhost:5001/apidocs/`

## External Service Integration

The platform integrates with:
- **CORDRA**: Digital object repository with Handle generation
- **Crossref**: DOI metadata and registration
- **CSTR**: China Science and Technology Resource platform
- **ROR**: Research Organization Registry
- **ORCID**: Researcher identification
- **Local Contexts**: Cultural protocols and labels

## Developers

- Steve Gaikia <steveggaita@gmail.com>
- Erastus Kariuki <ekariz@gmail.com>

## License

[License Type]

## Support

For issues and questions, please create an issue in the GitHub repository.

## Acknowledgments

- Africa PID Alliance
- DOCiD Development Team
