#!/usr/bin/env python3
"""
Migrate secrets from legacy keys.json to organized structure.

This script migrates:
- GitHub tokens → secrets/agents/*.token
- API keys → secrets/keys/*.key
"""

import json
import sys
from pathlib import Path


def main():
    """Migrate secrets from keys.json to organized structure."""
    project_root = Path(__file__).parent.parent
    keys_json_path = project_root / 'secrets' / 'keys.json'
    
    if not keys_json_path.exists():
        print("✅ No keys.json found - nothing to migrate")
        return 0
    
    print("🔄 Migrating secrets from keys.json...\n")
    
    # Load keys.json
    with open(keys_json_path) as f:
        keys = json.load(f)
    
    # Migration mapping
    migrations = {
        # GitHub tokens → agents/
        'GITHUB_TOKEN': 'agents/m0nk111.token',
        'BOT_GITHUB_TOKEN': 'agents/m0nk111-post.token',
        'QWEN_GITHUB_TOKEN': 'agents/m0nk111-qwen-agent.token',
        'CODER1_GITHUB_TOKEN': 'agents/m0nk111-coder1.token',
        'CODER2_GITHUB_TOKEN': 'agents/m0nk111-coder2.token',
        'REVIEWER_GITHUB_TOKEN': 'agents/m0nk111-reviewer.token',
        
        # API keys → keys/
        'OPENAI_API_KEY': 'keys/openai.key',
        'ANTHROPIC_API_KEY': 'keys/anthropic.key',
        'OLLAMA_API_KEY': 'keys/ollama.key',
    }
    
    migrated = []
    skipped = []
    
    for old_key, new_path in migrations.items():
        if old_key not in keys or not keys[old_key]:
            continue
        
        value = keys[old_key]
        target_path = project_root / 'secrets' / new_path
        
        # Check if file already exists
        if target_path.exists():
            existing = target_path.read_text().strip()
            if existing == value:
                print(f"⏭️  {old_key} → {new_path} (already up-to-date)")
                skipped.append(old_key)
                continue
            else:
                print(f"⚠️  {old_key} → {new_path} (file exists with different value)")
                print(f"   Existing: {existing[:10]}...")
                print(f"   keys.json: {value[:10]}...")
                
                response = input("   Overwrite? [y/N]: ").lower()
                if response != 'y':
                    print("   Skipped")
                    skipped.append(old_key)
                    continue
        
        # Create parent directory if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write new file
        target_path.write_text(value)
        target_path.chmod(0o600)  # Owner read/write only
        
        print(f"✅ {old_key} → {new_path}")
        migrated.append((old_key, new_path))
    
    # Summary
    print("\n" + "="*60)
    print("Migration Summary:")
    print(f"  Migrated: {len(migrated)}")
    print(f"  Skipped: {len(skipped)}")
    
    if migrated:
        print("\nMigrated secrets:")
        for old_key, new_path in migrated:
            print(f"  ✅ {old_key} → {new_path}")
    
    # Deprecate keys.json
    if migrated:
        deprecated_path = keys_json_path.with_suffix('.json.deprecated')
        keys_json_path.rename(deprecated_path)
        print(f"\n🗄️  Renamed keys.json → {deprecated_path.name}")
        print("   (You can safely delete this file after verifying migration)")
    
    print("\n✅ Migration complete!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
