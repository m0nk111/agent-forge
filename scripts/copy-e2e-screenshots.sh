#!/bin/bash
# Copy E2E Test Screenshots from Playwright Temp to Media Directory
# Date: 2025-10-12

MEDIA_DIR="/home/flip/agent-forge/media"
PLAYWRIGHT_TEMP_PATTERN="/tmp/playwright-mcp-output/*/media/e2e-test-*.png"
WINDOWS_PATH="C:\\Users\\onyou\\AppData\\Local\\Temp\\playwright-mcp-output\\1760265229972\\media\\"

echo "🔍 Searching for E2E test screenshots..."
echo ""

# Check Linux temp directory
if ls ${PLAYWRIGHT_TEMP_PATTERN} 2>/dev/null; then
    echo "✅ Found screenshots in Linux temp directory"
    cp -v ${PLAYWRIGHT_TEMP_PATTERN} "${MEDIA_DIR}/"
    echo "✅ Screenshots copied to ${MEDIA_DIR}/"
else
    echo "❌ No screenshots found in Linux temp: /tmp/playwright-mcp-output/"
    echo ""
    echo "📌 Manual Copy Instructions:"
    echo ""
    echo "If running on Windows machine, copy from:"
    echo "  ${WINDOWS_PATH}"
    echo ""
    echo "To server location:"
    echo "  ${MEDIA_DIR}/"
    echo ""
    echo "Files to copy:"
    echo "  - e2e-test-dashboard-agents.png"
    echo "  - e2e-test-github-issue3-claim.png"
    echo ""
    echo "Using SCP command:"
    echo "  scp \"${WINDOWS_PATH}e2e-test-*.png\" flip@192.168.1.30:${MEDIA_DIR}/"
fi

echo ""
echo "📂 Current media directory contents:"
ls -lh "${MEDIA_DIR}/"
