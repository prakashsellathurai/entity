import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import unittest
import platform
from entityAgent.platform_interaction import get_operating_system, execute_command, list_processes

class TestPlatformInteraction(unittest.TestCase):

    def test_get_operating_system(self):
        """
        Tests that the get_operating_system function returns the correct OS.
        """
        os_name = get_operating_system()
        self.assertEqual(os_name, platform.system() if platform.system() != 'Darwin' else 'macOS')

    def test_execute_command(self):
        """
        Tests the execute_command function with a simple command.
        """
        # A simple command that works on all platforms
        command = "echo hello"
        stdout, stderr, return_code = execute_command(command)
        self.assertEqual(return_code, 0)
        self.assertEqual(stdout, "hello")
        self.assertEqual(stderr, "")

    def test_list_processes(self):
        """
        Tests that the list_processes function returns a list of processes.
        """
        processes = list_processes()
        self.assertIsInstance(processes, list)
        # Check if the list is not empty and contains process information
        if processes:
            self.assertIn('pid', processes[0])
            self.assertIn('name', processes[0])

if __name__ == '__main__':
    unittest.main()
