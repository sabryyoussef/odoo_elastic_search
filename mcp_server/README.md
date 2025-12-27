# Odoo 19 MCP Search Server

MCP (Model Context Protocol) server that provides search tools for AI agents to query indexed Odoo 19 source code and documentation.

## Features

- 🔍 **search_code**: Search through Python, JavaScript, XML, and other code files
- 📄 **search_docs**: Search through documentation (Markdown, RST, text)
- 📦 **get_chunk**: Retrieve full content of specific code/doc chunks
- 🎯 **Filtering**: Filter by module, path, language, or document type
- 📍 **Line-level precision**: Every result includes exact line ranges
- ⚡ **Fast**: Powered by Elasticsearch full-text search

## Prerequisites

- Python 3.8+
- Elasticsearch 8.x running (see ../docker/)
- Indexed Odoo 19 data (see ../indexer/)

## Installation

Create a virtual environment and install dependencies:

```bash
cd mcp_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Set these environment variables:

```bash
# Optional (defaults shown)
export ES_URL=http://localhost:9200
export ES_USER=elastic
export ES_PASS=elastic
export CODE_INDEX=odoo19_code
export DOC_INDEX=odoo19_docs
```

## Usage

### Running the Server

```bash
# Make sure your venv is activated
source venv/bin/activate

# Set password if needed
export ES_PASS=elastic

# Run the MCP server
python server.py
```

The server communicates via stdio (standard input/output) following the MCP protocol.

### Configuring with Cursor/Claude Desktop

Add to your MCP configuration file:

**For Cursor** (`.cursor/mcp.json` or settings):
```json
{
  "mcpServers": {
    "odoo19-search": {
      "command": "/home/sabry3/sabry_backup/odoo_base/base_odoo_19/odoo19_search_stack/mcp_server/venv/bin/python",
      "args": [
        "/home/sabry3/sabry_backup/odoo_base/base_odoo_19/odoo19_search_stack/mcp_server/server.py"
      ],
      "env": {
        "ES_URL": "http://localhost:9200",
        "ES_USER": "elastic",
        "ES_PASS": "elastic"
      }
    }
  }
}
```

**For Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):
```json
{
  "mcpServers": {
    "odoo19-search": {
      "command": "/path/to/odoo19_search_stack/mcp_server/venv/bin/python",
      "args": ["/path/to/odoo19_search_stack/mcp_server/server.py"],
      "env": {
        "ES_PASS": "elastic"
      }
    }
  }
}
```

## Available Tools

### 1. search_code

Search Odoo 19 source code.

**Parameters:**
- `query` (required): Search query text
- `module` (optional): Filter by Odoo module name
- `path_prefix` (optional): Filter by path prefix
- `language` (optional): Filter by language (python, javascript, xml, etc.)
- `size` (optional): Number of results (default: 8, max: 50)

**Example:**
```python
{
  "query": "class AccountMove",
  "module": "account",
  "language": "python",
  "size": 5
}
```

**Returns:**
- File path
- Module name (if applicable)
- Language
- Line range (start_line - end_line)
- Chunk ID
- Relevance score
- Content preview

### 2. search_docs

Search Odoo 19 documentation.

**Parameters:**
- `query` (required): Search query text
- `doc_kind` (optional): Filter by document type (markdown, restructuredtext, text)
- `size` (optional): Number of results (default: 8, max: 50)

**Example:**
```python
{
  "query": "how to create invoice",
  "size": 5
}
```

**Returns:**
- File path
- Document type
- Line range
- Chunk ID
- Relevance score
- Content preview

### 3. get_chunk

Retrieve full content of a specific chunk.

**Parameters:**
- `index` (required): Index name ('odoo19_code' or 'odoo19_docs')
- `chunk_id` (required): Chunk ID from search results

**Example:**
```python
{
  "index": "odoo19_code",
  "chunk_id": "addons/account/models/account_move.py:0"
}
```

**Returns:**
- Complete chunk content
- All metadata (path, lines, module, etc.)

## Example Queries

### Search for Account Move class
```json
{
  "tool": "search_code",
  "args": {
    "query": "class AccountMove",
    "module": "account"
  }
}
```

### Search for XML views
```json
{
  "tool": "search_code",
  "args": {
    "query": "form view invoice",
    "language": "xml",
    "size": 10
  }
}
```

### Search for API documentation
```json
{
  "tool": "search_docs",
  "args": {
    "query": "ORM API reference",
    "doc_kind": "restructuredtext"
  }
}
```

### Get full chunk content
```json
{
  "tool": "get_chunk",
  "args": {
    "index": "odoo19_code",
    "chunk_id": "addons/account/models/account_move.py:2"
  }
}
```

## AI Agent Usage Guidelines

When using this MCP server, AI agents should:

1. **Search first**: Always call `search_code` or `search_docs` to find relevant chunks
2. **Use top results**: Focus on the top 5-12 highest-scoring results
3. **Get full content when needed**: Use `get_chunk` to retrieve complete code for detailed analysis
4. **Cite sources**: Include `path:start_line-end_line` in responses
5. **Filter intelligently**: Use module/path/language filters to narrow results

### Example Agent Workflow

```
1. User asks: "How does Odoo handle invoice posting?"

2. Agent calls: search_code(query="invoice post", module="account")

3. Agent receives: Top 8 chunks from account module

4. Agent calls: get_chunk() for most relevant 2-3 chunks

5. Agent responds with answer + citations:
   "Invoice posting is handled in `addons/account/models/account_move.py:450-520`..."
```

## Testing

Test the server locally:

```bash
# Start the server
python server.py

# In another terminal, use mcp-client or test with sample MCP requests
# The server expects JSON-RPC 2.0 messages on stdin
```

## Troubleshooting

### Cannot connect to Elasticsearch

```bash
# Check if ES is running
curl -u elastic:elastic http://localhost:9200

# Check Docker containers
docker ps | grep elasticsearch
```

### MCP server not responding

Check the server logs (stderr output) for connection errors or other issues.

### Tool not found

Make sure the Odoo code/docs have been indexed (see ../indexer/README.md).

## Performance

- Search latency: 50-200ms per query
- Typical search: 8 results in <100ms
- Full chunk retrieval: <50ms

## Security Note

This is a local development tool. Do not expose Elasticsearch to the internet without proper authentication and encryption.
