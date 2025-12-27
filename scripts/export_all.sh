#!/bin/bash

# Export Odoo Elasticsearch Indices and Kibana Objects
# This script exports all Odoo indices and Kibana configurations for easy cloning

set -e

EXPORT_DIR="exported_data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
EXPORT_SUBDIR="$EXPORT_DIR/export_$TIMESTAMP"

ES_URL="${ES_URL:-http://localhost:9200}"
ES_USER="${ES_USER:-elastic}"
ES_PASS="${ES_PASS:-elastic}"
KIBANA_URL="${KIBANA_URL:-http://localhost:5601}"

echo "🎯 Odoo Elasticsearch Export Script"
echo "===================================="
echo "Elasticsearch: $ES_URL"
echo "Kibana: $KIBANA_URL"
echo "Export Directory: $EXPORT_SUBDIR"
echo ""

# Create export directories
mkdir -p "$EXPORT_SUBDIR/indices"
mkdir -p "$EXPORT_SUBDIR/mappings"
mkdir -p "$EXPORT_SUBDIR/kibana"

# Export index mappings and settings
echo "📋 Exporting index mappings and settings..."
for index in odoo16_code odoo16_docs odoo17_code odoo17_docs odoo18_code odoo18_docs odoo19_code odoo19_docs; do
    if curl -s -u "$ES_USER:$ES_PASS" "$ES_URL/$index" | grep -q "\"$index\""; then
        echo "  📦 Exporting $index mapping..."
        curl -s -u "$ES_USER:$ES_PASS" "$ES_URL/$index/_mapping" | \
            jq ".$index" > "$EXPORT_SUBDIR/mappings/${index}_mapping.json"
        
        echo "  ⚙️  Exporting $index settings..."
        curl -s -u "$ES_USER:$ES_PASS" "$ES_URL/$index/_settings" | \
            jq ".$index.settings" > "$EXPORT_SUBDIR/mappings/${index}_settings.json"
        
        # Get document count
        count=$(curl -s -u "$ES_USER:$ES_PASS" "$ES_URL/$index/_count" | jq '.count')
        echo "  ✅ $index: $count documents"
    else
        echo "  ⏭️  Skipping $index (not found)"
    fi
done

# Export sample documents (for testing import)
echo ""
echo "📄 Exporting sample documents..."
for index in odoo16_code odoo17_code odoo18_code odoo19_code; do
    if curl -s -u "$ES_USER:$ES_PASS" "$ES_URL/$index" | grep -q "\"$index\""; then
        echo "  📦 Exporting 100 sample docs from $index..."
        curl -s -u "$ES_USER:$ES_PASS" "$ES_URL/$index/_search?size=100" | \
            jq '{hits: .hits.hits}' > "$EXPORT_SUBDIR/indices/${index}_sample.json"
    fi
done

# Export Kibana data views
echo ""
echo "🎨 Exporting Kibana data views..."
curl -s -X GET "$KIBANA_URL/api/data_views" \
    -H "kbn-xsrf: true" \
    -u "$ES_USER:$ES_PASS" | \
    jq '.data_view' > "$EXPORT_SUBDIR/kibana/data_views.json"

# Export all Kibana saved objects
echo "🎨 Exporting Kibana saved objects..."
curl -s -X POST "$KIBANA_URL/api/saved_objects/_export" \
    -H "kbn-xsrf: true" \
    -H "Content-Type: application/json" \
    -u "$ES_USER:$ES_PASS" \
    -d '{
        "type": ["data-view", "dashboard", "visualization", "search", "index-pattern"],
        "includeReferencesDeep": true
    }' \
    --output "$EXPORT_SUBDIR/kibana/saved_objects.ndjson"

# Create index recreation scripts
echo ""
echo "📝 Creating index recreation scripts..."

cat > "$EXPORT_SUBDIR/create_indices.sh" << 'EOF'
#!/bin/bash

# Recreate Odoo indices in new Elasticsearch cluster

ES_URL="${ES_URL:-http://localhost:9200}"
ES_USER="${ES_USER:-elastic}"
ES_PASS="${ES_PASS:-elastic}"

echo "🏗️  Creating Odoo indices in $ES_URL"

