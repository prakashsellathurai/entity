import sys
import pytest
from unittest.mock import MagicMock, patch, call
from entityAgent.ollama_utils import (
    _run,
    ensure_python_package,
    OllamaSetupError,
    setup_ollama_cli,
    ensure_ollama_ready,
    find_existing_cli,
    locate_or_install_cli,
    verify_cli,
    ensure_model,
    ensure_server_running,
    ensure_cli_ready,
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
# Test find_existing_cli
# -----------------------------------------------------------------------------

def test_find_existing_cli_found_in_path():
    with patch("shutil.which", return_value="/usr/bin/ollama"):
        result = find_existing_cli()
        assert result == "/usr/bin/ollama"

def test_find_existing_cli_not_found():
    with patch("shutil.which", return_value=None):
        result = find_existing_cli()
        assert result is None

# -----------------------------------------------------------------------------
# Test locate_or_install_cli
# -----------------------------------------------------------------------------

@patch("entityAgent.ollama_utils.find_existing_cli", return_value="/usr/bin/ollama")
def test_locate_or_install_cli_found(mock_find):
    result = locate_or_install_cli()
    assert result == "/usr/bin/ollama"

@patch("entityAgent.ollama_utils.find_existing_cli", return_value=None)
@patch("entityAgent.ollama_utils.auto_install_cli", return_value="/usr/local/bin/ollama")
def test_locate_or_install_cli_auto_install(mock_find, mock_auto):
    result = locate_or_install_cli()
    assert result == "/usr/local/bin/ollama"

@patch("entityAgent.ollama_utils.find_existing_cli", return_value=None)
@patch("entityAgent.ollama_utils.auto_install_cli", return_value=None)
def test_locate_or_install_cli_fails(mock_find, mock_auto):
    with pytest.raises(OllamaSetupError, match="Ollama CLI not found"):
        locate_or_install_cli()

# -----------------------------------------------------------------------------
# Test verify_cli
# -----------------------------------------------------------------------------

def test_verify_cli():
    with patch("entityAgent.ollama_utils._run") as mock_run:
        verify_cli("/bin/ollama")
        mock_run.assert_called_once_with(["/bin/ollama", "--version"])

# -----------------------------------------------------------------------------
# Test ensure_model
# -----------------------------------------------------------------------------

def test_ensure_model_already_present():
    with patch("entityAgent.ollama_utils._run") as mock_run:
        mock_run.return_value.stdout = "model1\ntest-model\nmodel2"
        ensure_model("/bin/ollama", "test-model")
        mock_run.assert_called_once_with(["/bin/ollama", "list"], check=False)

def test_ensure_model_missing():
    with patch("entityAgent.ollama_utils._run") as mock_run:
        mock_run.return_value.stdout = "model1\nmodel2"
        ensure_model("/bin/ollama", "test-model")
        assert mock_run.call_count == 2
        mock_run.assert_has_calls([
            call(["/bin/ollama", "list"], check=False),
            call(["/bin/ollama", "pull", "test-model"])
        ])

# -----------------------------------------------------------------------------
# Test ensure_server_running
# -----------------------------------------------------------------------------

def test_ensure_server_running_already_up():
    with patch.dict(sys.modules, {"ollama": MagicMock()}):
        import ollama
        ensure_server_running("/bin/ollama", "test-model")
        ollama.list.assert_called_once()

def test_ensure_server_running_start_server():
    mock_ollama = MagicMock()
    mock_ollama.list.side_effect = [Exception("down"), ["model"]]

    with patch.dict(sys.modules, {"ollama": mock_ollama}):
        with patch("subprocess.Popen") as mock_popen:
            with patch("time.sleep"):
                ensure_server_running("/bin/ollama", "test-model")

                mock_popen.assert_called_once_with(["/bin/ollama", "run", "test-model"])
                assert mock_ollama.list.call_count == 2

# -----------------------------------------------------------------------------
# Test ensure_cli_ready (orchestrator)
# -----------------------------------------------------------------------------

@patch("entityAgent.ollama_utils.ensure_server_running")
@patch("entityAgent.ollama_utils.ensure_model")
@patch("entityAgent.ollama_utils.verify_cli")
@patch("entityAgent.ollama_utils.locate_or_install_cli", return_value="/bin/ollama")
def test_ensure_cli_ready(mock_locate, mock_verify, mock_model, mock_server):
    ensure_cli_ready("test-model")
    mock_locate.assert_called_once()
    mock_verify.assert_called_once_with("/bin/ollama")
    mock_model.assert_called_once_with("/bin/ollama", "test-model")
    mock_server.assert_called_once_with("/bin/ollama", "test-model")

# -----------------------------------------------------------------------------
# Test Wrappers
# -----------------------------------------------------------------------------

@patch("entityAgent.ollama_utils.locate_or_install_cli", return_value="/bin/ollama")
def test_setup_ollama_cli(mock_locate):
    setup_ollama_cli("my-model")

@patch("entityAgent.ollama_utils.ensure_cli_ready")
@patch("entityAgent.ollama_utils.ensure_python_package")
def test_ensure_ollama_ready(mock_pkg, mock_cli_ready):
    ensure_ollama_ready("my-model")
    mock_pkg.assert_called_once_with("ollama")
    mock_cli_ready.assert_called_once_with("my-model")
