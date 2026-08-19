"""YAML configuration loader with optional environment overrides."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from data_generation.config import GeneratorConfig


def load_config(path: str | Path) -> GeneratorConfig:
    """Load and validate generator configuration from a YAML file."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if raw is None:
        raise ValueError(f"Configuration file is empty: {config_path}")

    config = GeneratorConfig.model_validate(raw)
    return _apply_env_overrides(config)


def _apply_env_overrides(config: GeneratorConfig) -> GeneratorConfig:
    """Apply optional environment variable overrides."""
    updates: dict = {}

    if seed := os.environ.get("RANDOM_SEED"):
        updates.setdefault("reproducibility", {})["random_seed"] = int(seed)

    if output_dir := os.environ.get("OUTPUT_DIR"):
        updates.setdefault("output", {})["directory"] = output_dir

    if not updates:
        return config

    data = config.model_dump(mode="json")
    for section, values in updates.items():
        data[section].update(values)
    return GeneratorConfig.model_validate(data)


def default_config_path() -> Path:
    """Return the default configuration file path relative to project root."""
    candidates = [
        Path("config/generator_config.yaml"),
        Path("generator_config.yaml"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]
