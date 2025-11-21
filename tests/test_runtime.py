import os
import sys
import pytest
from unittest.mock import MagicMock, patch, call
from entityAgent.runtime import main, runtime

# -----------------------------------------------------------------------------
# Test main()
# -----------------------------------------------------------------------------

def test_main_install_ollama():
    with patch("argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = MagicMock(install_ollama=True, llm_model=None, web=False)
        with patch("entityAgent.runtime.setup_ollama_cli") as mock_setup:
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0
            mock_setup.assert_called_once()

def test_main_web_interface():
    with patch("argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = MagicMock(install_ollama=False, llm_model=None, web=True)
        with patch("entityAgent.config.load_config") as mock_config:
            mock_config.return_value = MagicMock(server_url=None, model="default-model")
            with patch("uvicorn.run") as mock_uvicorn:
                main()
                mock_uvicorn.assert_called_once()

def test_main_runtime_execution():
    with patch("argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = MagicMock(install_ollama=False, llm_model="custom-model", web=False)
        with patch("entityAgent.config.load_config") as mock_config:
            mock_config.return_value = MagicMock(server_url="http://custom-host", model="default-model")
            with patch("entityAgent.runtime.runtime") as mock_runtime:
                main()
                mock_runtime.assert_called_once()
                assert os.environ["OLLAMA_HOST"] == "http://custom-host"
                assert os.environ["ENTITY_LLM_MODEL"] == "custom-model"

# -----------------------------------------------------------------------------
# Test runtime()
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_ollama_ready():
    with patch("entityAgent.runtime.ensure_ollama_ready") as mock:
        yield mock

@pytest.fixture
def mock_ollama_module():
    with patch.dict(sys.modules, {"ollama": MagicMock()}):
        yield sys.modules["ollama"]

def test_runtime_exit(mock_ollama_ready, mock_ollama_module):
    with patch("builtins.input", side_effect=["exit"]):
        with patch("entityAgent.config.load_config") as mock_config:
            mock_config.return_value.model = "test-model"
            runtime()

def test_runtime_list_processes(mock_ollama_ready, mock_ollama_module):
    with patch("builtins.input", side_effect=["run: list_processes", "exit"]):
        with patch("entityAgent.config.load_config") as mock_config:
            mock_config.return_value.model = "test-model"
            with patch("entityAgent.runtime.list_processes") as mock_list:
                mock_list.return_value = [{"pid": 123, "name": "test_proc", "username": "user"}]
                runtime()
                mock_list.assert_called_once()

def test_runtime_execute_command_success(mock_ollama_ready, mock_ollama_module):
    with patch("builtins.input", side_effect=["run: echo hello", "exit"]):
        with patch("entityAgent.config.load_config") as mock_config:
            mock_config.return_value.model = "test-model"
            with patch("entityAgent.runtime.execute_command") as mock_exec:
                mock_exec.return_value = ("hello\n", "", 0)
                runtime()
                mock_exec.assert_called_with("echo hello")

def test_runtime_execute_command_failure(mock_ollama_ready, mock_ollama_module):
    with patch("builtins.input", side_effect=["run: fail", "exit"]):
        with patch("entityAgent.config.load_config") as mock_config:
            mock_config.return_value.model = "test-model"
            with patch("entityAgent.runtime.execute_command") as mock_exec:
                mock_exec.return_value = ("", "error\n", 1)
                runtime()
                mock_exec.assert_called_with("fail")

def test_runtime_chat_interaction(mock_ollama_ready, mock_ollama_module):
    with patch("builtins.input", side_effect=["hello", "exit"]):
        with patch("entityAgent.config.load_config") as mock_config:
            mock_config.return_value.model = "test-model"
            
            mock_ollama_module.chat.return_value = {'message': {'content': 'Hi there!'}}
            
            runtime()
            
            mock_ollama_module.chat.assert_called_once()
            call_args = mock_ollama_module.chat.call_args
            assert call_args.kwargs['model'] == "test-model"
            # messages is mutable and has the assistant response appended after the call
            # so we check the second to last message for the user input
            assert call_args.kwargs['messages'][-2]['content'] == "hello"
