import argparse
import os
import sys
import time

from entityAgent import ensure_ollama_ready, setup_ollama_cli
from entityAgent.platform_interaction import execute_command, get_operating_system, list_processes


def _handle_command(command: str) -> str:
    if command == "list_processes":
        print("Listing running processes...")
        processes = list_processes()
        result = "\n".join(
            f"PID: {p['pid']}, Name: {p['name']}, User: {p['username']}"
            for p in processes
        )
        print(result)
        return result
    print(f"Executing command: '{command}'")
    stdout, stderr, return_code = execute_command(command)
    if return_code == 0:
        print("Output:")
        print(stdout)
    else:
        print("Error:")
        print(stderr)
    return stdout if return_code == 0 else stderr


def _process_llm_command(assistant_response: str, messages: list) -> str:
    command = assistant_response.strip()[4:].strip()
    if command == "list_processes":
        print("Entity is listing running processes...")
        processes = list_processes()
        result = "\n".join(
            f"PID: {p['pid']}, Name: {p['name']}, User: {p['username']}"
            for p in processes
        )
        print(result)
        return result
    print(f"Entity is executing: {command}")
    stdout, stderr, return_code = execute_command(command)
    if return_code == 0:
        print(f"Output:\n{stdout}")
        return f"Command execution result:\n{stdout}"
    print(f"Error:\n{stderr}")
    return f"Command failed with error:\n{stderr}"


def _chat_loop(messages: list, model: str) -> None:
    import ollama

    while True:
        response = ollama.chat(model=model, messages=messages)
        assistant_response = response["message"]["content"]

        if assistant_response.strip().lower().startswith("run:"):
            print(assistant_response)
            messages.append({"role": "assistant", "content": assistant_response})
            result = _process_llm_command(assistant_response, messages)
            messages.append({"role": "system", "content": result})
        else:
            print(assistant_response)
            messages.append({"role": "assistant", "content": assistant_response})
            break


def runtime() -> None:
    print("Entity Agent: Initializing...")
    ensure_ollama_ready()
    import ollama
    print("Ollama connection successful.")

    os_name = get_operating_system()
    print(f"Running on: {os_name}. Welcome to Entity.")
    print("You can ask me questions, run terminal commands (e.g., 'run: ls -l'), or list processes (e.g., 'run: list_processes').")

    system_prompt = (
        f"You are Entity, an AI assistant running on {os_name}.\n"
        "You have the following capabilities:\n"
        "1. Execute terminal commands: `run: <command>`\n"
        "2. List running processes: `run: list_processes`\n"
        "3. If you run a command, I will show you the output, and you can decide what to do next.\n\n"
        "To execute a command, your response must start with \"run:\". "
        "Do not put any explanation before the command.\n"
        "Example:\n"
        "run: ls -la\n\n"
        "When the user asks you to perform a task, use these capabilities to achieve the goal.\n"
        "If the user asks a question that requires information from the system, run a command to get it."
    )

    messages = [{"role": "system", "content": system_prompt}]
    from entityAgent.config import load_config
    config = load_config()
    llm_model = config.model
    print(f"Using LLM model: {llm_model}", flush=True)

    while True:
        try:
            user_input = input("> ")
            match user_input.lower():
                case "exit" | "quit":
                    print("Exiting Entity Agent.")
                    break

            if user_input.lower().startswith("run:"):
                command = user_input[4:].strip()
                result = _handle_command(command)
                messages.append(
                    {
                        "role": "assistant",
                        "content": f"Executed command: '{command}'\nOutput:\n{result}",
                    }
                )
            else:
                messages.append({"role": "user", "content": user_input})
                _chat_loop(messages, llm_model)

        except KeyboardInterrupt:
            print("\nExiting Entity Agent.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")


def _start_web_server(host: str, port: int) -> None:
    import uvicorn
    url = f"http://{host}:{port}"
    print(f"Starting Web Interface at {url}")
    uvicorn.run("entityAgent.web.server:app", host=host, port=port, log_level="error", reload=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Entity Agent CLI")
    parser.add_argument("--install-ollama", action="store_true", help="Install Ollama CLI and exit.")
    parser.add_argument("--llm-model", type=str, help="Specify the LLM model to use.")
    parser.add_argument("--web", action="store_true", help="Start the Web Interface.")
    parser.add_argument("--gui", action="store_true", help="Start the Native GUI.")
    args = parser.parse_args()

    if args.install_ollama:
        setup_ollama_cli()
        sys.exit(0)

    from entityAgent.config import load_config
    config = load_config()
    if args.llm_model:
        config.model = args.llm_model
    if config.server_url:
        os.environ["OLLAMA_HOST"] = config.server_url
    os.environ["ENTITY_LLM_MODEL"] = config.model

    if args.web or args.gui:
        host = "127.0.0.1"
        port = 8000
        if args.gui:
            try:
                import webview
            except ImportError:
                print("Error: pywebview is not installed. Please install it with 'pip install pywebview'.")
                sys.exit(1)
            import threading
            t = threading.Thread(target=_start_web_server, args=(host, port), daemon=True)
            t.start()
            time.sleep(1)
            print("Starting Native GUI...")
            webview.create_window("Entity Agent", f"http://{host}:{port}")
            try:
                webview.start()
            except Exception as e:
                print(f"Warning: Could not start native GUI: {e}")
                print("This is common in WSL or headless environments.")
                print(f"The Web Interface is still running at http://{host}:{port}")
                print("Press Ctrl+C to exit.")
                while True:
                    time.sleep(1)
        else:
            _start_web_server(host, port)
    else:
        runtime()


if __name__ == "__main__":
    main()
