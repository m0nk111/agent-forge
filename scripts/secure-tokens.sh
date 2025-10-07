#!/bin/bash
# Token Security Emergency Fix
# Run immediately to secure exposed token

set -e

echo "🚨 Token Security Emergency Fix"
echo "================================"
echo ""

# Step 1: Check if token is still in agents.yaml
echo "1️⃣ Checking for exposed tokens..."
if grep -q "ghp_" config/agents.yaml; then
    echo "   ⚠️  WARNING: GitHub token found in config/agents.yaml"
    echo "   This token MUST be revoked immediately!"
    echo ""
    echo "   Action required:"
    echo "   1. Go to: https://github.com/settings/tokens"
    echo "   2. Find token: ghp_EXAMPLE_TOKEN_REPLACE_WITH_YOUR_OWN"
    echo "   3. Click: Delete / Revoke"
    echo ""
    read -p "   Press Enter after revoking the token..."
else
    echo "   ✅ No plaintext tokens found"
fi

# Step 2: Create secrets directory
echo ""
echo "2️⃣ Creating secrets infrastructure..."
mkdir -p secrets/agents secrets/keys
chmod 700 secrets
echo "   ✅ Created: secrets/agents/"
echo "   ✅ Created: secrets/keys/"
echo "   ✅ Permissions: 700 (owner only)"

# Step 3: Update .gitignore
echo ""
echo "3️⃣ Updating .gitignore..."
if ! grep -q "^secrets/" .gitignore; then
    cat >> .gitignore << 'EOF'

# Token Security (docs/TOKEN_SECURITY.md)
secrets/
!secrets/.gitkeep
master.key
*.token
*.enc
EOF
    echo "   ✅ Added secrets/ to .gitignore"
else
    echo "   ✅ .gitignore already configured"
fi

# Step 4: Create .gitkeep
touch secrets/.gitkeep
echo "   ✅ Created: secrets/.gitkeep"

# Step 5: Prompt for new token
echo ""
echo "4️⃣ Configure new GitHub token..."
echo ""
echo "   Generate new token at: https://github.com/settings/tokens/new"
echo "   Required scopes: repo, workflow, admin:org (if applicable)"
echo ""
read -p "   Enter NEW GitHub token for m0nk111-qwen-agent: " NEW_TOKEN

if [ -z "$NEW_TOKEN" ]; then
    echo "   ⚠️  No token entered, skipping..."
else
    echo "$NEW_TOKEN" > secrets/agents/m0nk111-qwen-agent.token
    chmod 600 secrets/agents/m0nk111-qwen-agent.token
    echo "   ✅ Saved: secrets/agents/m0nk111-qwen-agent.token (permissions: 600)"
fi

# Step 6: Update agents.yaml
echo ""
echo "5️⃣ Removing tokens from agents.yaml..."
sed -i.bak 's/github_token: ghp_.*/github_token: null  # Moved to secrets\/agents\//g' config/agents.yaml
echo "   ✅ Updated: config/agents.yaml"
echo "   ✅ Backup: config/agents.yaml.bak"

# Step 7: Verify
echo ""
echo "6️⃣ Verification..."
if grep -q "ghp_" config/agents.yaml; then
    echo "   ❌ ERROR: Token still in agents.yaml!"
    exit 1
else
    echo "   ✅ No plaintext tokens in agents.yaml"
fi

if [ -f "secrets/agents/m0nk111-qwen-agent.token" ]; then
    PERMS=$(stat -c "%a" secrets/agents/m0nk111-qwen-agent.token)
    if [ "$PERMS" = "600" ]; then
        echo "   ✅ Token file has correct permissions (600)"
    else
        echo "   ⚠️  WARNING: Token file has permissions $PERMS (should be 600)"
    fi
fi

# Step 8: Git status
echo ""
echo "7️⃣ Git status..."
git status --short
echo ""

# Step 9: Instructions
echo "✅ Security fix completed!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Commit changes:"
echo "   git add .gitignore config/agents.yaml"
echo "   git commit -m 'security(tokens): move tokens to secrets directory'"
echo "   git push"
echo ""
echo "2. Verify secrets are ignored:"
echo "   git status  # Should NOT show secrets/"
echo ""
echo "3. Test token:"
echo "   curl -H \"Authorization: token \$(cat secrets/agents/m0nk111-qwen-agent.token)\" https://api.github.com/user"
echo ""
echo "4. Update ConfigManager to load tokens from secrets/ (see docs/TOKEN_SECURITY.md)"
echo ""
echo "🔐 Your tokens are now secure!"
