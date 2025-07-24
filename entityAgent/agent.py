import sys
import subprocess
import time
try:
    import ollama
except ImportError:
    print("Ollama Python package not found. Attempting to install ollama...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ollama"])
    import ollama
from entityAgent.platform_interaction import execute_command, get_operating_system, list_processes

def runtime():
    """
    Main function to run the Entity agent.
    """
    print("Entity Agent: Initializing...")


    # Check if Ollama is running, try to start with default model if not found
    try:
        ollama.list()
    except Exception:
        print("Ollama is not running. Attempting to start Ollama with default model 'llama3'...")
        try:
            # Check if ollama CLI is installed
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                print("Ollama CLI not found. Please install Ollama from https://ollama.com/download and ensure it is in your PATH.")
                sys.exit(1)
            # Check if model is present
            model_list = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if "llama3" not in model_list.stdout:
                print("Downloading model 'llama3'...")
                pull_result = subprocess.run(["ollama", "pull", "llama3"], capture_output=True, text=True)
                if pull_result.returncode != 0:
                    print(f"Failed to download model 'llama3': {pull_result.stderr}")
                    sys.exit(1)
            subprocess.Popen(["ollama", "run", "llama3"])
            time.sleep(5)  # Give Ollama some time to start
            ollama.list()
            print("Ollama started successfully with model 'llama3'.")
        except Exception as e:
            print(f"Error: Could not start Ollama automatically. Please start the Ollama service and try again.\nDetails: {e}")
            sys.exit(1)

    print("Ollama connection successful.")
    
    os_name = get_operating_system()
    print(f"Running on: {os_name}. Welcome to Entity.")
    print("You can ask me questions, run terminal commands (e.g., 'run: ls -l'), or list processes (e.g., 'run: list_processes').")

    system_prompt = f"""You are Entity, an AI assistant running on {os_name}.
You have the following capabilities:
1. Execute terminal commands: `run: <command>`
2. List running processes: `run: list_processes`

When the user asks you to perform a task, respond with the appropriate command."""

    messages = [{'role': 'system', 'content': system_prompt}]

    while True:
        try:
            user_input = input("> ")
            if user_input.lower() in ["exit", "quit"]:
                break

            if user_input.lower().startswith("run:"):
                command_full = user_input[4:].strip()
                
                if command_full == "list_processes":
                    print("Listing running processes...")
                    processes = list_processes()
                    process_list_str = "\n".join([f"PID: {p['pid']}, Name: {p['name']}, User: {p['username']}" for p in processes])
                    print(process_list_str)
                    messages.append({'role': 'assistant', 'content': f"Executed command: 'list_processes'\nOutput:\n{process_list_str}"})
                else:
                    command = command_full
                    print(f"Executing command: '{command}'")
                    stdout, stderr, return_code = execute_command(command)
                    
                    if return_code == 0:
                        print("Output:")
                        print(stdout)
                    else:
                        print("Error:")
                        print(stderr)
                    messages.append({'role': 'assistant', 'content': f"Executed command: '{command}'\nOutput:\n{stdout}\nError:\n{stderr}"})
            else:
                messages.append({'role': 'user', 'content': user_input})
                response = ollama.chat(model='llama3', messages=messages)
                assistant_response = response['message']['content']
                print(assistant_response)
                messages.append({'role': 'assistant', 'content': assistant_response})

        except KeyboardInterrupt:
            print("\nExiting Entity Agent.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    runtime()
