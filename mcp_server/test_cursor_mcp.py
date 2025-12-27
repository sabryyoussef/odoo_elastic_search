#!/usr/bin/env python3
"""
Test script to verify Cursor MCP integration works
"""

import subprocess
import json
import sys
import time

def test_mcp_server():
    """Test if MCP server can respond to requests"""
    
    print("🧪 Testing Cursor MCP Integration\n")
    print("=" * 60)
    
    # Test 1: Check dependencies
    print("\n1️⃣ Checking dependencies...")
    
    try:
        import mcp
        print("   ✅ mcp package installed")
    except ImportError:
        print("   ❌ mcp package not found")
        print("   Run: pip install mcp")
        return False
    
    try:
        import elasticsearch
        print("   ✅ elasticsearch package installed")
    except ImportError:
        print("   ❌ elasticsearch package not found")
        print("   Run: pip install elasticsearch")
        return False
    
    # Test 2: Elasticsearch connection
    print("\n2️⃣ Testing Elasticsearch connection...")
    
    try:
        import requests
        response = requests.get(
            "http://localhost:9200/_cluster/health",
            auth=("elastic", "elastic"),
            timeout=5
        )
        
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Elasticsearch status: {health['status']}")
            print(f"   ✅ Cluster name: {health['cluster_name']}")
        else:
            print(f"   ❌ Elasticsearch returned status {response.status_code}")
            print("   Make sure Elasticsearch is running:")
            print("   cd docker && docker compose up -d")
            return False
            
    except Exception as e:
        print(f"   ❌ Cannot connect to Elasticsearch: {e}")
        print("   Make sure Elasticsearch is running:")
        print("   cd docker && docker compose up -d")
        return False
    
    # Test 3: Index exists
    print("\n3️⃣ Testing index availability...")
    
    try:
        response = requests.get(
            "http://localhost:9200/odoo19_code/_count",
            auth=("elastic", "elastic"),
            timeout=5
        )
        
        if response.status_code == 200:
            count = response.json()['count']
            print(f"   ✅ Index 'odoo19_code' has {count:,} documents")
            
            if count == 0:
                print("   ⚠️  Index is empty, run indexer first")
                return False
        else:
            print(f"   ❌ Index not accessible")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking index: {e}")
        return False
    
    # Test 4: Test search query
    print("\n4️⃣ Testing search functionality...")
    
    try:
        response = requests.post(
            "http://localhost:9200/odoo19_code/_search",
            auth=("elastic", "elastic"),
            headers={"Content-Type": "application/json"},
            json={
                "query": {"match": {"content": "Many2one"}},
                "size": 3,
                "_source": ["path", "module", "start_line", "end_line"]
            },
            timeout=5
        )
        
        if response.status_code == 200:
            results = response.json()
            hits = results['hits']['hits']
            total = results['hits']['total']['value']
            
            print(f"   ✅ Search works! Found {total} results for 'Many2one'")
            print(f"   ✅ Sample result: {hits[0]['_source']['path']}")
        else:
            print(f"   ❌ Search failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing search: {e}")
        return False
    
    # Test 5: MCP Server startup test
    print("\n5️⃣ Testing MCP server startup...")
    
    try:
        # Just try to import and start server
        print("   Starting server for 3 seconds...")
        proc = subprocess.Popen(
            ["python3", "server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for startup
        time.sleep(3)
        
        # Check if process is still running
        if proc.poll() is None:
            print("   ✅ MCP server started successfully")
            proc.terminate()
            proc.wait(timeout=5)
            
            # Read stderr to see connection messages
            _, stderr = proc.communicate()
            if "Connected to Elasticsearch" in stderr:
                print("   ✅ Server connected to Elasticsearch")
        else:
            _, stderr = proc.communicate()
            print(f"   ❌ Server exited unexpectedly")
            print(f"   Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error starting server: {e}")
        try:
            proc.kill()
        except:
            pass
        return False
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Cursor MCP integration is ready.")
    print("\n📝 Next steps:")
    print("   1. Create Cursor config file")
    print("   2. Add this configuration:")
    print()
    print("   File: ~/.config/cursor/mcp_config.json")
    print()
    print('   {')
    print('     "mcpServers": {')
    print('       "odoo19-search": {')
    print('         "command": "python3",')
    print('         "args": [')
    print('           "/home/sabry3/sabry_backup/odoo_base/base_odoo_19/odoo19_search_stack/mcp_server/server.py"')
    print('         ],')
    print('         "env": {')
    print('           "ES_URL": "http://localhost:9200",')
    print('           "ES_USER": "elastic",')
    print('           "ES_PASS": "elastic"')
    print('         }')
    print('       }')
    print('     }')
    print('   }')
    print()
    print("   3. Restart Cursor")
    print("   4. Try: 'Search for Many2one in Odoo code'")
    
    return True


if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)
