# Git Workflow Instructions for DOCiD Project

## Repository Structure
- **Backend** (`/backend`) - Flask REST API (you push changes)
- **Frontend** (`/frontend`) - Next.js application (you pull changes from other developer)

## Prerequisites
Ensure you have SSH key configured for GitHub:
```bash
ssh -T git@github.com
# Should see: "Hi ekariz! You've successfully authenticated..."
```

## Backend Workflow (Pushing Your Local Changes)

### Daily Workflow
1. **Start your work session - Pull latest changes:**
```bash
cd /Users/ekariz/Projects/AMBAND/DOCiD/project
git pull origin main
```

2. **Make your backend changes**
```bash
# Edit files in backend/
# Test your changes locally
cd backend
python run.py
```

3. **Check what files you've modified:**
```bash
git status
```

4. **Stage and commit your backend changes:**
```bash
# Stage specific backend files
git add backend/

# Or stage specific files only
git add backend/app/routes/new_route.py
git add backend/app/models.py

# Commit with descriptive message
git commit -m "Backend: Add new API endpoint for user authentication"
```

5. **Push to GitHub:**
```bash
git push origin main
```

### Handling Conflicts
If you get conflicts when pulling:
```bash
# See which files have conflicts
git status

# Edit conflicted files to resolve
# Look for <<<<<<< HEAD markers

# After resolving, stage and commit
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

## Frontend Workflow (Pulling Other Developer's Changes)

### Daily Workflow
1. **Check for frontend updates:**
```bash
cd /Users/ekariz/Projects/AMBAND/DOCiD/project
git fetch origin
```

2. **See what's changed:**
```bash
git log HEAD..origin/main --oneline
```

3. **Pull frontend changes:**
```bash
git pull origin main
```

4. **Install any new dependencies:**
```bash
cd frontend
npm install
```

5. **Test the frontend locally:**
```bash
npm run dev
# Visit http://localhost:3000
```

### If Frontend Has Breaking Changes
```bash
# Clean install of dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## Combined Workflow Example

### Typical Day:
```bash
# Morning - Get latest updates
cd /Users/ekariz/Projects/AMBAND/DOCiD/project
git pull origin main

# Check if frontend has new dependencies
cd frontend
npm install

# Work on backend
cd ../backend
# ... make your changes ...

# End of day - Push your backend changes
cd ..
git add backend/
git commit -m "Backend: Implement RAID API integration"
git push origin main
```

## Important Commands

### View Recent Commits
```bash
git log --oneline -10
```

### Check Remote Repository
```bash
git remote -v
```

### See Who Changed What
```bash
git blame backend/app/routes/publications.py
```

### Undo Local Changes (Before Commit)
```bash
# Undo changes to a specific file
git checkout -- backend/app/config.py

# Undo all local changes
git checkout -- .
```

### Create a Branch for Major Changes
```bash
# Create and switch to new branch
git checkout -b backend-feature-raid

# Work and commit on branch
git add backend/
git commit -m "Add RAID integration"

# Push branch
git push origin backend-feature-raid

# Later, merge to main
git checkout main
git merge backend-feature-raid
git push origin main
```

## Environment Files

### Never Commit .env Files
The `.gitignore` is configured to exclude:
- `backend/.env`
- `frontend/.env.development`
- `frontend/.env.production`

### To Update .env.example
When you add new environment variables:
```bash
# Update the example file
vim backend/.env.example

# Commit only the example
git add backend/.env.example
git commit -m "Backend: Add new RAID API env variables to example"
git push origin main
```

## Quick Status Check
```bash
# See current branch and changes
git status

# See difference in files
git diff backend/

# See staged changes
git diff --staged
```

## Troubleshooting

### If Push is Rejected
```bash
# Someone else pushed changes first
git pull origin main
# Resolve any conflicts if they exist
git push origin main
```

### If You Accidentally Committed Secrets
```bash
# DO NOT PUSH!
# Remove the file from staging
git reset HEAD~1
# Fix the file
# Recommit without secrets
```

### Check What Will Be Pushed
```bash
git diff origin/main..HEAD
```

## Contact
- Backend Developer: Erastus Kariuki <ekariz@gmail.com>
- Frontend Developer: Steve Gaikia <steveggaita@gmail.com>

## Remember
- Always pull before starting work
- Commit frequently with clear messages
- Never commit passwords, keys, or secrets
- Test locally before pushing
- Communicate with team about major changes