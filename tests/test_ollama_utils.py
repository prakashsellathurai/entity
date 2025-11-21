import sys
import subprocess
import pytest
from unittest.mock import MagicMock, patch, call
from entityAgent.ollama_utils import (
    _run,
    ensure_python_package,
    OllamaCLI,
    OllamaSetupError,
    setup_ollama_cli,
    ensure_ollama_ready,
)

# -----------------------------------------------------------------------------
# Test _run
# -----------------------------------------------------------------------------

def test_run_success():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        result = _run(["echo", "hello"])
        assert result.returncode == 0
        assert result.stdout == "ok"
        mock_run.assert_called_once_with(["echo", "hello"], capture_output=True, text=True)

def test_run_failure_check_true():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        with pytest.raises(OllamaSetupError) as exc:
            _run(["ls", "missing"], check=True)
        assert "Command 'ls missing' failed" in str(exc.value)

def test_run_failure_check_false():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        result = _run(["ls", "missing"], check=False)
        assert result.returncode == 1

# -----------------------------------------------------------------------------
# Test ensure_python_package
# -----------------------------------------------------------------------------

def test_ensure_python_package_installed():
    with patch("builtins.__import__") as mock_import:
        ensure_python_package("existing_pkg")
        mock_import.assert_called_once_with("existing_pkg")

def test_ensure_python_package_missing():
    import builtins
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "missing_pkg":
            raise ImportError
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        with patch("entityAgent.ollama_utils._run") as mock_run:
            ensure_python_package("missing_pkg")
            mock_run.assert_called_once_with(
                [sys.executable, "-m", "pip", "install", "missing_pkg"]
            )

# -----------------------------------------------------------------------------
# Test OllamaCLI
# -----------------------------------------------------------------------------

@pytest.fixture
def ollama_cli():
    return OllamaCLI(model="test-model")

def test_locate_or_install_cli_found_in_path(ollama_cli):
    with patch("shutil.which", return_value="/usr/bin/ollama"):
        ollama_cli._locate_or_install_cli()
        assert ollama_cli.executable == "/usr/bin/ollama"

def test_locate_or_install_cli_auto_install_linux(ollama_cli):
    # Force system to linux
    with patch.object(ollama_cli, "_system", "linux"):
        with patch("shutil.which", side_effect=[None, "/usr/local/bin/ollama"]): # First check fails, second (after install) succeeds
            with patch.object(ollama_cli, "_install_linux_tar", return_value="/usr/local/bin/ollama") as mock_install:
                ollama_cli._locate_or_install_cli()
                assert ollama_cli.executable == "/usr/local/bin/ollama"
                mock_install.assert_called_once()

def test_verify_cli(ollama_cli):
    ollama_cli.executable = "/bin/ollama"
    with patch("entityAgent.ollama_utils._run") as mock_run:
        ollama_cli._verify_cli()
        mock_run.assert_called_once_with(["/bin/ollama", "--version"])

def test_ensure_model_already_present(ollama_cli):
    ollama_cli.executable = "/bin/ollama"
    with patch("entityAgent.ollama_utils._run") as mock_run:
        mock_run.return_value.stdout = "model1\ntest-model\nmodel2"
        ollama_cli._ensure_model()
        # Should list but not pull
        mock_run.assert_called_once_with(["/bin/ollama", "list"], check=False)

def test_ensure_model_missing(ollama_cli):
    ollama_cli.executable = "/bin/ollama"
    with patch("entityAgent.ollama_utils._run") as mock_run:
        mock_run.return_value.stdout = "model1\nmodel2"
        ollama_cli._ensure_model()
        # Should list AND pull
        assert mock_run.call_count == 2
        mock_run.assert_has_calls([
            call(["/bin/ollama", "list"], check=False),
            call(["/bin/ollama", "pull", "test-model"])
        ])

def test_ensure_server_running_already_up(ollama_cli):
    with patch.dict(sys.modules, {"ollama": MagicMock()}):
        import ollama
        ollama_cli._ensure_server_running()
        ollama.list.assert_called_once()

def test_ensure_server_running_start_server(ollama_cli):
    ollama_cli.executable = "/bin/ollama"
    mock_ollama = MagicMock()
    # First call raises exception, second succeeds
    mock_ollama.list.side_effect = [Exception("down"), ["model"]]
    
    with patch.dict(sys.modules, {"ollama": mock_ollama}):
        with patch("subprocess.Popen") as mock_popen:
            with patch("time.sleep"): # skip sleep
                ollama_cli._ensure_server_running()
                
                mock_popen.assert_called_once_with(["/bin/ollama", "run", "test-model"])
                assert mock_ollama.list.call_count == 2

# -----------------------------------------------------------------------------
# Test Wrappers
# -----------------------------------------------------------------------------

def test_setup_ollama_cli():
    with patch("entityAgent.ollama_utils.OllamaCLI") as MockCLI:
        setup_ollama_cli("my-model")
        MockCLI.assert_called_with("my-model")
        MockCLI.return_value._locate_or_install_cli.assert_called_once()

def test_ensure_ollama_ready():
    with patch("entityAgent.ollama_utils.ensure_python_package") as mock_pkg:
        with patch("entityAgent.ollama_utils.OllamaCLI") as MockCLI:
            ensure_ollama_ready("my-model")
            mock_pkg.assert_called_once_with("ollama")
            MockCLI.assert_called_with("my-model")
            MockCLI.return_value.ensure_ready.assert_called_once()
