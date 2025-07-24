import unittest
from unittest.mock import patch, MagicMock
import sys

class TestOllamaUtils(unittest.TestCase):
    @patch('builtins.print')
    @patch('subprocess.run')
    def test_ensure_ollama_cli_and_model_already_installed(self, mock_run, mock_print):
        # Simulate ollama CLI and model already present
        mock_run.side_effect = [
            type('Result', (), {'returncode': 0, 'stdout': '', 'stderr': ''})(),  # ollama --version
            type('Result', (), {'returncode': 0, 'stdout': 'llama3', 'stderr': ''})()  # ollama list
        ]
        from entityAgent.ollama_utils import ensure_ollama_cli_and_model
        self.assertTrue(ensure_ollama_cli_and_model('llama3'))
        mock_print.assert_not_called()

    @patch('builtins.print')
    @patch('subprocess.run')
    def test_ensure_ollama_cli_and_model_download_model(self, mock_run, mock_print):
        # Simulate ollama CLI present, model not present, download succeeds
        mock_run.side_effect = [
            type('Result', (), {'returncode': 0, 'stdout': '', 'stderr': ''})(),  # ollama --version
            type('Result', (), {'returncode': 0, 'stdout': '', 'stderr': ''})(),  # ollama list
            type('Result', (), {'returncode': 0, 'stdout': '', 'stderr': ''})()   # ollama pull
        ]
        from entityAgent.ollama_utils import ensure_ollama_cli_and_model
        self.assertTrue(ensure_ollama_cli_and_model('llama3'))
        mock_print.assert_any_call("Downloading model 'llama3'...")

    @patch('builtins.print')
    @patch('subprocess.run')
    def test_ensure_ollama_cli_and_model_fail_download(self, mock_run, mock_print):
        # Simulate ollama CLI present, model not present, download fails
        mock_run.side_effect = [
            type('Result', (), {'returncode': 0, 'stdout': '', 'stderr': ''})(),  # ollama --version
            type('Result', (), {'returncode': 0, 'stdout': '', 'stderr': ''})(),  # ollama list
            type('Result', (), {'returncode': 1, 'stdout': '', 'stderr': 'fail'})()   # ollama pull
        ]
        from entityAgent.ollama_utils import ensure_ollama_cli_and_model
        with self.assertRaises(SystemExit):
            ensure_ollama_cli_and_model('llama3')
        mock_print.assert_any_call("Downloading model 'llama3'...")
        mock_print.assert_any_call("Failed to download model 'llama3': fail")

    @patch('builtins.print')
    @patch('subprocess.run')
    @patch('platform.system', return_value='Linux')
    @patch('shutil.move')
    @patch('tarfile.open')
    @patch('urllib.request.urlretrieve')
    @patch('tempfile.TemporaryDirectory')
    def test_ensure_ollama_cli_and_model_install_linux(self, mock_tmpdir, mock_urlretrieve, mock_tarfile, mock_move, mock_system, mock_run, mock_print):
        # Simulate ollama CLI not present, install succeeds
        # subprocess.run is called for:
        # 1. ollama --version (not found)
        # 2. chmod +x /usr/local/bin/ollama
        # 3. ollama list
        mock_run.side_effect = [
            type('Result', (), {'returncode': 1, 'stdout': '', 'stderr': ''})(),  # ollama --version (not found)
            type('Result', (), {'returncode': 0, 'stdout': '', 'stderr': ''})(),  # chmod
            type('Result', (), {'returncode': 0, 'stdout': 'llama3', 'stderr': ''})()  # ollama list
        ]
        mock_tmpdir.return_value.__enter__.return_value = '/tmp/fake'
        from entityAgent.ollama_utils import ensure_ollama_cli_and_model
        self.assertTrue(ensure_ollama_cli_and_model('llama3'))
        mock_print.assert_any_call('Ollama CLI installed to /usr/local/bin/ollama.')

if __name__ == '__main__':
    unittest.main()
