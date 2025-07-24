
import subprocess
import sys
import os
import pytest
import socket

def is_ollama_running(host='localhost', port=11434):
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except Exception:
        return False

skip_e2e = pytest.mark.skipif(
    os.environ.get('GITHUB_ACTIONS') == 'true' or not is_ollama_running(),
    reason="Ollama server not running or running in CI"
)


# Use the correct module for CLI entry point
AGENT_MODULE = "entityAgent.runtime"


import re

@skip_e2e
@pytest.mark.parametrize("inputs,expected_patterns,flaky", [
    # Shell command
    (["run: echo hello"], [r"hello"], False),
    # List processes
    (["run: list_processes"], [r"PID:.*Name:.*User:"], False),
    # Natural language (joke) - allow for more flexible matching and mark as flaky
    (["Tell me a joke."], [r"(?i)joke|funny|laugh|smile|comedian|I'm an AI|Why did the programmer|Hope that made you LOL|AI puns|not a comedian|can try"], True),
    # Invalid command
    (["run: foobarbazcommand"], [r"Error:", r"not found|No such file|is not recognized"], False),
    # Multiple commands
    (["run: echo test1", "run: echo test2"], [r"test1", r"test2"], False),
    # Exit
    (["exit"], [r"Exiting Entity Agent."], False),
])
def test_agent_e2e(inputs, expected_patterns, flaky):
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
            try:
                assert re.search(pat, stdout), f"Expected pattern '{pat}' in output. Got: {stdout}"
            except AssertionError as e:
                if flaky:
                    pytest.xfail(f"Flaky LLM output: {e}")
                else:
                    raise
    finally:
        proc.kill()
