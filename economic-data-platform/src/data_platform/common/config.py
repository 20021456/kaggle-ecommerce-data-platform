"""Configuration loader"""

import os
import yaml
from pathlib import Path

def load_config(env: str | None = None) -> dict:
    """Load configuration from YAML file based on environment"""
    env_value: str = env if env is not None else os.getenv("ENV", "dev")
    config_path = Path(__file__).parents[3] / "config" / f"{env_value}.yml"
    
    if not config_path.exists():
        return {}
    
    with open(config_path) as f:
        return yaml.safe_load(f)
