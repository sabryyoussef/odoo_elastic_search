#!/usr/bin/env python3
"""
Odoo 19 Search Stack - Interactive Test Script
Demonstrates various search capabilities with real examples
"""

import json
import requests
from requests.auth import HTTPBasicAuth

ES_HOST = "localhost"
ES_PORT = "9200"
ES_USER = "elastic"
ES_PASS = "elastic"
BASE_URL = f"http://{ES_HOST}:{ES_PORT}"

def search(query, size=5):
    """Execute search query and return results"""
    url = f"{BASE_URL}/odoo19_code/_search"
    response = requests.post(
        url,
        auth=HTTPBasicAuth(ES_USER, ES_PASS),
        headers={'Content-Type': 'application/json'},
        json=query
    )
    return response.json()

def print_results(results, show_content=False):
    """Pretty print search results"""
    hits = results.get('hits', {}).get('hits', [])
    total = results.get('hits', {}).get('total', {}).get('value', 0)
    took = results.get('took', 0)
    
    print(f"\n📊 Found {total} results (showing {len(hits)}) - took {took}ms\n")
    
    for i, hit in enumerate(hits, 1):
        source = hit['_source']
        score = hit['_score']
        
        print(f"{i}. [Score: {score:.2f}] {source.get('module', 'unknown')}")
        print(f"   📁 {source.get('path', 'N/A')}")
        print(f"   📍 Lines: {source.get('start_line', '?')}-{source.get('end_line', '?')}")
        
        if show_content:
            content = source.get('content', '')[:200]
            print(f"   📝 {content}...")
        print()

def test_1_simple_search():
    """Test 1: Simple text search"""
    print("\n" + "="*80)
    print("TEST 1: Simple Search - Finding 'Many2one' in code")
    print("="*80)
    
    query = {
        "query": {
            "match": {
                "content": "Many2one"
            }
        },
        "size": 5,
        "_source": ["path", "module", "start_line", "end_line", "language"]
    }
    
    results = search(query)
    print_results(results)

def test_2_module_specific():
    """Test 2: Search within specific module"""
    print("\n" + "="*80)
    print("TEST 2: Module-Specific Search - 'Many2one' in 'account' module")
    print("="*80)
    
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"content": "Many2one"}},
                    {"term": {"module.keyword": "account"}}
                ]
            }
        },
        "size": 5,
        "_source": ["path", "module", "start_line", "end_line"]
    }
    
    results = search(query)
    print_results(results)

def test_3_file_type_filter():
    """Test 3: Search specific file types"""
    print("\n" + "="*80)
    print("TEST 3: File Type Filter - JavaScript files with 'widget'")
    print("="*80)
    
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"content": "widget"}},
                    {"term": {"language": "javascript"}}
                ]
            }
        },
        "size": 5,
        "_source": ["path", "module", "start_line", "end_line", "language"]
    }
    
    results = search(query)
    print_results(results)

def test_4_phrase_search():
    """Test 4: Exact phrase matching"""
    print("\n" + "="*80)
    print("TEST 4: Phrase Search - Exact match 'def create'")
    print("="*80)
    
    query = {
        "query": {
            "match_phrase": {
                "content": "def create"
            }
        },
        "size": 5,
        "_source": ["path", "module", "start_line", "end_line"]
    }
    
    results = search(query)
    print_results(results)

def test_5_wildcard_path():
    """Test 5: Wildcard path search"""
    print("\n" + "="*80)
    print("TEST 5: Wildcard Path - Files in 'models' directories")
    print("="*80)
    
    query = {
        "query": {
            "wildcard": {
                "path": "*/models/*.py"
            }
        },
        "size": 5,
        "_source": ["path", "module", "start_line", "end_line"]
    }
    
    results = search(query)
    print_results(results)

def test_6_aggregation():
    """Test 6: Aggregation - Top modules by code volume"""
    print("\n" + "="*80)
    print("TEST 6: Aggregation - Top 10 modules by document count")
    print("="*80)
    
    query = {
        "size": 0,
        "aggs": {
            "top_modules": {
                "terms": {
                    "field": "module.keyword",
                    "size": 10,
                    "order": {"_count": "desc"}
                }
            }
        }
    }
    
    results = search(query)
    buckets = results.get('aggregations', {}).get('top_modules', {}).get('buckets', [])
    
    print("\n📊 Top 10 Modules:\n")
    for i, bucket in enumerate(buckets, 1):
        module = bucket['key']
        count = bucket['doc_count']
        print(f"{i:2}. {module:30} → {count:,} code chunks")
    print()

def test_7_complex_query():
    """Test 7: Complex multi-condition query"""
    print("\n" + "="*80)
    print("TEST 7: Complex Query - Python models with 'compute' methods")
    print("="*80)
    
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"content": "compute"}},
                    {"term": {"language": "python"}},
                    {"wildcard": {"path": "*/models/*.py"}}
                ]
            }
        },
        "size": 5,
        "_source": ["path", "module", "start_line", "end_line"]
    }
    
    results = search(query)
    print_results(results)

def test_8_boosted_search():
    """Test 8: Boosted multi-field search"""
    print("\n" + "="*80)
    print("TEST 8: Boosted Search - 'invoice' prioritizing file paths")
    print("="*80)
    
    query = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"content": {"query": "invoice", "boost": 1}}},
                    {"match": {"path": {"query": "invoice", "boost": 3}}}
                ]
            }
        },
        "size": 5,
        "_source": ["path", "module", "start_line", "end_line"]
    }
    
    results = search(query)
    print_results(results)

def test_9_line_range():
    """Test 9: Search within specific line ranges"""
    print("\n" + "="*80)
    print("TEST 9: Line Range Filter - Classes defined in first 100 lines")
    print("="*80)
    
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"content": "class"}},
                    {"range": {"start_line": {"gte": 1, "lte": 100}}}
                ]
            }
        },
        "size": 5,
        "_source": ["path", "module", "start_line", "end_line"]
    }
    
    results = search(query)
    print_results(results)

def test_10_content_preview():
    """Test 10: Search with content preview"""
    print("\n" + "="*80)
    print("TEST 10: Content Preview - Show actual code snippets")
    print("="*80)
    
    query = {
        "query": {
            "match": {
                "content": "api.depends"
            }
        },
        "size": 3,
        "_source": ["path", "module", "start_line", "end_line", "content"]
    }
    
    results = search(query)
    print_results(results, show_content=True)

def main():
    """Run all tests"""
    print("\n" + "🔍 " + "="*76)
    print("🔍  Odoo 19 Search Stack - Interactive Test Suite")
    print("🔍 " + "="*76)
    
    # Run all tests
    test_1_simple_search()
    test_2_module_specific()
    test_3_file_type_filter()
    test_4_phrase_search()
    test_5_wildcard_path()
    test_6_aggregation()
    test_7_complex_query()
    test_8_boosted_search()
    test_9_line_range()
    test_10_content_preview()
    
    print("\n" + "="*80)
    print("✅ All tests completed successfully!")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
