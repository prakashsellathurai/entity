import subprocess
import sys
import os
import pytest


# Use the correct module for CLI entry point
AGENT_MODULE = "entityAgent.runtime"


import re

@pytest.mark.parametrize("inputs,expected_patterns", [
    # Shell command
    (["run: echo hello"], [r"hello"]),
    # List processes
    (["run: list_processes"], [r"PID:.*Name:.*User:"]),
    # Natural language
    (["Tell me a joke."], [r"(?i)joke|funny|laugh|smile"]),
    # Invalid command
    (["run: foobarbazcommand"], [r"Error:", r"not found|No such file|is not recognized"]),
    # Multiple commands
    (["run: echo test1", "run: echo test2"], [r"test1", r"test2"]),
    # Exit
    (["exit"], [r"Exiting Entity Agent."]),
])
def test_agent_e2e(inputs, expected_patterns):
    """
    End-to-end test for the agent CLI.
    Simulates user input and checks for expected output patterns.
    """
    cmd = [sys.executable, "-m", AGENT_MODULE]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy(),
    )
    try:
        for line in inputs:
            proc.stdin.write(line + "\n")
        proc.stdin.write("exit\n")
        proc.stdin.flush()
        stdout, stderr = proc.communicate(timeout=60)
        for pat in expected_patterns:
            assert re.search(pat, stdout), f"Expected pattern '{pat}' in output. Got: {stdout}"
    finally:
        proc.kill()
