import ollama
import sys
from .platform_interaction import execute_command, get_operating_system, list_processes

def runtime():
    """
    Main function to run the Entity agent.
    """
    print("Entity Agent: Initializing...")

    # Check if Ollama is running
    try:
        ollama.list()
    except Exception:
        print("Error: Ollama is not running. Please start the Ollama service and try again.")
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
