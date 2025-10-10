"""Tests for YAML-first configuration loading in PollingService."""

import json
from pathlib import Path

from engine.runners.polling_service import PollingService, PollingConfig


def test_load_from_yaml_then_override(tmp_path):
    # Arrange: schrijf tijdelijke YAML
    cfg_dir = tmp_path / "config/services"
    cfg_dir.mkdir(parents=True)
    yaml_path = cfg_dir / "polling.yaml"
    yaml_path.write_text(
        """
interval_seconds: 42
github:
  username: "yaml-bot"
repositories:
  - "owner/repoA"
  - "owner/repoB"
watch_labels:
  - "agent-ready"
  - "yaml-only"
max_concurrent_issues: 7
claim_timeout_minutes: 15
state_file: "yaml_state.json"
""",
        encoding="utf-8",
    )

    # Act: laad via expliciete config_path
    service_yaml = PollingService(config=None, config_path=yaml_path)

    # Assert: waarden uit YAML
    assert service_yaml.config.interval_seconds == 42
    assert service_yaml.config.github_username == "yaml-bot"
    assert service_yaml.config.repositories == ["owner/repoA", "owner/repoB"]
    assert service_yaml.config.watch_labels == ["agent-ready", "yaml-only"]
    assert service_yaml.config.max_concurrent_issues == 7
    assert service_yaml.config.claim_timeout_minutes == 15
    assert service_yaml.config.state_file == "yaml_state.json"

    # Act: override met PollingConfig (bijv. interval en labels)
    override = PollingConfig(interval_seconds=5, watch_labels=["agent-ready"]) 
    service_override = PollingService(config=override, config_path=yaml_path)

    # Assert: overrides werken, overige YAML blijft intact
    assert service_override.config.interval_seconds == 5  # override
    assert service_override.config.watch_labels == ["agent-ready"]  # override
    assert service_override.config.github_username == "yaml-bot"  # uit YAML
    assert service_override.config.repositories == ["owner/repoA", "owner/repoB"]