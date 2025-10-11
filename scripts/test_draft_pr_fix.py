#!/usr/bin/env python3
"""Test script to check and fix draft PRs manually."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_draft_pr_fix():
    """Test the draft PR fixing functionality."""
    from engine.runners.polling_service import PollingService, PollingConfig
    
    # Create minimal config
    config = PollingConfig(
        repositories=['m0nk111/agent-forge'],
        pr_monitoring_enabled=True,
        interval_seconds=60
    )
    
    # Create polling service
    service = PollingService(config=config, enable_monitoring=False)
    
    logger.info("🚀 Testing draft PR check and fix...")
    
    # Run the check
    await service.check_and_fix_draft_prs()
    
    logger.info("✅ Test complete")

if __name__ == '__main__':
    asyncio.run(test_draft_pr_fix())