for mapping_file in mappings/*_mapping.json; do
    index_name=$(basename "$mapping_file" _mapping.json)
    settings_file="mappings/${index_name}_settings.json"
    
    echo "📦 Creating index: $index_name"
    
    # Delete if exists
    curl -s -X DELETE -u "$ES_USER:$ES_PASS" "$ES_URL/$index_name" 2>/dev/null || true
    
    # Create with mapping and settings
    curl -s -X PUT -u "$ES_USER:$ES_PASS" "$ES_URL/$index_name" \
        -H "Content-Type: application/json" \
        -d "{
            \"settings\": $(cat "$settings_file"),
            \"mappings\": $(cat "$mapping_file" | jq '.mappings')
        }" | jq '.acknowledged'
done

echo "✅ All indices created!"
EOF

chmod +x "$EXPORT_SUBDIR/create_indices.sh"

# Create import script
cat > "$EXPORT_SUBDIR/import_sample_data.sh" << 'EOF'
#!/bin/bash

# Import sample data to new Elasticsearch cluster

ES_URL="${ES_URL:-http://localhost:9200}"
ES_USER="${ES_USER:-elastic}"
ES_PASS="${ES_PASS:-elastic}"

echo "📥 Importing sample documents to $ES_URL"

for sample_file in indices/*_sample.json; do
    index_name=$(basename "$sample_file" _sample.json)
    
    echo "📦 Importing samples to: $index_name"
    
    # Extract and bulk index documents
    jq -r '.hits[] | "{\"index\":{\"_index\":\"'$index_name'\"}}\n\(._source)"' "$sample_file" | \
        curl -s -X POST -u "$ES_USER:$ES_PASS" "$ES_URL/_bulk" \
        -H "Content-Type: application/x-ndjson" \
        --data-binary @- | jq '.errors'
done

echo "✅ Sample data imported!"
EOF

chmod +x "$EXPORT_SUBDIR/import_sample_data.sh"

# Create Kibana import script
cat > "$EXPORT_SUBDIR/import_kibana.sh" << 'EOF'
#!/bin/bash

# Import Kibana objects to new Kibana instance

KIBANA_URL="${KIBANA_URL:-http://localhost:5601}"
KIBANA_USER="${KIBANA_USER:-elastic}"
KIBANA_PASS="${KIBANA_PASS:-elastic}"

echo "🎨 Importing Kibana objects to $KIBANA_URL"

curl -X POST "$KIBANA_URL/api/saved_objects/_import" \
    -H "kbn-xsrf: true" \
    -u "$KIBANA_USER:$KIBANA_PASS" \
    --form file=@kibana/saved_objects.ndjson \
    --form createNewCopies=false

echo "✅ Kibana objects imported!"
EOF

chmod +x "$EXPORT_SUBDIR/import_kibana.sh"

# Create README for export
cat > "$EXPORT_SUBDIR/README.md" << 'EOF'
# Odoo Elasticsearch Export

This export contains:
- Index mappings and settings
- Sample documents for testing
- Kibana data views and saved objects
- Import scripts for quick setup

## Quick Setup on New Machine

1. **Start Elasticsearch and Kibana:**
   ```bash
   cd ../docker
   docker compose up -d
   ```

2. **Create indices:**
   ```bash
   ./create_indices.sh
   ```

3. **Import sample data (optional):**
   ```bash
   ./import_sample_data.sh
   ```

4. **Import Kibana objects:**
   ```bash
   ./import_kibana.sh
   ```

5. **Full data indexing:**
   ```bash
   cd ../indexer
   export ODOO19_ROOT=/path/to/your/odoo19
   python3 index_odoo19.py
   ```

## Files Included

- `mappings/*.json` - Index mappings and settings
- `indices/*_sample.json` - Sample documents for testing
- `kibana/saved_objects.ndjson` - Kibana dashboards and data views
- `*.sh` - Import scripts

## Configuration

Set these environment variables before running scripts:

```bash
export ES_URL=http://localhost:9200
export ES_USER=elastic
export ES_PASS=elastic
export KIBANA_URL=http://localhost:5601
```
EOF

# Create archive
echo ""
echo "📦 Creating archive..."
cd "$EXPORT_DIR"
tar -czf "export_${TIMESTAMP}.tar.gz" "export_$TIMESTAMP"
cd ..

echo ""
echo "✅ Export completed successfully!"
echo ""
echo "📁 Export location: $EXPORT_SUBDIR"
echo "📦 Archive: $EXPORT_DIR/export_${TIMESTAMP}.tar.gz"
echo ""
echo "📊 Export summary:"
echo "  • Index mappings: $(ls -1 $EXPORT_SUBDIR/mappings/*_mapping.json | wc -l) files"
echo "  • Sample data: $(ls -1 $EXPORT_SUBDIR/indices/*_sample.json 2>/dev/null | wc -l) files"
echo "  • Kibana objects: $(wc -l < $EXPORT_SUBDIR/kibana/saved_objects.ndjson) objects"
echo ""
echo "🚀 To use on another machine:"
echo "  1. Copy export_${TIMESTAMP}.tar.gz to the new machine"
echo "  2. Extract: tar -xzf export_${TIMESTAMP}.tar.gz"
echo "  3. Follow instructions in export_$TIMESTAMP/README.md"
