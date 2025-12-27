#!/usr/bin/env python3
"""
MCP Server for Odoo 19 Search Stack
Provides search tools for AI agents to query indexed Odoo code and documentation.
"""
import os
import sys
import asyncio
from typing import Optional, List, Dict, Any
import json

from mcp.server import Server
from mcp.types import Tool, TextContent
from elasticsearch import Elasticsearch


# Configuration from environment
ES_URL = os.getenv("ES_URL", "http://localhost:9200")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASS = os.getenv("ES_PASS", "elastic")
CODE_INDEX = os.getenv("CODE_INDEX", "odoo19_code")
DOC_INDEX = os.getenv("DOC_INDEX", "odoo19_docs")

# Initialize Elasticsearch client
es_client = Elasticsearch(
    ES_URL,
    basic_auth=(ES_USER, ES_PASS),
    verify_certs=False,
    request_timeout=30
)

# Initialize MCP server
app = Server("odoo19-search-mcp")


def format_search_result(hit: Dict) -> Dict[str, Any]:
    """Format Elasticsearch hit into a clean result."""
    source = hit['_source']
    
    result = {
        'id': hit['_id'],
        'path': source.get('path', ''),
        'start_line': source.get('start_line', 0),
        'end_line': source.get('end_line', 0),
        'score': hit['_score'],
        'content': source.get('content', '')[:500]  # Limit content preview
    }
    
    # Add code-specific fields
    if 'module' in source:
        result['module'] = source.get('module')
    if 'language' in source:
        result['language'] = source.get('language')
    
    return result


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_code",
            description=(
                "Search Odoo 19 source code for specific content. "
                "Returns code chunks with file paths, line ranges, and relevance scores. "
                "Use this to find Python classes, functions, XML views, JavaScript code, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text (e.g., 'class AccountMove', 'ir.actions.report')"
                    },
                    "module": {
                        "type": "string",
                        "description": "Optional: filter by Odoo module name (e.g., 'account', 'sale')"
                    },
                    "path_prefix": {
                        "type": "string",
                        "description": "Optional: filter by path prefix (e.g., 'addons/account/')"
                    },
                    "language": {
                        "type": "string",
                        "description": "Optional: filter by language (e.g., 'python', 'javascript', 'xml')"
                    },
                    "size": {
                        "type": "integer",
                        "description": "Number of results to return (default: 8, max: 50)",
                        "default": 8
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_docs",
            description=(
                "Search Odoo 19 documentation for specific content. "
                "Returns documentation chunks with file paths, line ranges, and relevance scores. "
                "Use this to find user guides, API documentation, tutorials, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text (e.g., 'how to create invoice', 'API reference')"
                    },
                    "doc_kind": {
                        "type": "string",
                        "description": "Optional: filter by document type ('markdown', 'restructuredtext', 'text')"
                    },
                    "size": {
                        "type": "integer",
                        "description": "Number of results to return (default: 8, max: 50)",
                        "default": 8
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_chunk",
            description=(
                "Retrieve the full content of a specific code or documentation chunk by its ID. "
                "Use this after searching to get complete content of a relevant chunk."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "index": {
                        "type": "string",
                        "description": "Index name ('odoo19_code' or 'odoo19_docs')",
                        "enum": ["odoo19_code", "odoo19_docs"]
                    },
                    "chunk_id": {
                        "type": "string",
                        "description": "Chunk ID from search results"
                    }
                },
                "required": ["index", "chunk_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    
    if name == "search_code":
        return await search_code_tool(arguments)
    elif name == "search_docs":
        return await search_docs_tool(arguments)
    elif name == "get_chunk":
        return await get_chunk_tool(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def search_code_tool(args: Dict[str, Any]) -> List[TextContent]:
    """Search code index."""
    query_text = args['query']
    size = min(args.get('size', 8), 50)
    
    # Build Elasticsearch query
    must_clauses = [
        {"match": {"content": query_text}}
    ]
    
    filter_clauses = []
    
    if args.get('module'):
        filter_clauses.append({"term": {"module": args['module']}})
    
    if args.get('path_prefix'):
        filter_clauses.append({"prefix": {"path": args['path_prefix']}})
    
    if args.get('language'):
        filter_clauses.append({"term": {"language": args['language']}})
    
    es_query = {
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses
            }
        },
        "size": size,
        "_source": ["path", "module", "language", "content", "start_line", "end_line", "chunk_id"]
    }
    
    try:
        response = es_client.search(index=CODE_INDEX, body=es_query)
        results = [format_search_result(hit) for hit in response['hits']['hits']]
        
        # Format as text
        result_text = f"# Code Search Results for: {query_text}\n\n"
        result_text += f"Found {len(results)} results\n\n"
        
        for i, result in enumerate(results, 1):
            result_text += f"## Result {i} (score: {result['score']:.2f})\n"
            result_text += f"**Path:** `{result['path']}`\n"
            if result.get('module'):
                result_text += f"**Module:** `{result['module']}`\n"
            if result.get('language'):
                result_text += f"**Language:** {result['language']}\n"
            result_text += f"**Lines:** {result['start_line']}-{result['end_line']}\n"
            result_text += f"**ID:** `{result['id']}`\n"
            result_text += f"\n```\n{result['content'][:400]}...\n```\n\n"
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        error_msg = f"Error searching code: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


async def search_docs_tool(args: Dict[str, Any]) -> List[TextContent]:
    """Search documentation index."""
    query_text = args['query']
    size = min(args.get('size', 8), 50)
    
    # Build Elasticsearch query
    must_clauses = [
        {"match": {"content": query_text}}
    ]
    
    filter_clauses = []
    
    if args.get('doc_kind'):
        filter_clauses.append({"term": {"doc_kind": args['doc_kind']}})
    
    es_query = {
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses
            }
        },
        "size": size,
        "_source": ["path", "doc_kind", "content", "start_line", "end_line", "chunk_id"]
    }
    
    try:
        response = es_client.search(index=DOC_INDEX, body=es_query)
        results = [format_search_result(hit) for hit in response['hits']['hits']]
        
        # Format as text
        result_text = f"# Documentation Search Results for: {query_text}\n\n"
        result_text += f"Found {len(results)} results\n\n"
        
        for i, result in enumerate(results, 1):
            result_text += f"## Result {i} (score: {result['score']:.2f})\n"
            result_text += f"**Path:** `{result['path']}`\n"
            result_text += f"**Lines:** {result['start_line']}-{result['end_line']}\n"
            result_text += f"**ID:** `{result['id']}`\n"
            result_text += f"\n```\n{result['content'][:400]}...\n```\n\n"
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        error_msg = f"Error searching docs: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


