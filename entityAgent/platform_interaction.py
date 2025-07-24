import platform
import subprocess
import sys

def get_operating_system():
    os_name = platform.system()
    if os_name == 'Darwin':
        return 'macOS'
    return os_name

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        return_code = result.returncode
        return stdout, stderr, return_code
    except Exception as e:
        return '', str(e), 1

def list_processes():
    import psutil
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes
