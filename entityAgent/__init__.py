from .ollama_utils import ensure_ollama_ready, setup_ollama_cli, uninstall_ollama_cli, OllamaSetupError
from .platform_interaction import get_operating_system, execute_command, list_processes
from .runtime import main

__all__ = [
    "ensure_ollama_ready",
    "setup_ollama_cli",
    "uninstall_ollama_cli",
    "OllamaSetupError",
    "get_operating_system",
    "execute_command",
    "list_processes",
    "main",
]
