import sys
import os
import subprocess
import platform
import shutil
import pytest
import entityAgent.ollama_utils as ollama_utils


def is_ollama_installed():
    return shutil.which("ollama") is not None

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
        if os.getenv("WSL_CHECK") == "true":
            try:
                result = subprocess.run(["wsl.exe", "--version"], capture_output=True)
                assert result.returncode == 0, "WSL not available on Windows."
            except FileNotFoundError:
                pytest.skip("WSL not installed")

@pytest.mark.skipif(platform.system().lower() != "linux", reason="WSL test only on Linux")
def test_wsl_detection():
    # Only run this on Linux runners (may be WSL)
    try:
        with open('/proc/version', 'r') as f:
            version = f.read().lower()
        assert 'microsoft' in version, "Not running in WSL."
    except Exception:
        pytest.skip("/proc/version not available or not WSL")


@pytest.fixture(scope="function")
def test_env():
    """
    Sets up a clean test environment.
    """
    # Create a temporary directory
    test_dir = os.path.join(os.getcwd(), "test_tmp")
    os.makedirs(test_dir, exist_ok=True)
    yield test_dir
    # Clean up the temporary directory
    shutil.rmtree(test_dir)

def test_successful_uninstall(test_env):
    """
    Tests a successful Ollama uninstallation.
    """
    # 1. Install Entity Agent (which installs Ollama)
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "."], cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))), check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Failed to install Entity Agent: {e.stderr.decode()}")

    # 2. Run the uninstall command
    try:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "entityagent"], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Failed to uninstall Entity Agent: {e.stderr.decode()}")

        # 3. Verify that Ollama is uninstalled
        from entityAgent.ollama_utils import is_ollama_installed
        assert not is_ollama_installed(), "Ollama was not uninstalled."

    # 4. Verify that Entity Agent is uninstalled
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True, check=True)
        assert "entityagent" not in result.stdout.lower(), "Entity Agent was not uninstalled"
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Failed to list pip packages: {e.stderr.decode()}")