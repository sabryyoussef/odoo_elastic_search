# 🤖 AI Agent Setup Guide

This guide shows you how to integrate the Odoo Elasticsearch stack with AI agents for automated code analysis and search.

## 🎯 Overview

The Odoo Elastic Search stack provides an MCP (Model Context Protocol) server that enables AI agents to:
- Search Odoo source code across versions
- Analyze code changes between versions
- Find implementation patterns
- Assist with migration planning
- Generate documentation

## 🚀 Quick Setup

### 1. Start the MCP Server

```bash
cd mcp_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

### 2. Configure Your AI Assistant

#### For Cursor IDE

Add to `.cursor/mcp.json` or Cursor settings:

```json
{
  "mcpServers": {
    "odoo-search": {
      "command": "/absolute/path/to/odoo_elastic_search/mcp_server/venv/bin/python",
      "args": ["/absolute/path/to/odoo_elastic_search/mcp_server/server.py"],
      "env": {
        "ES_URL": "http://localhost:9200",
        "ES_USER": "elastic",
        "ES_PASS": "elastic",
        "CODE_INDEX": "odoo19_code",
        "DOC_INDEX": "odoo19_docs"
      }
    }
  }
}
```

#### For Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent:

```json
{
  "mcpServers": {
    "odoo-search": {
      "command": "/absolute/path/to/odoo_elastic_search/mcp_server/venv/bin/python",
      "args": ["/absolute/path/to/odoo_elastic_search/mcp_server/server.py"],
      "env": {
        "ES_PASS": "elastic"
      }
    }
  }
}
```

#### For VS Code with GitHub Copilot

Add to VS Code settings.json:

```json
{
  "github.copilot.advanced": {
    "mcp": {
      "servers": {
        "odoo-search": {
          "command": "/absolute/path/to/odoo_elastic_search/mcp_server/venv/bin/python",
          "args": ["/absolute/path/to/odoo_elastic_search/mcp_server/server.py"]
        }
      }
    }
  }
}
```

## 📝 AI Agent Prompts Library

### 🔍 Code Search & Discovery

#### Find Implementation Examples
```
Search the Odoo 19 codebase for all implementations of the Many2one field type.
Show me the top 5 examples from different modules with their full code context 
including line numbers.
```

#### Module Discovery
```
Find all modules in Odoo 18 that implement accounting-related functionality.
List the modules with a brief description of what each module does based on 
its code structure.
```

#### Pattern Search
```
Search for all wizard implementations in Odoo 19. Show me the class definitions,
their methods, and how they're typically structured. Include examples from at 
least 3 different modules.
```

### 📊 Version Comparison

#### Field Changes Analysis
```
Compare the hr.employee model between Odoo 17 and Odoo 18. 
Identify:
1. New fields added in version 18
2. Fields removed or deprecated
3. Changed field types or attributes
4. New computed fields

Present the findings in a structured format with code examples.
```

#### API Changes
```
Analyze API changes in the sale.order model between Odoo 18 and Odoo 19.
Focus on:
- Method signature changes
- New methods added
- Deprecated methods
- Changed decorators (@api.depends, @api.constrains, etc.)
```

#### Module Evolution
```
Compare the 'account' module between Odoo 16, 17, 18, and 19.
Show me:
1. New features added in each version
2. Removed or deprecated features
3. Major refactoring or restructuring
4. Migration considerations for each upgrade path
```

### 🔄 Migration Assistance

#### Upgrade Path Analysis
```
I'm planning to upgrade from Odoo 17 to Odoo 19. Analyze the changes in:
- Core models (res.partner, product.product, sale.order)
- Common fields (name, email, phone, state)
- Security and access rights
- View structures

Provide a migration checklist with potential breaking changes.
```

#### Custom Module Compatibility
```
I have a custom module that extends sale.order with these fields:
[list your custom fields]

Check if these field names or related methods have been added or changed 
in Odoo 19 core. Identify any potential conflicts.
```

### 🏗️ Development Assistance

#### Best Practices Discovery
```
Show me the best practices for implementing computed fields in Odoo 19.
Find real examples from core modules showing:
- @api.depends usage
- Store vs non-stored computed fields
- Performance optimization patterns
- Common pitfalls to avoid
```

#### Security Implementation
```
Find examples of security implementation in Odoo 19 modules.
Show me:
- Record rules (ir.rule)
- Access rights (ir.model.access)
- Field-level security
- Multi-company rules
Include code snippets from at least 3 different modules.
```

#### View Inheritance Patterns
```
Search for examples of view inheritance in Odoo 19.
Show me different patterns for:
- Adding fields to existing views
- Hiding fields
- Modifying field attributes
- Adding buttons or smart buttons
- Creating completely new views that inherit from existing ones
```

### 🐛 Debugging & Troubleshooting

#### Error Investigation
```
Search the Odoo 19 codebase for references to ValidationError with the 
message containing "duplicate". Show me all instances where this error 
is raised and the context around it.
```

#### Performance Optimization
```
Find all instances of large SQL queries or ORM operations in the 
account module of Odoo 19. Identify potential performance bottlenecks 
and show me how similar operations are optimized in other modules.
```

### 📚 Documentation Generation

#### API Documentation
```
Generate documentation for the sale.order model in Odoo 19 including:
- All fields with their types and descriptions
- All methods with their parameters
- Computed fields with their dependencies
- Constraints and validations
Format it as a markdown documentation file.
```

#### Module Documentation
```
Analyze the 'website_sale' module in Odoo 19 and generate comprehensive 
documentation including:
- Module purpose and overview
- Main models and their relationships
- Key features and functionality
- Integration points with other modules
- Configuration options
```

## 🎯 Advanced Agent Workflows

### Workflow 1: Complete Feature Analysis

```
I want to understand how product variants work in Odoo 19.

