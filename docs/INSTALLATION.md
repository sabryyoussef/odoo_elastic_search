# 📥 Installation Guide

Complete setup guide for Odoo Elasticsearch Search Stack.

## System Requirements

- **OS**: Linux, macOS, or Windows (WSL2)
- **RAM**: Minimum 4GB, recommended 8GB+
- **Disk**: 10GB+ free space (depending on Odoo versions indexed)
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Python**: 3.8 or higher

## Installation Options

Choose one based on your needs:

1. **Quick Start** - Use pre-exported data (fastest)
2. **Full Setup** - Index your own Odoo source code
3. **Hybrid** - Import structure, index specific versions

---

## Option 1: Quick Start (Recommended)

### Step 1: Clone Repository

```bash
git clone https://github.com/sabryyoussef/odoo_elastic_search.git
cd odoo_elastic_search
```

### Step 2: Start Elasticsearch & Kibana

```bash
cd docker
docker compose up -d
```

Wait for services to be healthy (2-3 minutes):

```bash
# Check status
docker compose ps

# Wait for healthy status
watch docker compose ps
```

### Step 3: Import Pre-configured Setup

```bash
cd ../exported_data
# Extract the latest export
tar -xzf export_*.tar.gz
cd export_*

# Create indices
./create_indices.sh

# Import Kibana objects
./import_kibana.sh

# (Optional) Import sample data for testing
./import_sample_data.sh
```

### Step 4: Verify Installation

```bash
# Check Elasticsearch
curl -u elastic:elastic http://localhost:9200/_cat/indices?v

# Access Kibana
# Open http://localhost:5601 in browser
# Login: elastic / elastic
```

**Done!** You can now search Odoo code in Kibana.

---

## Option 2: Full Setup (Index Your Own Code)

### Step 1: Clone and Start Services

```bash
git clone https://github.com/sabryyoussef/odoo_elastic_search.git
cd odoo_elastic_search/docker
docker compose up -d
```

### Step 2: Set Up Python Environment

```bash
cd ../indexer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Odoo Paths

```bash
# Set environment variables for your Odoo installations
export ODOO16_ROOT="/path/to/your/odoo16"
export ODOO17_ROOT="/path/to/your/odoo17"
export ODOO18_ROOT="/path/to/your/odoo18"
export ODOO19_ROOT="/path/to/your/odoo19"

# Optional: Add to your ~/.bashrc or ~/.zshrc
echo 'export ODOO19_ROOT="/path/to/your/odoo19"' >> ~/.bashrc
```

### Step 4: Index Odoo Versions

```bash
# Index one version
python3 index_odoo19.py

# Or index all versions
cd ../scripts
./index_all_versions.sh
```

Indexing time varies:
- **Odoo 16/17/18**: ~10-15 minutes each
- **Odoo 19**: ~20-30 minutes

### Step 5: Import Kibana Configuration

```bash
cd ../exported_data/export_*
./import_kibana.sh
```

---

## Option 3: Docker-Only Setup

If you prefer running everything in Docker:

### Step 1: Create Docker Network

```bash
docker network create odoo-search-network
```

### Step 2: Start with Docker Compose

```bash
git clone https://github.com/sabryyoussef/odoo_elastic_search.git
cd odoo_elastic_search/docker
docker compose up -d
```

### Step 3: Index Using Docker

```bash
# Build indexer container
docker build -t odoo-indexer ../indexer

# Run indexing
docker run --rm \
  --network odoo-search-network \
  -v /path/to/odoo19:/odoo19:ro \
  -e ODOO19_ROOT=/odoo19 \
  -e ES_URL=http://elasticsearch:9200 \
  odoo-indexer python3 index_odoo19.py
```

---

## Post-Installation Configuration

### Configure Elasticsearch Memory

Edit `docker/.env`:

```bash
# For 8GB RAM systems
MEM_LIMIT=2147483648  # 2GB

# For 16GB+ RAM systems
MEM_LIMIT=4294967296  # 4GB
```

Restart services:

```bash
docker compose down
docker compose up -d
```

### Security Configuration

**Important:** Change default passwords in production!

```bash
# Edit docker/.env
ELASTIC_PASSWORD=your_secure_password
KIBANA_PASSWORD=your_secure_password

# Rebuild
docker compose down
docker compose up -d
```

### Firewall Configuration

If accessing remotely:

```bash
# Ubuntu/Debian
sudo ufw allow 9200/tcp  # Elasticsearch
sudo ufw allow 5601/tcp  # Kibana

# CentOS/RHEL
sudo firewall-cmd --add-port=9200/tcp --permanent
sudo firewall-cmd --add-port=5601/tcp --permanent
sudo firewall-cmd --reload
```

---

## MCP Server Setup (For AI Agents)

### Step 1: Install MCP Server

```bash
cd mcp_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Test MCP Server

```bash
python3 test_cursor_mcp.py
```

### Step 3: Configure with Your IDE

See [AI_AGENT_SETUP.md](AI_AGENT_SETUP.md) for detailed configuration.

---

## Troubleshooting Installation

### Elasticsearch Won't Start

```bash
# Check logs
docker compose logs elasticsearch

# Common issue: Memory lock failed
# Fix: Increase vm.max_map_count
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

### Kibana Connection Refused

```bash
# Wait for Elasticsearch to be fully ready
docker compose logs kibana

# Usually needs 2-3 minutes after Elasticsearch starts
```

### Indexing Fails

```bash
# Check Elasticsearch connection
curl -u elastic:elastic http://localhost:9200

# Verify Odoo path exists
ls -la $ODOO19_ROOT

# Check Python dependencies
pip install -r indexer/requirements.txt
```

### Permission Denied Errors

```bash
# Fix script permissions
chmod +x scripts/*.sh
chmod +x exported_data/export_*/*.sh
```

---

## Verification Checklist

After installation, verify:

- [ ] Elasticsearch is running: `curl -u elastic:elastic http://localhost:9200`
- [ ] Kibana is accessible: Open http://localhost:5601
- [ ] Indices are created: Check in Kibana Discover
- [ ] Data views exist: Stack Management → Data Views
- [ ] Search works: Try searching in Discover
- [ ] MCP server works (optional): Run test script

---

## Next Steps

1. **Learn to Search**: Read [USAGE.md](USAGE.md)
2. **Set Up AI Agent**: Follow [AI_AGENT_SETUP.md](AI_AGENT_SETUP.md)
3. **Customize**: Adjust settings in `docker/.env`
4. **Backup**: Run `scripts/export_all.sh` regularly

---

## Getting Help

- **Issues**: https://github.com/sabryyoussef/odoo_elastic_search/issues
- **Discussions**: https://github.com/sabryyoussef/odoo_elastic_search/discussions
- **Documentation**: Check `docs/` folder

**Installation complete! Happy searching! 🎉**