async def get_chunk_tool(args: Dict[str, Any]) -> List[TextContent]:
    """Get full content of a specific chunk."""
    index = args['index']
    chunk_id = args['chunk_id']
    
    try:
        response = es_client.get(index=index, id=chunk_id)
        source = response['_source']
        
        result_text = f"# Chunk: {chunk_id}\n\n"
        result_text += f"**Path:** `{source.get('path', 'unknown')}`\n"
        result_text += f"**Lines:** {source.get('start_line', 0)}-{source.get('end_line', 0)}\n"
        
        if 'module' in source:
            result_text += f"**Module:** `{source['module']}`\n"
        if 'language' in source:
            result_text += f"**Language:** {source['language']}\n"
        if 'doc_kind' in source:
            result_text += f"**Type:** {source['doc_kind']}\n"
        
        result_text += f"\n## Content\n\n```\n{source.get('content', '')}\n```\n"
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        error_msg = f"Error retrieving chunk: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


async def main():
    """Run the MCP server."""
    # Test Elasticsearch connection
    try:
        if not es_client.ping():
            print("❌ Cannot connect to Elasticsearch!", file=sys.stderr)
            sys.exit(1)
        
        info = es_client.info()
        print(f"✅ Connected to Elasticsearch {info['version']['number']}", file=sys.stderr)
        print(f"   Cluster: {info['cluster_name']}", file=sys.stderr)
        print(f"   Serving tools: search_code, search_docs, get_chunk", file=sys.stderr)
        
    except Exception as e:
        print(f"❌ Elasticsearch connection error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Run the MCP server
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
