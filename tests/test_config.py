from __future__ import annotations

from pathlib import Path

from src.core.config_loader import load_config


def test_load_config_expands_environment(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ANALYSIS_API_KEY", "sk-analysis")
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
analysis_model:
  api_key: "${ANALYSIS_API_KEY}"
search_engines:
  - name: "serper"
    enabled: true
    priority: 1
    config:
      api_key: "${SERPER_API_KEY:-fallback-key}"
cache:
  backend: "memory"
""",
        encoding="utf-8",
    )
    config = load_config(config_file)
    assert config.analysis_model.api_key == "sk-analysis"
    assert config.search_engines[0].config["api_key"] == "fallback-key"
