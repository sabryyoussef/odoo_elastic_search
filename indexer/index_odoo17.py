#!/usr/bin/env python3
"""
Odoo 17 Source Code & Documentation Indexer
Indexes Odoo 17 files (community and enterprise) into Elasticsearch with chunking support.
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
CODE_INDEX = os.getenv("CODE_INDEX", "odoo17_code")
DOC_INDEX = os.getenv("DOC_INDEX", "odoo17_docs")
ODOO17_ROOT = os.getenv("ODOO17_ROOT")

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


def get_language_from_extension(file_path: str) -> str:
    """Determine language from file extension."""
    ext = Path(file_path).suffix.lower()
    ext_to_lang = {
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
        '.rst': 'rst',
        '.txt': 'text'
    }
    return ext_to_lang.get(ext, 'unknown')


def chunk_content(content: str, chunk_lines: int = 200, overlap: int = 30) -> List[Dict]:
    """
    Split content into overlapping chunks by lines.
    Returns list of chunk dictionaries with content, start_line, end_line.
    """
    lines = content.split('\n')
    total_lines = len(lines)
    
    if total_lines <= chunk_lines:
        return [{
            'content': content,
            'start_line': 1,
            'end_line': total_lines
        }]
    
    chunks = []
    start_idx = 0
    chunk_num = 1
    
    while start_idx < total_lines:
        end_idx = min(start_idx + chunk_lines, total_lines)
        
        chunk_lines_list = lines[start_idx:end_idx]
        chunk_content = '\n'.join(chunk_lines_list)
        
        chunks.append({
            'content': chunk_content,
            'start_line': start_idx + 1,
            'end_line': end_idx,
            'chunk_number': chunk_num
        })
        
        chunk_num += 1
        
        # Move start position, accounting for overlap
        if end_idx >= total_lines:
            break
        start_idx = max(start_idx + chunk_lines - overlap, start_idx + 1)
    
    return chunks


def create_elasticsearch_mappings(es: Elasticsearch, index_name: str, is_doc: bool = False):
    """Create Elasticsearch index with appropriate mappings."""
    
    if is_doc:
        mapping = {
            "mappings": {
                "properties": {
                    "content": {"type": "text", "analyzer": "standard"},
                    "file_path": {"type": "keyword"},
                    "relative_path": {"type": "keyword"},
                    "filename": {"type": "keyword"},
                    "file_size": {"type": "integer"},
                    "language": {"type": "keyword"},
                    "indexed_at": {"type": "date"},
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"},
                    "chunk_number": {"type": "integer"}
                }
            }
        }
    else:
        mapping = {
            "mappings": {
                "properties": {
                    "content": {"type": "text", "analyzer": "standard"},
                    "file_path": {"type": "keyword"},
                    "relative_path": {"type": "keyword"},
                    "filename": {"type": "keyword"},
                    "file_size": {"type": "integer"},
                    "language": {"type": "keyword"},
                    "module": {"type": "keyword"},
                    "indexed_at": {"type": "date"},
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"},
                    "chunk_number": {"type": "integer"}
                }
            }
        }
    
    try:
        if es.indices.exists(index=index_name):
            print(f"⚠️  Index '{index_name}' already exists. Deleting and recreating...")
            es.indices.delete(index=index_name)
        
        es.indices.create(index=index_name, body=mapping)
        print(f"✅ Created index: {index_name}")
    except Exception as e:
        print(f"❌ Error creating index {index_name}: {e}")
        return False
    
    return True


def should_skip_file(file_path: Path, root_path: Path) -> bool:
    """Check if file should be skipped based on various criteria."""
    
    # Skip if in skip directories
    for part in file_path.parts:
        if part in SKIP_DIRS or part.startswith('.'):
            return True
    
    # Skip binary files and other unwanted extensions
    skip_extensions = {'.pyc', '.pyo', '.so', '.dylib', '.dll', '.exe', '.bin', 
                      '.jpg', '.png', '.gif', '.pdf', '.zip', '.tar', '.gz'}
    if file_path.suffix.lower() in skip_extensions:
        return True
    
    # Skip very large files (>10MB)
    try:
        if file_path.stat().st_size > 10 * 1024 * 1024:
            return True
    except (OSError, IOError):
        return True
    
    return False


def get_files_to_index(root_path: Path, extensions: set) -> List[Path]:
    """Get list of files to index based on extensions."""
    files = []
    
    for file_path in root_path.rglob('*'):
        if not file_path.is_file():
            continue
        
        if should_skip_file(file_path, root_path):
            continue
        
        if file_path.suffix.lower() in extensions:
            files.append(file_path)
    
    return files


def create_document(file_path: Path, root_path: Path, chunk: Dict, is_doc: bool = False) -> Dict:
    """Create document for Elasticsearch indexing."""
    
    rel_path = file_path.relative_to(root_path)
    language = get_language_from_extension(str(file_path))
    
    doc = {
        'content': chunk['content'],
        'file_path': str(file_path),
        'relative_path': str(rel_path),
        'filename': file_path.name,
        'file_size': file_path.stat().st_size,
        'language': language,
        'indexed_at': datetime.now(),
        'start_line': chunk['start_line'],
        'end_line': chunk['end_line']
    }
    
    if 'chunk_number' in chunk:
        doc['chunk_number'] = chunk['chunk_number']
    
    # Add module information for code files
    if not is_doc:
        module = extract_module_name(str(file_path), str(root_path))
        if module:
            doc['module'] = module
    
    return doc


def index_files(es: Elasticsearch, files: List[Path], index_name: str, root_path: Path, is_doc: bool = False):
    """Index files into Elasticsearch with chunking."""
    
    def generate_docs():
        for file_path in tqdm(files, desc=f"Processing {'docs' if is_doc else 'code'} files"):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Skip empty files
                if not content.strip():
                    continue
                
                # Chunk the content
                chunks = chunk_content(content, CHUNK_LINES, OVERLAP)
                
                for chunk in chunks:
                    doc = create_document(file_path, root_path, chunk, is_doc)
                    yield {
                        "_index": index_name,
                        "_source": doc
                    }
            
            except Exception as e:
                print(f"⚠️  Error processing {file_path}: {e}")
                continue
    
    try:
        # Use bulk indexing for better performance
        success_count = 0
        error_count = 0
        
        for success, info in helpers.parallel_bulk(
            es, 
            generate_docs(),
            chunk_size=100,
            max_chunk_bytes=10485760,  # 10MB chunks
            thread_count=4
        ):
            if success:
                success_count += 1
            else:
                error_count += 1
                print(f"❌ Error indexing document: {info}")
        
        print(f"✅ Indexed {success_count} documents successfully")
        if error_count > 0:
            print(f"⚠️  {error_count} documents failed to index")
    
    except Exception as e:
        print(f"❌ Bulk indexing error: {e}")


def main():
    """Main indexing function."""
    
    # Validate Odoo root
    if not ODOO17_ROOT:
        print("❌ ODOO17_ROOT environment variable not set")
        print("Usage: export ODOO17_ROOT=/path/to/odoo17 && python index_odoo17.py")
        return 1
    
    root_path = Path(ODOO17_ROOT)
    if not root_path.exists():
        print(f"❌ Odoo 17 root directory does not exist: {root_path}")
        return 1
    
    print(f"🎯 Indexing Odoo 17 from: {root_path}")
    print(f"📍 Elasticsearch: {ES_URL}")
    print(f"📊 Code Index: {CODE_INDEX}")
    print(f"📄 Docs Index: {DOC_INDEX}")
    print(f"⚙️  Chunk Size: {CHUNK_LINES} lines (overlap: {OVERLAP})")
    print("-" * 60)
    
    # Connect to Elasticsearch
    try:
        es = Elasticsearch(
            [ES_URL],
            http_auth=(ES_USER, ES_PASS),
            verify_certs=False,
            timeout=30
        )
        
        if not es.ping():
            print("❌ Cannot connect to Elasticsearch")
            return 1
        
        print("✅ Connected to Elasticsearch")
    
    except Exception as e:
        print(f"❌ Elasticsearch connection error: {e}")
        return 1
    
    # Create indices
    if not create_elasticsearch_mappings(es, CODE_INDEX, is_doc=False):
        return 1
    
    if not create_elasticsearch_mappings(es, DOC_INDEX, is_doc=True):
        return 1
    
    # Find files to index
    print("\n🔍 Scanning for files...")
    code_files = get_files_to_index(root_path, CODE_EXTENSIONS)
    doc_files = get_files_to_index(root_path, DOC_EXTENSIONS)
    
    print(f"📁 Found {len(code_files)} code files")
    print(f"📄 Found {len(doc_files)} documentation files")
    
    if not code_files and not doc_files:
        print("⚠️  No files found to index")
        return 1
    
    # Index code files
    if code_files:
        print(f"\n📁 Indexing {len(code_files)} code files...")
        index_files(es, code_files, CODE_INDEX, root_path, is_doc=False)
    
    # Index documentation files
    if doc_files:
        print(f"\n📄 Indexing {len(doc_files)} documentation files...")
        index_files(es, doc_files, DOC_INDEX, root_path, is_doc=True)
    
    # Print final statistics
    try:
        code_count = es.count(index=CODE_INDEX)['count'] if code_files else 0
        doc_count = es.count(index=DOC_INDEX)['count'] if doc_files else 0
        
        print("\n" + "=" * 60)
        print("🎉 INDEXING COMPLETE!")
        print(f"📁 Code documents: {code_count}")
        print(f"📄 Documentation documents: {doc_count}")
        print(f"🔗 Total documents: {code_count + doc_count}")
        print("=" * 60)
    
    except Exception as e:
        print(f"⚠️  Could not retrieve final counts: {e}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())