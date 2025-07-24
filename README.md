# Entity - A Cross-Platform LLM Agent

Entity is a Python-based AI agent designed to interact with your operating system, execute commands, and control programs across Windows, macOS, and Linux.

## Architecture

This agent uses a local Large Language Model (LLM) powered by Ollama. This ensures that all data and interactions remain private and on your local machine.

The core components are:
- **Agent Logic:** The main Python application that orchestrates tasks.
- **LLM Service:** An Ollama server running a local model (e.g., Llama 3).
- **Platform Interaction:** Modules for interacting with the specific operating system's terminal and applications.

## Getting Started

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running.
- A downloaded Ollama model (e.g., `ollama run llama3`)

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd entity
    ```

2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Agent

```bash
python main.py
```

## Usage

You can interact with the agent in two ways:

1.  **Natural Language:** Ask questions or give commands in plain English.
    ```
    > Tell me a joke.
    > What is the capital of France?
    ```

2.  **Commands:** Use the `run:` prefix to execute shell commands or use built-in functions.
    -   **Execute a shell command:**
        ```
        > run: ls -l
        ```
    -   **List running processes:**
        ```
        > run: list_processes
## Testing

To run the test suite, execute the following command:

```bash
pytest
```