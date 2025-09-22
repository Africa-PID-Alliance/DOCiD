# PM2 Deployment Guide for DOCiD Frontend

## Overview

This guide provides detailed instructions for deploying the DOCiD frontend application using PM2, a production-ready process manager for Node.js applications.

## Prerequisites

- Node.js (v18.0.0 or higher)
- npm or yarn
- Built application (`npm run build` completed)
- PM2 installed globally (`npm install pm2 -g`)

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Build the application
npm run build

# 3. Start with PM2
pm2 start ecosystem.config.js

# 4. Check status
pm2 status
```

## Detailed Setup

### 1. Initial Configuration

The `ecosystem.config.js` file is pre-configured with optimal settings for both the Next.js frontend and Express.js backend server.

**Key configurations:**
- **Frontend**: Runs in cluster mode with max CPU cores
- **Backend**: Runs with 2 instances in cluster mode
- **Logging**: Separate log files for errors and output
- **Memory limits**: Auto-restart on memory threshold
- **Environment**: Separate dev/production configurations

### 2. Starting the Application

**Start all services:**
```bash
pm2 start ecosystem.config.js
```

**Start specific service:**
```bash
pm2 start ecosystem.config.js --only docid-frontend
pm2 start ecosystem.config.js --only docid-server
```

**Start in production mode:**
```bash
pm2 start ecosystem.config.js --env production
```

### 3. Process Management

**View running processes:**
```bash
pm2 list
```

**Monitor in real-time:**
```bash
pm2 monit
```

**View logs:**
```bash
# All logs
pm2 logs

# Specific service logs
pm2 logs docid-frontend
pm2 logs docid-server

# Last 100 lines
pm2 logs --lines 100
```

**Restart processes:**
```bash
# Restart all
pm2 restart all

# Restart specific
pm2 restart docid-frontend

# Graceful reload (zero-downtime)
pm2 reload docid-frontend
```

### 4. Scaling

**Scale frontend instances:**
```bash
# Scale to 8 instances
pm2 scale docid-frontend 8

# Scale down to 2 instances
pm2 scale docid-frontend 2
```

**Scale backend instances:**
```bash
pm2 scale docid-server 4
```

### 5. Persistence & Auto-start

**Save current process list:**
```bash
pm2 save
```

**Setup auto-start on system boot:**
```bash
pm2 startup
# Follow the command output instructions
```

**Disable auto-start:**
```bash
pm2 unstartup
```

### 6. Log Management

**Install log rotation:**
```bash
pm2 install pm2-logrotate
```

**Configure log rotation:**
```bash
# Max size before rotation
pm2 set pm2-logrotate:max_size 10M

# Number of rotated logs to keep
pm2 set pm2-logrotate:retain 7

# Compression
pm2 set pm2-logrotate:compress true
```

**Flush logs:**
```bash
pm2 flush
```

### 7. Monitoring & Metrics

**Built-in monitoring:**
```bash
pm2 monit
```

**Web-based dashboard:**
```bash
pm2 install pm2-web
# Access at http://localhost:9615
```

**Process information:**
```bash
pm2 info docid-frontend
pm2 info docid-server
```

## Environment Variables

PM2 respects the `.env.local` file. For production deployments, ensure all required environment variables are set:

```bash
# Create production env file
cp .env.local .env.production.local

# Edit with production values
nano .env.production.local
```

## Troubleshooting

### Process Crashes
```bash
# Check error logs
pm2 logs --err

# Check process details
pm2 describe docid-frontend

# Increase error details
pm2 set pm2:error-detail true
```

### Memory Issues
```bash
# Check memory usage
pm2 status

# Adjust memory limit in ecosystem.config.js
max_memory_restart: '2G'  # Increase limit

# Restart to apply
pm2 restart all
```

### Port Conflicts
```bash
# Check what's using the port
lsof -i :3000
lsof -i :5000

# Kill process using port
kill -9 <PID>
```

### Permission Issues
```bash
# Fix log directory permissions
mkdir -p logs
chmod 755 logs

# Run PM2 as current user (not root)
pm2 delete all
pm2 start ecosystem.config.js
```

## Production Best Practices

### 1. Security
- Use environment variables for sensitive data
- Enable HTTPS in production
- Set proper CORS origins
- Keep dependencies updated

### 2. Performance
- Enable cluster mode for multi-core CPUs
- Set appropriate memory limits
- Use PM2's graceful reload for updates
- Monitor CPU and memory usage

### 3. Reliability
- Configure auto-restart settings
- Set up log rotation
- Use PM2's built-in error handling
- Implement health checks

### 4. Monitoring
- Set up alerts for crashes
- Monitor response times
- Track memory usage trends
- Review logs regularly

## Deployment Script

Create a deployment script for consistent deployments:

```bash
#!/bin/bash
# deploy.sh

echo "Starting deployment..."

# Pull latest code
git pull origin main

# Install dependencies
npm install

# Build application
npm run build

# Reload PM2 processes
pm2 reload ecosystem.config.js --env production

echo "Deployment complete!"
```

Make it executable:
```bash
chmod +x deploy.sh
./deploy.sh
```

## Backup & Recovery

### Backup PM2 configuration
```bash
pm2 save
cp ~/.pm2/dump.pm2 ./backup/pm2-dump-$(date +%Y%m%d).pm2
```

### Restore from backup
```bash
pm2 delete all
pm2 resurrect ./backup/pm2-dump-20240101.pm2
```

## Additional Resources

- [PM2 Documentation](https://pm2.keymetrics.io/docs/)
- [PM2 Best Practices](https://pm2.keymetrics.io/docs/usage/best-practices/)
- [Next.js Production Deployment](https://nextjs.org/docs/deployment)
- [Node.js Production Best Practices](https://nodejs.org/en/docs/guides/nodejs-docker-webapp/)

## Support

For DOCiD-specific issues:
- Check application logs: `pm2 logs`
- Review error logs: `pm2 logs --err`
- Contact support: support@africapidalliance.org