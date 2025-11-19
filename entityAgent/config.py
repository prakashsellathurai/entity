import os
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Config:
    model: str = "llama3"
    server_url: Optional[str] = None

def load_config() -> Config:
    """
    Load configuration from config.yaml or environment variables.
    Priority:
    1. Environment Variables (ENTITY_LLM_MODEL, ENTITY_OLLAMA_URL)
    2. config.yaml in current directory
    3. config.yaml in ~/.entity/config.yaml
    4. Defaults
    """
    config = Config()

    # Load from config files
    config_paths = [
        Path.home() / ".entity" / "config.yaml",
        Path("config.yaml")
    ]

    for path in config_paths:
        if path.exists():
            try:
                with open(path, "r") as f:
                    data = yaml.safe_load(f)
                    if data:
                        if "model" in data:
                            config.model = data["model"]
                        if "server_url" in data:
                            config.server_url = data["server_url"]
            except Exception as e:
                print(f"[WARN] Failed to load config from {path}: {e}")

    # Override with environment variables
    env_model = os.environ.get("ENTITY_LLM_MODEL")
    if env_model:
        config.model = env_model

    env_url = os.environ.get("ENTITY_OLLAMA_URL")
    if env_url:
        config.server_url = env_url

    return config
