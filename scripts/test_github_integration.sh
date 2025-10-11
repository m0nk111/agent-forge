#!/bin/bash
# Test of GitHub integratie werkt in de praktijk

echo "=========================================="
echo "🔍 GitHub Integration Status Check"
echo "=========================================="
echo ""

# 1. Check GitHub Token
echo "1️⃣  Checking GitHub Token..."
if [ -n "$GITHUB_TOKEN" ]; then
    echo "   ✅ GITHUB_TOKEN is set"
    TOKEN_LENGTH=${#GITHUB_TOKEN}
    echo "   📏 Length: $TOKEN_LENGTH characters"
else
    echo "   ❌ GITHUB_TOKEN not set"
    echo "   💡 Set with: export GITHUB_TOKEN='ghp_...'"
fi
echo ""

# 2. Check GitHub CLI
echo "2️⃣  Checking GitHub CLI (gh)..."
if command -v gh &> /dev/null; then
    echo "   ✅ gh CLI installed"
    gh --version | head -1
    
    # Check gh auth status
    if gh auth status &> /dev/null; then
        echo "   ✅ gh CLI authenticated"
        gh auth status 2>&1 | grep "Logged in" | head -1
    else
        echo "   ⚠️  gh CLI not authenticated"
        echo "   💡 Run: gh auth login"
    fi
else
    echo "   ⚠️  gh CLI not installed"
    echo "   💡 Install: https://cli.github.com/"
fi
echo ""

# 3. Check Python dependencies
echo "3️⃣  Checking Python Dependencies..."
python3 -c "
import sys
try:
    import requests
    print('   ✅ requests installed')
except ImportError:
    print('   ❌ requests not installed')
    sys.exit(1)

try:
    import yaml
    print('   ✅ yaml installed')
except ImportError:
    print('   ❌ yaml not installed')
    sys.exit(1)

try:
    from engine.operations.issue_handler import IssueHandler
    print('   ✅ IssueHandler importable')
except ImportError as e:
    print(f'   ❌ IssueHandler import failed: {e}')
    sys.exit(1)

try:
    from engine.operations.code_generator import CodeGenerator
    print('   ✅ CodeGenerator importable')
except ImportError as e:
    print(f'   ❌ CodeGenerator import failed: {e}')
    sys.exit(1)
"
echo ""

# 4. Check Ollama (for LLM)
echo "4️⃣  Checking Ollama (LLM)..."
if command -v ollama &> /dev/null; then
    echo "   ✅ ollama installed"
    
    if pgrep -x "ollama" > /dev/null; then
        echo "   ✅ ollama service running"
        
        # Check if model is available
        if ollama list | grep -q "qwen2.5-coder"; then
            echo "   ✅ qwen2.5-coder model available"
        else
            echo "   ⚠️  qwen2.5-coder model not found"
            echo "   💡 Pull with: ollama pull qwen2.5-coder:7b"
        fi
    else
        echo "   ⚠️  ollama service not running"
        echo "   💡 Start with: ollama serve"
    fi
else
    echo "   ⚠️  ollama not installed"
    echo "   💡 Install: https://ollama.ai/"
fi
echo ""

# 5. Check repo access
echo "5️⃣  Checking GitHub Repository Access..."
if [ -n "$GITHUB_TOKEN" ]; then
    RESPONSE=$(curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
        https://api.github.com/repos/m0nk111/agent-forge)
    
    if echo "$RESPONSE" | grep -q '"full_name"'; then
        echo "   ✅ Can access m0nk111/agent-forge"
        PRIVATE=$(echo "$RESPONSE" | grep '"private"' | grep -o 'true\|false')
        echo "   📁 Repo visibility: $([ "$PRIVATE" = "true" ] && echo "Private" || echo "Public")"
    else
        echo "   ❌ Cannot access repository"
        echo "   Response: $(echo "$RESPONSE" | head -c 100)..."
    fi
else
    echo "   ⏭️  Skipped (no token)"
fi
echo ""

# 6. Summary
echo "=========================================="
echo "📊 SUMMARY"
echo "=========================================="
echo ""

READY=true

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Missing: GitHub Token"
    READY=false
fi

if ! command -v ollama &> /dev/null || ! pgrep -x "ollama" > /dev/null; then
    echo "⚠️  Warning: Ollama not running (needed for code generation)"
    READY=false
fi

if [ "$READY" = true ]; then
    echo "✅ System is READY for GitHub automation!"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Create a test issue: gh issue create"
    echo "   2. Run polling service: python3 -m engine.runners.polling_service"
    echo "   3. Watch it automatically create PR!"
else
    echo "⚠️  System needs configuration before use"
    echo ""
    echo "📝 TODO:"
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "   • Set GITHUB_TOKEN environment variable"
    fi
    if ! command -v ollama &> /dev/null; then
        echo "   • Install Ollama for LLM support"
    elif ! pgrep -x "ollama" > /dev/null; then
        echo "   • Start Ollama service"
    fi
fi
echo ""
echo "=========================================="

