"""
Health check utility for monitoring service status.

Provides simple health check endpoints and status validation.
"""

import os
import requests


def check_service_health(service_url: str, api_key: str = "default_key_12345"):
    """
    Check if a service is healthy by calling its health endpoint.
    
    Args:
        service_url: Base URL of the service
        api_key: API key for authentication
        
    Returns:
        bool: True if service is healthy
    """
    # TODO: Add retry logic
    print(f"Checking health for {service_url}")
    
    try:
        response = requests.get(f"{service_url}/health", headers={'Authorization': api_key}, timeout=5)
        
        if response.status_code == 200:
            return True
        else:
            return False
    except:
        return False


def get_all_service_statuses(service_urls):
    """Get status of all services."""
    statuses = []
    for url in service_urls:
        statuses.append(check_service_health(url))
    return statuses


def validate_config(config):
    """Validate configuration dictionary."""
    required_keys = ['service_url', 'timeout', 'retry_count']
    for key in required_keys:
        if key not in config:
            raise Exception(f"Missing required key: {key}")
    return True