Step 1: Find all models related to product variants
Step 2: Show me the main product.template and product.product models
Step 3: Explain the relationship between templates and variants
Step 4: Show how variant attributes are defined and used
Step 5: Find examples of variant-specific pricing
Step 6: Provide code examples for creating products with variants programmatically
```

### Workflow 2: Custom Module Development

```
I want to create a custom module for employee certifications.

Step 1: Search for similar functionality in existing modules
Step 2: Show me how hr.employee is typically extended
Step 3: Find examples of Many2many fields with custom domains
Step 4: Show me how to create custom wizards for certificate management
Step 5: Find examples of scheduled actions for certification expiry
Step 6: Provide a complete module structure with code templates
```

### Workflow 3: Migration Planning

```
Plan migration from Odoo 17 to Odoo 19 for custom modules:

Step 1: List all breaking changes between Odoo 17, 18, and 19
Step 2: Identify deprecated features we might be using
Step 3: Find new features we should adopt
Step 4: Check for model/field name conflicts
Step 5: Analyze view structure changes
Step 6: Provide a detailed migration guide with code examples
```

## 🔧 MCP Tools Available

The MCP server provides these tools to AI agents:

### `search_code`
Search Odoo source code with filters.

**Parameters:**
- `query`: Search text
- `module`: Filter by module name
- `version`: Odoo version (16, 17, 18, 19)
- `language`: File type (python, xml, javascript, etc.)
- `size`: Number of results

**Example:**
```json
{
  "query": "class AccountMove",
  "module": "account",
  "version": "19",
  "language": "python",
  "size": 10
}
```

### `search_docs`
Search Odoo documentation.

**Parameters:**
- `query`: Search text
- `doc_kind`: Document type (markdown, rst, text)
- `version`: Odoo version
- `size`: Number of results

### `compare_versions`
Compare code between Odoo versions.

**Parameters:**
- `query`: What to compare
- `version1`: First version
- `version2`: Second version
- `module`: Module to compare (optional)

### `get_module_info`
Get comprehensive module information.

**Parameters:**
- `module`: Module name
- `version`: Odoo version

## 🎨 Custom Agent Configurations

### Configuration for Code Review Agent

```json
{
  "agent_name": "odoo_code_reviewer",
  "capabilities": [
    "search_code",
    "compare_versions",
    "find_patterns"
  ],
  "default_params": {
    "max_results": 20,
    "include_context": true,
    "syntax_highlighting": true
  },
  "prompts": {
    "review_code": "Analyze this code for Odoo best practices...",
    "suggest_improvements": "Suggest improvements based on Odoo core patterns...",
    "check_security": "Check for security issues..."
  }
}
```

### Configuration for Migration Assistant

```json
{
  "agent_name": "odoo_migration_assistant",
  "capabilities": [
    "compare_versions",
    "analyze_changes",
    "generate_migration_guide"
  ],
  "workflow": [
    "Identify deprecated features",
    "Find replacement patterns",
    "Generate migration steps",
    "Validate compatibility"
  ]
}
```

## 📊 Performance Tips

1. **Use specific queries**: More specific searches are faster
2. **Filter by module**: Reduces search scope
3. **Limit results**: Start with fewer results, increase if needed
4. **Use version filters**: Search one version at a time when possible
5. **Cache common queries**: The MCP server caches frequent searches

## 🐛 Troubleshooting

### Agent Can't Connect to MCP Server

```bash
# Check if server is running
ps aux | grep server.py

# Check Elasticsearch connection
curl -u elastic:elastic http://localhost:9200/_cluster/health

# Check logs
tail -f mcp_server/mcp_server.log
```

### Slow Search Responses

- Reduce result size
- Use more specific queries
- Filter by module or file type
- Check Elasticsearch performance

### MCP Server Crashes

```bash
# Check Python dependencies
pip install -r requirements.txt

# Check Elasticsearch status
docker compose ps

# Restart with debug logging
DEBUG=1 python server.py
```

## 📚 Additional Resources

- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Elasticsearch Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
- [Odoo Development Documentation](https://www.odoo.com/documentation/19.0/developer.html)

## 🤝 Community Examples

Share your AI agent prompts and workflows in the [Discussions](https://github.com/sabryyoussef/odoo_elastic_search/discussions) section!

---

**Happy AI-Assisted Odoo Development! 🚀**
