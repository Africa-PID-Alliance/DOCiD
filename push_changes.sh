#!/bin/bash

echo "Pushing pending changes to GitHub..."
echo "This includes:"
echo "- Removing backend/docs folder"
echo "- Removing CLAUDE.md from tracking"
echo "- Adding backend/uploads/ to .gitignore"
echo "- Removing project-clean files"
echo ""

# Push the changes
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed all changes to GitHub!"
    echo ""
    echo "The following have been removed from GitHub:"
    echo "- backend/docs/ folder"
    echo "- backend/CLAUDE.md"
    echo "- project-clean/ files"
    echo ""
    echo "The following are now ignored:"
    echo "- backend/uploads/"
    echo "- backend/CLAUDE.md"
    echo "- GIT_WORKFLOW.md"
else
    echo "❌ Push failed. Please check your internet connection and try again."
    echo "You can run this script again: ./push_changes.sh"
fi