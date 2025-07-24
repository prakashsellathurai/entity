import unittest
from entityAgent.platform_interaction import get_operating_system, execute_command, list_processes
import platform

class TestPlatformInteraction(unittest.TestCase):
    def test_get_operating_system(self):
        os_name = get_operating_system()
        self.assertEqual(os_name, platform.system() if platform.system() != 'Darwin' else 'macOS')

    def test_execute_command(self):
        command = "echo hello"
        stdout, stderr, return_code = execute_command(command)
        self.assertEqual(return_code, 0)
        self.assertEqual(stdout, "hello")
        self.assertEqual(stderr, "")

    def test_list_processes(self):
        processes = list_processes()
        self.assertIsInstance(processes, list)
        if processes:
            self.assertIn('pid', processes[0])
            self.assertIn('name', processes[0])

if __name__ == '__main__':
    unittest.main()
