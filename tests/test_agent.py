import unittest
from entityAgent.agent import runtime
from unittest.mock import patch

class TestAgent(unittest.TestCase):
    @patch('entityAgent.agent.ollama')
    @patch('entityAgent.platform_interaction.get_operating_system', return_value='Linux')
    def test_agent_ollama_not_running(self, mock_os, mock_ollama):
        mock_ollama.list.side_effect = Exception('Ollama not running')
        with patch('builtins.print') as mock_print, self.assertRaises(SystemExit):
            runtime()
        mock_print.assert_any_call('Error: Ollama is not running. Please start the Ollama service and try again.')

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
