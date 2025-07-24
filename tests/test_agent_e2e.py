import subprocess
import sys
import os
import pytest

AGENT_MODULE = "entityAgent.agent"

@pytest.mark.parametrize("input_cmd,expected_output", [
    ("run: echo hello", "hello"),
    ("run: list_processes", "PID:"),
    ("exit", "Exiting Entity Agent."),
])
def test_agent_e2e(input_cmd, expected_output):
    """
    End-to-end test for the agent CLI.
    Simulates user input and checks for expected output.
    """
    # Prepare the command to run the agent
    cmd = [sys.executable, "-m", AGENT_MODULE]
    # Start the agent process
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy(),
    )
    try:
        # Send the input command and exit
        proc.stdin.write(input_cmd + "\n")
        proc.stdin.write("exit\n")
        proc.stdin.flush()
        # Read output
        stdout, stderr = proc.communicate(timeout=30)
        assert expected_output in stdout, f"Expected '{expected_output}' in output. Got: {stdout}"
    finally:
        proc.kill()
