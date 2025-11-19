module.exports = {
  apps: [
    {
      // Next.js Frontend Application
      name: 'docid-frontend',
      script: 'node_modules/next/dist/bin/next',
      args: 'start',
      cwd: './',
      instances: 'max',
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'development',
        PORT: 3000
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 3000,
        BACKEND_API_URL: 'http://197.136.17.175:6000/api'
      },
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      log_file: './logs/frontend-combined.log',
      time: true,
      max_memory_restart: '1G',
      watch: false,
      ignore_watch: ['node_modules', '.next', 'logs'],
      max_restarts: 10,
      min_uptime: '10s',
      listen_timeout: 3000,
      kill_timeout: 5000
    },
    {
      // Express.js Backend Server
      name: 'docid-server',
      script: './server/index.js',
      instances: 2,
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'development',
        PORT: 5000
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 5000
      },
      error_file: './logs/server-error.log',
      out_file: './logs/server-out.log',
      log_file: './logs/server-combined.log',
      time: true,
      max_memory_restart: '500M',
      watch: false,
      ignore_watch: ['node_modules', 'logs'],
      max_restarts: 10,
      min_uptime: '10s',
      listen_timeout: 3000,
      kill_timeout: 5000
    }
  ],

  // Deployment Configuration (Optional)
  deploy: {
    production: {
      user: 'deploy',
      host: 'your-server.com',
      ref: 'origin/main',
      repo: 'git@github.com:your-org/docid-frontend.git',
      path: '/var/www/docid',
      'pre-deploy-local': '',
      'post-deploy': 'npm install && npm run build && pm2 reload ecosystem.config.js --env production',
      'pre-setup': '',
      ssh_options: 'StrictHostKeyChecking=no'
    },
    staging: {
      user: 'deploy',
      host: 'staging.your-server.com',
      ref: 'origin/develop',
      repo: 'git@github.com:your-org/docid-frontend.git',
      path: '/var/www/docid-staging',
      'pre-deploy-local': '',
      'post-deploy': 'npm install && npm run build && pm2 reload ecosystem.config.js --env production',
      'pre-setup': '',
      ssh_options: 'StrictHostKeyChecking=no'
    }
  }
};