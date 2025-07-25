import sys
import subprocess
import platform
import shutil
import pytest


def is_ollama_installed():
    return shutil.which("ollama") is not None

def test_ollama_installed():
    assert is_ollama_installed(), "Ollama is not installed or not in PATH."

def test_platform_detection():
    os_name = platform.system().lower()
    assert os_name in ["windows", "linux", "darwin"], f"Unknown OS: {os_name}"

    # Check for WSL on Windows
    if os_name == "linux":
        try:
            with open('/proc/version', 'r') as f:
                version = f.read().lower()
            if 'microsoft' in version:
                assert 'microsoft' in version, "Not running in WSL, but expected WSL."
        except Exception:
            pass  # Not WSL
    elif os_name == "windows":
        # Optionally check for WSL presence
        try:
            result = subprocess.run(["wsl.exe", "--version"], capture_output=True)
            assert result.returncode == 0, "WSL not available on Windows."
        except FileNotFoundError:
            pass  # WSL not installed, but not required

@pytest.mark.skipif(platform.system().lower() != "linux", reason="WSL test only on Linux")
def test_wsl_detection():
    # Only run this on Linux runners (may be WSL)
    try:
        with open('/proc/version', 'r') as f:
            version = f.read().lower()
        assert 'microsoft' in version, "Not running in WSL."
    except Exception:
        pytest.skip("/proc/version not available or not WSL")
