#!/bin/bash

# Initialize Git Repository for Odoo Elastic Search

cd "$(dirname "$0")"

echo "🎯 Initializing Odoo Elastic Search Repository"
echo "=============================================="

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git repository already initialized"
fi

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Elasticsearch
data/
logs/
exported_data/export_*/
*.tar.gz

# Environment
.env.local
.env.*.local

# OS
.DS_Store
Thumbs.db

# Temporary files
*.log
*.tmp
tmp/

# Large data files (use Git LFS or external storage)
*.ndjson
*_sample.json
EOF

echo "✅ Created .gitignore"

# Create LICENSE
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 Odoo Elastic Search Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

echo "✅ Created LICENSE"

# Add all files to git
echo "📦 Staging files..."
git add .

echo ""
echo "✅ Repository initialized successfully!"
echo ""
echo "📋 Next steps:"
echo "  1. Review the files: git status"
echo "  2. Commit: git commit -m 'Initial commit: Odoo Elastic Search Stack'"
echo "  3. Add remote: git remote add origin https://github.com/sabryyoussef/odoo_elastic_search.git"
echo "  4. Push: git push -u origin main"
echo ""
echo "🎉 Your repository is ready to push to GitHub!"
