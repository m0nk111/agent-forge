#!/usr/bin/env python3
"""CLI tool for monitoring Agent-Forge agents and viewing logs.

Usage:
    # List all agents
    ./monitor-cli.py list
    
    # Watch agents in real-time
    ./monitor-cli.py watch
    
    # View logs for specific agent
    ./monitor-cli.py logs <agent_id>
    
    # Stream logs in real-time
    ./monitor-cli.py logs <agent_id> --follow
    
    # Show detailed agent info
    ./monitor-cli.py info <agent_id>
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from typing import Optional
import requests

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    print("⚠️  Warning: websockets not installed. Real-time features disabled.")
    print("   Install with: pip install websockets")


# Configuration
API_BASE = "http://192.168.1.26:7997"
WS_URL = "ws://192.168.1.26:7997/ws/monitor"


# Colors
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'


def format_timestamp(ts: float) -> str:
    """Format Unix timestamp to readable string."""
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


def format_status(status: str) -> str:
    """Format status with color."""
    status_colors = {
        'idle': Colors.BLUE,
        'working': Colors.GREEN,
        'error': Colors.RED,
        'offline': Colors.GRAY
    }
    color = status_colors.get(status.lower(), Colors.WHITE)
    return f"{color}{status.upper()}{Colors.RESET}"


def format_agent_short(agent: dict) -> str:
    """Format agent for list view (one line)."""
    agent_id = agent['agent_id']
    name = agent['agent_name']
    status = format_status(agent['status'])
    task = agent.get('current_task', 'None')
    
    return f"{Colors.BOLD}{agent_id}{Colors.RESET} | {name} | {status} | {task}"


def format_agent_detailed(agent: dict) -> str:
    """Format agent with full details."""
    lines = [
        f"\n{Colors.BOLD}{Colors.CYAN}Agent: {agent['agent_name']}{Colors.RESET}",
        f"{'─' * 70}",
        f"ID:              {agent['agent_id']}",
        f"Status:          {format_status(agent['status'])}",
        f"Current Task:    {agent.get('current_task', 'None')}",
        f"Progress:        {agent.get('progress', 0):.1f}%",
        f"Phase:           {agent.get('phase', 'N/A')}",
    ]
    
    if agent.get('current_issue'):
        lines.append(f"Current Issue:   #{agent['current_issue']}")
    
    if agent.get('current_pr'):
        lines.append(f"Current PR:      #{agent['current_pr']}")
    
    if agent.get('started_at'):
        started = format_timestamp(agent['started_at'])
        lines.append(f"Started At:      {started}")
    
    last_update = format_timestamp(agent['last_update'])
    lines.append(f"Last Update:     {last_update}")
    
    if agent.get('error_message'):
        lines.append(f"{Colors.RED}Error:           {agent['error_message']}{Colors.RESET}")
    
    lines.extend([
        f"\n{Colors.BOLD}Metrics:{Colors.RESET}",
        f"  CPU:           {agent.get('cpu_usage', 0):.1f}%",
        f"  Memory:        {agent.get('memory_usage', 0):.1f}%",
        f"  API Calls:     {agent.get('api_calls', 0)}",
        f"  Rate Limit:    {agent.get('api_rate_limit_remaining', 0)}",
    ])
    
    return '\n'.join(lines)


def list_agents():
    """List all connected agents."""
    try:
        response = requests.get(f"{API_BASE}/api/agents", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        agents = data.get('agents', [])
        total = data.get('total', 0)
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}Agent-Forge Agents ({total}){Colors.RESET}")
        print("=" * 80)
        
        if not agents:
            print(f"{Colors.YELLOW}No agents connected{Colors.RESET}")
            return
        
        for agent in agents:
            print(format_agent_short(agent))
        
        print()
        
    except requests.RequestException as e:
        print(f"{Colors.RED}Error connecting to API: {e}{Colors.RESET}")
        sys.exit(1)


def show_agent_info(agent_id: str):
    """Show detailed info for specific agent."""
    try:
        response = requests.get(f"{API_BASE}/api/agents/{agent_id}/status", timeout=5)
        response.raise_for_status()
        agent = response.json()
        
        print(format_agent_detailed(agent))
        print()
        
    except requests.HTTPException as e:
        if e.response.status_code == 404:
            print(f"{Colors.RED}Agent '{agent_id}' not found{Colors.RESET}")
        else:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"{Colors.RED}Error connecting to API: {e}{Colors.RESET}")
        sys.exit(1)


def show_logs(agent_id: str, limit: int = 50):
    """Show logs for specific agent."""
    try:
        response = requests.get(
            f"{API_BASE}/api/agents/{agent_id}/logs",
            params={'limit': limit},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        logs = data.get('logs', [])
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}Logs for {agent_id} (last {len(logs)}){Colors.RESET}")
        print("=" * 80)
        
        if not logs:
            print(f"{Colors.YELLOW}No logs available{Colors.RESET}")
            return
        
        for log in logs:
            timestamp = format_timestamp(log['timestamp'])
            level = log['level']
            message = log['message']
            
            # Color by level
            level_colors = {
                'DEBUG': Colors.GRAY,
                'INFO': Colors.BLUE,
                'WARNING': Colors.YELLOW,
                'ERROR': Colors.RED,
            }
            level_color = level_colors.get(level, Colors.WHITE)
            
            print(f"{Colors.GRAY}{timestamp}{Colors.RESET} {level_color}[{level}]{Colors.RESET} {message}")
        
        print()
        
    except requests.HTTPException as e:
        if e.response.status_code == 404:
            print(f"{Colors.RED}Agent '{agent_id}' not found{Colors.RESET}")
        else:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"{Colors.RED}Error connecting to API: {e}{Colors.RESET}")
        sys.exit(1)


async def watch_agents():
    """Watch agents in real-time via WebSocket."""
    if not HAS_WEBSOCKETS:
        print(f"{Colors.RED}WebSocket support required for watch mode{Colors.RESET}")
        print("Install with: pip install websockets")
        sys.exit(1)
    
    print(f"{Colors.CYAN}Connecting to {WS_URL}...{Colors.RESET}")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print(f"{Colors.GREEN}✓ Connected{Colors.RESET}")
            print(f"\n{Colors.BOLD}Watching agents (Ctrl+C to stop)...{Colors.RESET}\n")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type')
                    
                    if msg_type == 'initial_state':
                        agents = data.get('data', {}).get('agents', [])
                        print(f"{Colors.CYAN}Initial state: {len(agents)} agents{Colors.RESET}")
                        for agent in agents:
                            print(f"  {format_agent_short(agent)}")
                    
                    elif msg_type == 'agent_update':
                        agent = data.get('data', {})
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"{Colors.GRAY}[{timestamp}]{Colors.RESET} {format_agent_short(agent)}")
                    
                    elif msg_type == 'log_entry':
                        log = data.get('data', {})
                        agent_id = data.get('agent_id', 'unknown')
                        timestamp = format_timestamp(log.get('timestamp', 0))
                        level = log.get('level', 'INFO')
                        message = log.get('message', '')
                        
                        level_colors = {
                            'DEBUG': Colors.GRAY,
                            'INFO': Colors.BLUE,
                            'WARNING': Colors.YELLOW,
                            'ERROR': Colors.RED,
                        }
                        level_color = level_colors.get(level, Colors.WHITE)
                        
                        print(f"{Colors.GRAY}{timestamp}{Colors.RESET} {Colors.MAGENTA}[{agent_id}]{Colors.RESET} {level_color}{level}{Colors.RESET}: {message}")
                
                except json.JSONDecodeError:
                    pass
                except KeyboardInterrupt:
                    break
    
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        sys.exit(1)


async def follow_logs(agent_id: str):
    """Follow logs for specific agent in real-time."""
    if not HAS_WEBSOCKETS:
        print(f"{Colors.RED}WebSocket support required for follow mode{Colors.RESET}")
        print("Install with: pip install websockets")
        sys.exit(1)
    
    ws_url = f"ws://192.168.1.26:7997/ws/logs/{agent_id}"
    print(f"{Colors.CYAN}Connecting to {ws_url}...{Colors.RESET}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"{Colors.GREEN}✓ Connected{Colors.RESET}")
            print(f"\n{Colors.BOLD}Following logs for {agent_id} (Ctrl+C to stop)...{Colors.RESET}\n")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if data.get('type') == 'log_entry':
                        log = data.get('data', {})
                        timestamp = format_timestamp(log.get('timestamp', 0))
                        level = log.get('level', 'INFO')
                        msg = log.get('message', '')
                        
                        level_colors = {
                            'DEBUG': Colors.GRAY,
                            'INFO': Colors.BLUE,
                            'WARNING': Colors.YELLOW,
                            'ERROR': Colors.RED,
                        }
                        level_color = level_colors.get(level, Colors.WHITE)
                        
                        print(f"{Colors.GRAY}{timestamp}{Colors.RESET} {level_color}[{level}]{Colors.RESET} {msg}")
                
                except json.JSONDecodeError:
                    pass
                except KeyboardInterrupt:
                    break
    
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Agent-Forge CLI Monitor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  monitor-cli.py list                    # List all agents
  monitor-cli.py watch                   # Watch all agents in real-time
  monitor-cli.py info polling-service    # Show details for specific agent
  monitor-cli.py logs qwen-main-agent    # Show recent logs
  monitor-cli.py logs polling-service -f # Follow logs in real-time
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # List command
    subparsers.add_parser('list', help='List all connected agents')
    
    # Watch command
    subparsers.add_parser('watch', help='Watch agents in real-time (WebSocket)')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show detailed agent info')
    info_parser.add_argument('agent_id', help='Agent ID')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show agent logs')
    logs_parser.add_argument('agent_id', help='Agent ID')
    logs_parser.add_argument('-f', '--follow', action='store_true', help='Follow logs in real-time')
    logs_parser.add_argument('-n', '--lines', type=int, default=50, help='Number of lines to show')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'list':
            list_agents()
        
        elif args.command == 'watch':
            asyncio.run(watch_agents())
        
        elif args.command == 'info':
            show_agent_info(args.agent_id)
        
        elif args.command == 'logs':
            if args.follow:
                asyncio.run(follow_logs(args.agent_id))
            else:
                show_logs(args.agent_id, limit=args.lines)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted{Colors.RESET}")
        sys.exit(0)


if __name__ == '__main__':
    main()
