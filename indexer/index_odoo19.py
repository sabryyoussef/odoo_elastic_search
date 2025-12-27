#!/usr/bin/env python3
"""
Odoo 19 Source Code & Documentation Indexer
Indexes Odoo files into Elasticsearch with chunking support.
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import re

from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm


# Configuration from environment
ES_URL = os.getenv("ES_URL", "http://localhost:9200")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASS = os.getenv("ES_PASS", "elastic")
CODE_INDEX = os.getenv("CODE_INDEX", "odoo19_code")
DOC_INDEX = os.getenv("DOC_INDEX", "odoo19_docs")
ODOO19_ROOT = os.getenv("ODOO19_ROOT")

# Chunking configuration
CHUNK_LINES = int(os.getenv("CHUNK_LINES", "200"))
OVERLAP = int(os.getenv("OVERLAP", "30"))

# File extensions
CODE_EXTENSIONS = {'.py', '.js', '.xml', '.sql', '.csv', '.yml', '.yaml', '.scss', '.css', '.po'}
DOC_EXTENSIONS = {'.md', '.rst', '.txt'}

# Directories to skip
SKIP_DIRS = {'.git', '.venv', 'node_modules', '__pycache__', '.idea', '.vscode', 
             'venv', 'venv19', '.pytest_cache', '.mypy_cache', 'dist', 'build', 
             '.tox', '.eggs', '*.egg-info'}


def extract_module_name(path: str, root: str) -> Optional[str]:
    """
    Extract module name from path if it's in an addons directory.
    Looks for patterns like /addons/<module>/ or /custom_addons/<module>/
    """
    rel_path = os.path.relpath(path, root)
    parts = rel_path.split(os.sep)
    
    for i, part in enumerate(parts):
        if part in ('addons', 'custom_addons', 'enterprise') and i + 1 < len(parts):
            return parts[i + 1]
    
    return None


def chunk_file_content(lines: List[str], chunk_size: int = CHUNK_LINES, 
                       overlap: int = OVERLAP) -> List[Dict]:
    """
    Split file content into overlapping chunks.
    Returns list of dicts with chunk_id, start_line, end_line, and content.
    """
    chunks = []
    total_lines = len(lines)
    
    if total_lines == 0:
        return chunks
    
    chunk_id = 0
    start = 0
    
    while start < total_lines:
        end = min(start + chunk_size, total_lines)
        chunk_content = ''.join(lines[start:end])
        
        chunks.append({
            'chunk_id': chunk_id,
            'start_line': start + 1,  # 1-indexed
            'end_line': end,
            'content': chunk_content
        })
        
        chunk_id += 1
        
        # Move forward by chunk_size - overlap
        start += chunk_size - overlap
        
        # Avoid creating tiny chunks at the end
        if start < total_lines and (total_lines - start) < overlap:
            break
    
    return chunks


def detect_language(file_path: str) -> str:
    """Detect language/type from file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.xml': 'xml',
        '.sql': 'sql',
        '.csv': 'csv',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.scss': 'scss',
        '.css': 'css',
        '.po': 'gettext',
        '.md': 'markdown',
        '.rst': 'restructuredtext',
        '.txt': 'text'
    }
    
    return lang_map.get(ext, 'unknown')


def should_skip_dir(dir_name: str) -> bool:
    """Check if directory should be skipped."""
    return dir_name in SKIP_DIRS or dir_name.startswith('.')


def scan_files(root_path: str) -> tuple[List[str], List[str]]:
    """
    Scan directory tree and return lists of code files and doc files.
    """
    code_files = []
    doc_files = []
    
    print(f"📂 Scanning {root_path}...")
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip unwanted directories
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            ext = os.path.splitext(filename)[1].lower()
            
            if ext in CODE_EXTENSIONS:
                code_files.append(file_path)
            elif ext in DOC_EXTENSIONS:
                doc_files.append(file_path)
    
    print(f"✅ Found {len(code_files)} code files and {len(doc_files)} doc files")
    return code_files, doc_files


def index_code_file(file_path: str, root_path: str, es_client: Elasticsearch) -> List[Dict]:
    """
    Read and chunk a code file, returning documents ready for bulk indexing.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}")
        return []
    
    rel_path = os.path.relpath(file_path, root_path)
    module = extract_module_name(file_path, root_path)
    language = detect_language(file_path)
    file_ext = os.path.splitext(file_path)[1].lower()
    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
    
    chunks = chunk_file_content(lines)
    
    docs = []
    for chunk in chunks:
        doc_id = f"{rel_path}:{chunk['chunk_id']}"
        
        doc = {
            '_index': CODE_INDEX,
            '_id': doc_id,
            '_source': {
                'path': rel_path,
                'repo': 'odoo',
                'version': '19',
                'module': module,
                'language': language,
                'file_ext': file_ext,
                'content': chunk['content'],
                'mtime': mtime,
                'chunk_id': chunk['chunk_id'],
                'start_line': chunk['start_line'],
                'end_line': chunk['end_line']
            }
        }
        docs.append(doc)
    
    return docs


def index_doc_file(file_path: str, root_path: str, es_client: Elasticsearch) -> List[Dict]:
    """
    Read and chunk a documentation file, returning documents ready for bulk indexing.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}")
        return []
    
    rel_path = os.path.relpath(file_path, root_path)
    doc_kind = detect_language(file_path)
    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
    
    chunks = chunk_file_content(lines)
    
    docs = []
    for chunk in chunks:
        doc_id = f"{rel_path}:{chunk['chunk_id']}"
        
        doc = {
            '_index': DOC_INDEX,
            '_id': doc_id,
            '_source': {
                'path': rel_path,
                'repo': 'odoo',
                'version': '19',
                'doc_kind': doc_kind,
                'content': chunk['content'],
                'mtime': mtime,
                'chunk_id': chunk['chunk_id'],
                'start_line': chunk['start_line'],
                'end_line': chunk['end_line']
            }
        }
        docs.append(doc)
    
    return docs


