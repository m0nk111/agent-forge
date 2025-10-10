"""Health Check Utility Module.

Provides utilities for checking service health by attempting connections
and measuring latency.

Author: Agent-Forge Autonomous Pipeline
Date: 2025-10-10
"""

import socket
import time
from typing import Dict


def check_service_health(service_name: str, port: int) -> Dict[str, any]:
    """
    Check if a service is healthy by attempting connection.
    
    Args:
        service_name: Name of the service (hostname or IP)
        port: Port number to check
        
    Returns:
        dict with keys:
            - 'healthy' (bool): Whether the service is reachable
            - 'message' (str): Status message
            - 'latency_ms' (float): Connection latency in milliseconds (0 if failed)
    
    Examples:
        >>> result = check_service_health('localhost', 8080)
        >>> result['healthy']
        True
        >>> result['latency_ms'] > 0
        True
    """
    result = {
        'healthy': False,
        'message': '',
        'latency_ms': 0.0
    }
    
    # Validate inputs
    if not service_name or not isinstance(service_name, str):
        result['message'] = 'Invalid service name'
        return result
    
    if not isinstance(port, int) or port < 1 or port > 65535:
        result['message'] = f'Invalid port number: {port}'
        return result
    
    # Attempt connection with timeout
    sock = None
    try:
        start_time = time.time()
        
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)  # 5 second timeout
        
        # Attempt connection
        sock.connect((service_name, port))
        
        # Calculate latency
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000.0
        
        # Success
        result['healthy'] = True
        result['message'] = f'Service {service_name}:{port} is reachable'
        result['latency_ms'] = round(latency_ms, 2)
        
    except socket.timeout:
        result['message'] = f'Connection to {service_name}:{port} timed out'
        
    except socket.gaierror as e:
        result['message'] = f'DNS resolution failed for {service_name}: {e}'
        
    except ConnectionRefusedError:
        result['message'] = f'Connection refused by {service_name}:{port}'
        
    except OSError as e:
        result['message'] = f'Network error: {e}'
        
    except Exception as e:
        result['message'] = f'Unexpected error: {e}'
        
    finally:
        # Always close socket
        if sock:
            try:
                sock.close()
            except:
                pass
    
    return result
