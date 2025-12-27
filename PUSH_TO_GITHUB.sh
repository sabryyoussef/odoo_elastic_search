#!/bin/bash
# Run these commands to push to GitHub

echo "🚀 Pushing to GitHub: https://github.com/sabryyoussef/odoo_elastic_search"
echo ""

# Add remote (ignore error if already exists)
git remote add origin https://github.com/sabryyoussef/odoo_elastic_search.git 2>/dev/null || true

# Push to GitHub
echo "📤 Pushing to main branch..."
git push -u origin master:main --force

echo ""
echo "✅ Done! Check your repository at:"
echo "   https://github.com/sabryyoussef/odoo_elastic_search"
