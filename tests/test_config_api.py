#!/usr/bin/env python3
"""
Test Configuration API
Validate all endpoints and functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
import json

API_BASE = "http://localhost:7996/api/config"
AUTH_TOKEN = "dev-token-placeholder"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

def test_agents():
    """Test agent endpoints"""
    print("\n=== Testing Agent Endpoints ===")
    
    # Create agent
    print("\n1. Creating agent...")
    agent_data = {
        "agent_id": "test_agent_1",
        "name": "Test Agent",
        "model": "gpt-4",
        "enabled": True,
        "max_concurrent_tasks": 2,
        "polling_interval": 30,
        "capabilities": ["code_review", "issue_triage"]
    }
    response = requests.post(f"{API_BASE}/agents", headers=headers, json=agent_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 201
    
    # Get all agents
    print("\n2. Getting all agents...")
    response = requests.get(f"{API_BASE}/agents", headers=headers)
    print(f"Status: {response.status_code}")
    agents = response.json()
    print(f"Found {len(agents)} agent(s)")
    assert response.status_code == 200
    assert len(agents) > 0
    
    # Get specific agent
    print("\n3. Getting specific agent...")
    response = requests.get(f"{API_BASE}/agents/test_agent_1", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Agent: {response.json()['name']}")
    assert response.status_code == 200
    
    # Update agent
    print("\n4. Updating agent...")
    update_data = {
        "enabled": False,
        "max_concurrent_tasks": 3
    }
    response = requests.patch(f"{API_BASE}/agents/test_agent_1", headers=headers, json=update_data)
    print(f"Status: {response.status_code}")
    updated_agent = response.json()
    print(f"Enabled: {updated_agent['enabled']}, Max tasks: {updated_agent['max_concurrent_tasks']}")
    assert response.status_code == 200
    assert updated_agent["enabled"] == False
    
    # Delete agent
    print("\n5. Deleting agent...")
    response = requests.delete(f"{API_BASE}/agents/test_agent_1", headers=headers)
    print(f"Status: {response.status_code}")
    assert response.status_code == 204

def test_repositories():
    """Test repository endpoints"""
    print("\n=== Testing Repository Endpoints ===")
    
    # Create repository
    print("\n1. Creating repository...")
    repo_data = {
        "repo_id": "test_repo_1",
        "owner": "m0nk111",
        "name": "test-repo",
        "enabled": True,
        "auto_assign_issues": True,
        "issue_labels": ["bug", "enhancement"],
        "branch_prefix": "feature"
    }
    response = requests.post(f"{API_BASE}/repositories", headers=headers, json=repo_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 201
    
    # Get all repositories
    print("\n2. Getting all repositories...")
    response = requests.get(f"{API_BASE}/repositories", headers=headers)
    print(f"Status: {response.status_code}")
    repos = response.json()
    print(f"Found {len(repos)} repository(ies)")
    assert response.status_code == 200
    
    # Update repository
    print("\n3. Updating repository...")
    update_data = {
        "enabled": False,
        "branch_prefix": "feat"
    }
    response = requests.patch(f"{API_BASE}/repositories/test_repo_1", headers=headers, json=update_data)
    print(f"Status: {response.status_code}")
    updated_repo = response.json()
    print(f"Enabled: {updated_repo['enabled']}, Branch prefix: {updated_repo['branch_prefix']}")
    assert response.status_code == 200
    
    # Delete repository
    print("\n4. Deleting repository...")
    response = requests.delete(f"{API_BASE}/repositories/test_repo_1", headers=headers)
    print(f"Status: {response.status_code}")
    assert response.status_code == 204

def test_system():
    """Test system configuration endpoints"""
    print("\n=== Testing System Configuration ===")
    
    # Get system config
    print("\n1. Getting system configuration...")
    response = requests.get(f"{API_BASE}/system", headers=headers)
    print(f"Status: {response.status_code}")
    config = response.json()
    print(f"Monitoring: {config['monitoring_enabled']}, Log level: {config['log_level']}")
    assert response.status_code == 200
    
    # Update system config
    print("\n2. Updating system configuration...")
    update_data = {
        "log_level": "DEBUG",
        "max_log_size": 15000
    }
    response = requests.patch(f"{API_BASE}/system", headers=headers, json=update_data)
    print(f"Status: {response.status_code}")
    updated_config = response.json()
    print(f"Log level: {updated_config['log_level']}, Max log size: {updated_config['max_log_size']}")
    assert response.status_code == 200
    assert updated_config["log_level"] == "DEBUG"

def main():
    try:
        print("🧪 Starting Configuration API Tests")
        print(f"API Base URL: {API_BASE}")
        
        test_health()
        test_agents()
        test_repositories()
        test_system()
        
        print("\n✅ All tests PASSED!")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        return 1
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection failed. Is the API server running on port 7996?")
        print("Run: cd /home/flip/agent-forge && python3 api/config_routes.py")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
