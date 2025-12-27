# 🔍 Odoo Elasticsearch & Kibana Search Stack

A comprehensive Elasticsearch-based search solution for Odoo source code and documentation across multiple versions (16, 17, 18, 19). This repository provides everything you need to set up powerful code search capabilities for your Odoo development environment.

[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.11.0-blue.svg)](https://www.elastic.co/)
[![Kibana](https://img.shields.io/badge/Kibana-8.11.0-blue.svg)](https://www.elastic.co/kibana)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

- 🔍 **Multi-Version Support**: Search across Odoo 16, 17, 18, and 19
- 📦 **Smart Chunking**: Large files split into searchable chunks with overlap
- 🎯 **Module Filtering**: Search within specific Odoo modules
- 🔤 **File Type Filtering**: Focus on Python, XML, JavaScript, etc.
- 📊 **Kibana Integration**: Beautiful visualizations and dashboards
- 🤖 **AI Agent Integration**: MCP server for AI-powered code assistance
- ⚡ **Fast Search**: Optimized Elasticsearch indexing
- 🌐 **Web Interface**: User-friendly search interface

## 📊 Index Statistics

Current indices contain:
- **Odoo 16**: ~165K code docs, ~1K documentation docs
- **Odoo 17**: ~166K code docs, ~1K documentation docs  
- **Odoo 18**: ~171K code docs, ~1K documentation docs
- **Odoo 19**: ~268K code docs, ~1K documentation docs

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (for Elasticsearch/Kibana)
- Python 3.8+
- Odoo source code directories (16, 17, 18, 19)

### 1. Clone the Repository

```bash
git clone https://github.com/sabryyoussef/odoo_elastic_search.git
cd odoo_elastic_search
```

### 2. Start Elasticsearch & Kibana

```bash
cd docker
docker compose up -d
```

Wait for services to be healthy (~2-3 minutes):

```bash
docker compose ps
```

### 3. Import Pre-indexed Data (Recommended)

If you have the exported indices:

```bash
# Extract exported data
cd exported_data
tar -xzf odoo_indices_*.tar.gz

# Import to Elasticsearch
cd ../scripts
./import_indices.sh
```

### 4. OR Index Your Own Odoo Source

```bash
# Set Odoo paths
export ODOO16_ROOT="/path/to/your/odoo16"
export ODOO17_ROOT="/path/to/your/odoo17"
export ODOO18_ROOT="/path/to/your/odoo18"
export ODOO19_ROOT="/path/to/your/odoo19"

# Index all versions
./scripts/index_all_versions.sh
```

### 5. Import Kibana Dashboards

```bash
./scripts/import_kibana_objects.sh
```

### 6. Access the Stack

- **Kibana**: http://localhost:5601 (elastic/elastic)
- **Elasticsearch**: http://localhost:9200 (elastic/elastic)

## 🎯 Usage

### Interactive Search

```bash
cd search
./search.sh
```

Follow the prompts to:
1. Select Odoo version (16, 17, 18, 19)
2. Choose search type (code, docs, or both)
3. Filter by module or file type
4. Enter your search query
5. View results with syntax highlighting

### Command Line Search

```bash
# Search for "Many2one" in Odoo 19 code
./search.sh "Many2one" -v 19 -t code

# Search in specific module
./search.sh "wizard" -v 18 -m account

# Search for XML files only
./search.sh "tree view" -v 17 -f xml
```

### Kibana Discover

1. Open http://localhost:5601
2. Go to **Analytics** → **Discover**
3. Select a data view (e.g., "Odoo 19 Code Search")
4. Use the search bar with KQL or Lucene syntax

## 🤖 AI Agent Integration

### MCP Server Setup

The repository includes an MCP (Model Context Protocol) server for AI-powered code assistance:

```bash
cd mcp_server
source venv/bin/activate
python server.py
```

### Configure with Cursor/Claude

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "odoo-search": {
      "command": "/path/to/odoo_elastic_search/mcp_server/venv/bin/python",
      "args": ["/path/to/odoo_elastic_search/mcp_server/server.py"],
      "env": {
        "ES_URL": "http://localhost:9200",
        "ES_USER": "elastic",
        "ES_PASS": "elastic"
      }
    }
  }
}
```

### AI Agent Prompts

Use these prompts with your AI assistant for automated tasks:

#### 🔍 Code Search Prompt
```
Search the Odoo 19 codebase for implementations of the Many2one field. 
Show me examples from the account module with line numbers and context.
```

#### 📊 Version Comparison Prompt
```
Compare the implementation of the birthday field between Odoo 17 and Odoo 18. 
Identify any new features, removed functionality, or significant changes.
```

#### 🔄 Migration Analysis Prompt
```
Analyze the differences in the sale.order model between Odoo 18 and Odoo 19.
Focus on field changes, method signatures, and deprecated functionality.
```

#### 📦 Module Discovery Prompt
```
Find all modules in Odoo 19 that implement custom wizards. 
Show me the wizard class definitions and their associated views.
```

## 📂 Project Structure

```
odoo_elastic_search/
├── docker/                    # Docker Compose setup
│   ├── docker-compose.yml
│   └── .env
├── indexer/                   # Indexing scripts
│   ├── index_odoo16.py
│   ├── index_odoo17.py
│   ├── index_odoo18.py
│   ├── index_odoo19.py
│   └── requirements.txt
├── mcp_server/               # MCP server for AI agents
│   ├── server.py
│   ├── requirements.txt
│   └── README.md
├── search/                   # Search interfaces
│   ├── search.sh
│   ├── easy_search.py
│   └── test_search.py
├── scripts/                  # Utility scripts
│   ├── export_indices.sh
│   ├── import_indices.sh
│   ├── import_kibana_objects.sh
│   └── index_all_versions.sh
├── exported_data/           # Pre-indexed data (optional)
│   ├── indices/
│   └── kibana_objects.ndjson
├── docs/                    # Documentation
│   ├── INSTALLATION.md
│   ├── USAGE.md
│   ├── API.md
│   └── TROUBLESHOOTING.md
└── README.md
```

## 🔧 Configuration

### Elasticsearch Settings

Edit `docker/.env`:

```bash
ELASTIC_PASSWORD=elastic
KIBANA_PASSWORD=elastic
STACK_VERSION=8.11.0
CLUSTER_NAME=odoo-search-cluster
ES_PORT=9200
KIBANA_PORT=5601
MEM_LIMIT=2147483648  # 2GB
```

### Indexing Configuration

Edit indexer environment variables:

```bash
ES_URL=http://localhost:9200
ES_USER=elastic
ES_PASS=elastic
CHUNK_LINES=200        # Lines per chunk
OVERLAP=30             # Chunk overlap
```

## 📖 Documentation

- [Installation Guide](docs/INSTALLATION.md) - Detailed setup instructions
- [Usage Guide](docs/USAGE.md) - How to search and use features
- [API Documentation](docs/API.md) - Elasticsearch API and MCP endpoints
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## 🎯 Use Cases

### 1. Finding Implementation Examples
Search for specific Odoo patterns across versions to understand best practices.

### 2. Migration Planning
Compare code between versions to plan your Odoo upgrades.

### 3. Custom Module Development
Find similar implementations to use as templates for your custom modules.

### 4. Bug Investigation
Search for error messages or problematic code patterns across the codebase.

### 5. Learning Odoo Framework
Explore how Odoo implements various features internally.

## 🚢 Deployment Options

### Option 1: Local Development
Perfect for individual developers working on Odoo projects.

### Option 2: Team Server
Deploy on a shared server for your development team.

### Option 3: Cloud Deployment
Use cloud providers (AWS, GCP, Azure) for scalable search infrastructure.

## 🔐 Security

- Change default passwords in production
- Use HTTPS for remote access
- Configure firewall rules
- Enable Elasticsearch security features
- Use API keys for programmatic access

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Odoo Community for the excellent ERP framework
- Elastic for the powerful search engine
- Contributors and users of this project

## 📞 Support

- **Issues**: https://github.com/sabryyoussef/odoo_elastic_search/issues
- **Discussions**: https://github.com/sabryyoussef/odoo_elastic_search/discussions
- **Email**: support@example.com

## 🗺️ Roadmap

- [ ] GraphQL API for advanced queries
- [ ] Real-time indexing with file watchers
- [ ] Support for Odoo 20+
- [ ] Enhanced AI-powered code analysis
- [ ] Custom Kibana plugins
- [ ] Multi-cluster federation
- [ ] Advanced security features

---

**Made with ❤️ for the Odoo Community**

For detailed AI agent integration, see [AI_AGENT_SETUP.md](docs/AI_AGENT_SETUP.md)
