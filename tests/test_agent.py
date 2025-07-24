import unittest
import sys
from unittest.mock import patch, MagicMock

# Mock ollama before importing runtime
sys.modules['ollama'] = MagicMock()
from entityAgent.agent import runtime

class TestAgent(unittest.TestCase):
    @patch('entityAgent.agent.ollama')
    @patch('entityAgent.platform_interaction.get_operating_system', return_value='Linux')
    @patch('entityAgent.agent.subprocess.Popen')
    @patch('entityAgent.agent.time.sleep')
    @patch('entityAgent.agent.subprocess.run')
    def test_agent_ollama_not_running(self, mock_run, mock_sleep, mock_popen, mock_os, mock_ollama):
        # Simulate ollama.list raising an exception the first time, then succeeding
        mock_ollama.list.side_effect = [Exception('Ollama not running'), None]
        # Mock subprocess.run for ollama CLI checks
        def run_side_effect(args, **kwargs):
            class Result:
                def __init__(self, returncode=0, stdout="", stderr=""):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr
            if args[:2] == ["ollama", "--version"]:
                return Result(returncode=0)
            if args[:2] == ["ollama", "list"]:
                return Result(returncode=0, stdout="llama3")
            if args[:2] == ["ollama", "pull"]:
                return Result(returncode=0)
            return Result(returncode=0)
        mock_run.side_effect = run_side_effect
        with patch('builtins.input', side_effect=['exit']), patch('builtins.print') as mock_print:
            runtime()
        mock_print.assert_any_call("Ollama is not running. Attempting to start Ollama with default model 'llama3'...")
        mock_print.assert_any_call("Ollama started successfully with model 'llama3'.")

    @patch('entityAgent.agent.ollama')
    @patch('entityAgent.platform_interaction.get_operating_system', return_value='Linux')
    def test_agent_exit_command(self, mock_os, mock_ollama):
        mock_ollama.list.return_value = None
        with patch('builtins.input', side_effect=['exit']), patch('builtins.print') as mock_print:
            runtime()
        mock_print.assert_any_call('Entity Agent: Initializing...')
        mock_print.assert_any_call('Ollama connection successful.')

if __name__ == '__main__':
    unittest.main()