def bulk_index_files(files: List[str], root_path: str, es_client: Elasticsearch, 
                     file_type: str = 'code') -> int:
    """
    Index a list of files using bulk API.
    """
    print(f"\n📝 Indexing {len(files)} {file_type} files...")
    
    index_func = index_code_file if file_type == 'code' else index_doc_file
    total_docs = 0
    
    # Process files in batches
    batch_size = 50
    for i in tqdm(range(0, len(files), batch_size), desc=f"Processing {file_type} files"):
        batch_files = files[i:i+batch_size]
        
        # Prepare all documents for this batch
        all_docs = []
        for file_path in batch_files:
            docs = index_func(file_path, root_path, es_client)
            all_docs.extend(docs)
        
        # Bulk index
        if all_docs:
            try:
                success, failed = helpers.bulk(
                    es_client,
                    all_docs,
                    raise_on_error=False,
                    raise_on_exception=False
                )
                total_docs += success
                
                if failed:
                    print(f"⚠️  {failed} documents failed to index")
            except Exception as e:
                print(f"❌ Bulk indexing error: {e}")
    
    return total_docs


def main():
    """Main indexing process."""
    
    # Validate required environment variables
    if not ODOO19_ROOT:
        print("❌ ERROR: ODOO19_ROOT environment variable is required!")
        print("   Example: export ODOO19_ROOT=/path/to/odoo19")
        sys.exit(1)
    
    if not os.path.exists(ODOO19_ROOT):
        print(f"❌ ERROR: ODOO19_ROOT path does not exist: {ODOO19_ROOT}")
        sys.exit(1)
    
    print("=" * 70)
    print("🚀 Odoo 19 Search Stack Indexer")
    print("=" * 70)
    print(f"📁 Odoo Root:      {ODOO19_ROOT}")
    print(f"🔗 ES URL:         {ES_URL}")
    print(f"📊 Code Index:     {CODE_INDEX}")
    print(f"📄 Doc Index:      {DOC_INDEX}")
    print(f"📏 Chunk Size:     {CHUNK_LINES} lines")
    print(f"🔄 Overlap:        {OVERLAP} lines")
    print("=" * 70)
    
    # Connect to Elasticsearch
    print("\n🔌 Connecting to Elasticsearch...")
    try:
        import warnings
        from urllib3.exceptions import InsecureRequestWarning
        warnings.filterwarnings('ignore', category=InsecureRequestWarning)
        
        es = Elasticsearch(
            ES_URL,
            basic_auth=(ES_USER, ES_PASS),
            verify_certs=False,
            ssl_show_warn=False,
            request_timeout=30
        )
        
        # Test connection
        ping_result = es.ping()
        print(f"   Ping result: {ping_result}")
        if not ping_result:
            print("❌ Cannot connect to Elasticsearch!")
            print(f"   Tried: {ES_URL} with user {ES_USER}")
            sys.exit(1)
        
        info = es.info()
        print(f"✅ Connected to Elasticsearch {info['version']['number']}")
        print(f"   Cluster: {info['cluster_name']}")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Scan files
    code_files, doc_files = scan_files(ODOO19_ROOT)
    
    if not code_files and not doc_files:
        print("❌ No files found to index!")
        sys.exit(1)
    
    # Index code files
    if code_files:
        code_docs = bulk_index_files(code_files, ODOO19_ROOT, es, 'code')
        print(f"✅ Indexed {code_docs} code document chunks")
    
    # Index documentation files
    if doc_files:
        doc_docs = bulk_index_files(doc_files, ODOO19_ROOT, es, 'docs')
        print(f"✅ Indexed {doc_docs} documentation chunks")
    
    # Refresh indices
    print("\n🔄 Refreshing indices...")
    es.indices.refresh(index=[CODE_INDEX, DOC_INDEX])
    
    # Show final counts
    print("\n" + "=" * 70)
    print("📊 FINAL STATISTICS")
    print("=" * 70)
    
    code_count = es.count(index=CODE_INDEX)['count']
    doc_count = es.count(index=DOC_INDEX)['count']
    
    print(f"📝 {CODE_INDEX}: {code_count:,} documents")
    print(f"📄 {DOC_INDEX}: {doc_count:,} documents")
    print(f"💾 Total: {code_count + doc_count:,} documents")
    print("=" * 70)
    
    print("\n✨ Indexing complete!")
    print(f"\n🔍 Test with:")
    print(f'   curl -u {ES_USER}:{ES_PASS} "{ES_URL}/{CODE_INDEX}/_search?q=AccountMove&size=3&pretty"')


if __name__ == "__main__":
    main()
