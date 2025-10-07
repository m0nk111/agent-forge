#!/bin/bash
# Quick setup script voor Google OAuth

set -e

echo "🔐 Agent-Forge Google OAuth Setup"
echo "=================================="
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "✅ .env file gevonden"
    source .env
else
    echo "⚠️  .env file niet gevonden. Kopiëren van template..."
    cp .env.template .env
    echo "📝 .env bestand aangemaakt. Vul je Google OAuth credentials in:"
    echo "   nano .env"
    echo ""
    echo "📚 Zie docs/GOOGLE_OAUTH_SETUP.md voor instructies"
    exit 1
fi

# Validate configuration
if [ -z "$GOOGLE_CLIENT_ID" ] || [ "$GOOGLE_CLIENT_ID" = "your-client-id.apps.googleusercontent.com" ]; then
    echo "❌ GOOGLE_CLIENT_ID niet geconfigureerd in .env"
    exit 1
fi

if [ -z "$GOOGLE_CLIENT_SECRET" ] || [ "$GOOGLE_CLIENT_SECRET" = "your-client-secret" ]; then
    echo "❌ GOOGLE_CLIENT_SECRET niet geconfigureerd in .env"
    exit 1
fi

if [ -z "$ALLOWED_EMAILS" ] || [ "$ALLOWED_EMAILS" = "your-email@gmail.com,another-email@gmail.com" ]; then
    echo "❌ ALLOWED_EMAILS niet geconfigureerd in .env"
    exit 1
fi

echo "✅ Configuratie validatie OK"
echo ""

# Generate session secret if needed
if [ -z "$SESSION_SECRET" ] || [ "$SESSION_SECRET" = "generate-a-random-32-character-string-here" ]; then
    echo "🔑 Genereer SESSION_SECRET..."
    NEW_SECRET=$(openssl rand -hex 32)
    sed -i "s/SESSION_SECRET=.*/SESSION_SECRET=$NEW_SECRET/" .env
    echo "✅ SESSION_SECRET gegenereerd"
fi

echo ""
echo "📋 Configuratie:"
echo "   Client ID: ${GOOGLE_CLIENT_ID:0:20}..."
echo "   Redirect URI: $GOOGLE_REDIRECT_URI"
echo "   Allowed emails: $ALLOWED_EMAILS"
echo ""

# Start auth service
echo "🚀 Start Auth API op poort 7999..."
export $(cat .env | grep -v '^#' | xargs)
/opt/agent-forge/venv/bin/python3 -m api.auth_routes
