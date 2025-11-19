import os
import yaml
import pytest
from entityAgent.config import load_config, Config

@pytest.fixture
def clean_env():
    # Save original env
    original_env = os.environ.copy()
    # Clear relevant env vars
    if "ENTITY_LLM_MODEL" in os.environ:
        del os.environ["ENTITY_LLM_MODEL"]
    if "ENTITY_OLLAMA_URL" in os.environ:
        del os.environ["ENTITY_OLLAMA_URL"]
    yield
    # Restore env
    os.environ.clear()
    os.environ.update(original_env)

def test_default_config(clean_env):
    config = load_config()
    assert config.model == "llama3"
    assert config.server_url is None

def test_env_var_override(clean_env):
    os.environ["ENTITY_LLM_MODEL"] = "mistral"
    os.environ["ENTITY_OLLAMA_URL"] = "http://test-url:11434"
    
    config = load_config()
    assert config.model == "mistral"
    assert config.server_url == "http://test-url:11434"

def test_yaml_config(clean_env, tmp_path):
    # Create a temporary config.yaml
    config_data = {
        "model": "gemma",
        "server_url": "http://yaml-url:11434"
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
    
    # Mock Path.exists and open to read from tmp_path
    # Since we can't easily mock Path in the imported module without patching,
    # we'll temporarily change directory to tmp_path where we write config.yaml
    
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        config = load_config()
        assert config.model == "gemma"
        assert config.server_url == "http://yaml-url:11434"
    finally:
        os.chdir(original_cwd)

def test_env_priority_over_yaml(clean_env, tmp_path):
    # YAML config
    config_data = {"model": "yaml-model"}
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
        
    # Env var
    os.environ["ENTITY_LLM_MODEL"] = "env-model"
    
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        config = load_config()
        assert config.model == "env-model"
    finally:
        os.chdir(original_cwd)
