# DOCiD Frontend Setup & Development Instructions

## Prerequisites

Before you begin, ensure you have the following installed:
- **Node.js** (v18.0.0 or higher recommended)
- **npm** or **yarn** package manager
- **Git** for version control

## Initial Setup

### 1. Clone the Repository (if not already done)
```bash
git clone [repository-url]
cd /Users/ekariz/Projects/AMBAND/DOCiD/frontendv2/docid
```

### 2. Install Dependencies
```bash
npm install
# or
yarn install
```

### 3. Environment Configuration

Create a `.env.local` file in the root directory with the following variables:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:5001/api/v1
NEXT_PUBLIC_BASE_URL=http://localhost:3000

# Server Configuration
PORT=5000
NEXT_PUBLIC_SERVER_URL=http://localhost:5000

# Authentication
JWT_SECRET=your-secret-key-here
JWT_EXPIRES_IN=24h

# OAuth Credentials (Optional)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
ORCID_CLIENT_ID=your-orcid-client-id
ORCID_CLIENT_SECRET=your-orcid-client-secret

# Email Configuration (for password reset)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
EMAIL_FROM=noreply@docid.africapidalliance.org
```

## Development Workflow

### 1. Start the Development Servers

The application consists of two parts: the Next.js frontend and an Express.js backend server.

**Option A: Run both servers separately (Recommended for development)**

Terminal 1 - Start the Express server:
```bash
npm run server:dev
# This starts the Express server on port 5000 with hot-reloading
```

Terminal 2 - Start the Next.js development server:
```bash
npm run dev
# This starts Next.js on port 3000 with Turbopack
```

**Option B: Run both concurrently**
```bash
npm run dev:all
# Starts both servers in one terminal
```

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api-docs (if configured)

### 3. Development Features

- **Hot Reloading**: Both frontend and backend support hot reloading
- **TypeScript Support**: Full TypeScript support with type checking
- **Path Aliases**: Use `@/` to import from the `src` directory
- **Redux DevTools**: Install the browser extension for Redux debugging

## Common Development Tasks

### Running Tests
```bash
npm test
# or
npm run test:watch
```

### Type Checking
```bash
npm run type-check
```

### Linting
```bash
npm run lint
# Auto-fix issues
npm run lint:fix
```

### Building for Production
```bash
npm run build
```

### Running Production Build Locally
```bash
npm run build
npm start
```

## Project Structure Overview

```
docid/
├── src/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # Reusable React components
│   ├── redux/           # Redux store and slices
│   ├── theme/           # MUI theme configuration
│   ├── context/         # React context providers
│   └── utils/           # Utility functions
├── server/              # Express.js backend
│   ├── controllers/     # Route controllers
│   ├── routes/          # API routes
│   └── index.js         # Server entry point
├── public/              # Static assets
├── locales/             # i18n translation files
└── next.config.js       # Next.js configuration
```

## Working with Features

### 1. Authentication
- Login page: `/login`
- Register page: `/register`
- OAuth providers configured in server
- JWT tokens stored in Redux

### 2. DOCiD Management
- Create DOCiD: `/assign-docid` (multi-step form)
- List DOCiDs: `/list-docids`
- View DOCiD: `/docid/[id]`

### 3. Internationalization
- Supported languages: English, French, Swahili, Arabic, Portuguese, German
- Language files in `/locales/[lang]/`
- Change language using the language selector in the UI

### 4. Theme Management
- Light/Dark mode toggle available
- Theme configuration in `/src/theme/`
- Uses MUI theming system

## Production Deployment with PM2

PM2 is a production-ready process manager that keeps your application running continuously, manages logs, and provides monitoring capabilities.

### Installing PM2

```bash
# Install PM2 globally
npm install pm2 -g

# Verify installation
pm2 --version
```

### PM2 Configuration

The project includes a PM2 ecosystem configuration file. If not present, it will be created during setup.

### Running with PM2

**Option 1: Using the ecosystem file (Recommended)**
```bash
# Start all services
pm2 start ecosystem.config.js

# Start specific service
pm2 start ecosystem.config.js --only docid-frontend
pm2 start ecosystem.config.js --only docid-server
```

**Option 2: Direct commands**
```bash
# Build the Next.js app first
npm run build

# Start Next.js frontend
pm2 start npm --name "docid-frontend" -- start

# Start Express server
pm2 start server/index.js --name "docid-server"
```

### PM2 Commands Reference

```bash
# View all processes
pm2 list

# Monitor processes
pm2 monit

# View logs
pm2 logs
pm2 logs docid-frontend
pm2 logs docid-server

# Restart services
pm2 restart all
pm2 restart docid-frontend
pm2 restart docid-server

# Stop services
pm2 stop all
pm2 stop docid-frontend

# Delete services
pm2 delete all
pm2 delete docid-frontend

# Save current process list
pm2 save

# Setup startup script
pm2 startup
```

### PM2 Log Management

```bash
# Flush logs
pm2 flush

# Reload logs
pm2 reloadLogs

# Install log rotation
pm2 install pm2-logrotate

# Configure log rotation
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```

### PM2 Monitoring

```bash
# Real-time monitoring
pm2 monit

# Web-based monitoring (optional)
pm2 install pm2-web
# Access at http://localhost:9615

# Get process information
pm2 describe docid-frontend
pm2 describe docid-server
```

### Environment Management with PM2

PM2 can manage different environments:

```bash
# Start with production environment
pm2 start ecosystem.config.js --env production

# Start with development environment
pm2 start ecosystem.config.js --env development

# Restart with different environment
pm2 restart docid-frontend --env production
```

### PM2 Cluster Mode

For better performance, run Next.js in cluster mode:

```bash
# Start in cluster mode with 4 instances
pm2 start npm --name "docid-frontend" -i 4 -- start

# Scale up/down
pm2 scale docid-frontend 8
pm2 scale docid-frontend 2
```

### PM2 Deployment

PM2 can handle deployments:

```bash
# Setup deployment
pm2 deploy ecosystem.config.js production setup

# Deploy
pm2 deploy ecosystem.config.js production

# Revert to previous deployment
pm2 deploy ecosystem.config.js production revert 1
```

## Troubleshooting

### Port Already in Use
If ports 3000 or 5000 are already in use:
```bash
# Change Next.js port
PORT=3001 npm run dev

# Change server port in .env.local
PORT=5001
```

### Dependencies Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### Build Errors
```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

### Redux Persist Issues
If experiencing state persistence issues:
1. Clear browser local storage
2. Check Redux DevTools for state shape
3. Verify persist configuration in `/src/redux/store.js`

## Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Material-UI Documentation](https://mui.com/)
- [Redux Toolkit Documentation](https://redux-toolkit.js.org/)
- [next-i18next Documentation](https://github.com/i18next/next-i18next)

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests and linting
4. Commit your changes: `git commit -m "Add your feature"`
5. Push to the branch: `git push origin feature/your-feature`
6. Create a Pull Request

## Support

For issues or questions:
- Check existing issues in the repository
- Contact the development team
- Refer to the Africa PID Alliance documentation