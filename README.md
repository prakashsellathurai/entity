
Entity: The  AI agent that bridges you and your OS—seamlessly execute commands and control apps on Windows, macOS, and Linux.

[![Run Pytest](https://github.com/prakashsellathurai/entity/actions/workflows/pytest.yml/badge.svg)](https://github.com/prakashsellathurai/entity/actions/workflows/pytest.yml)
[![cross platform-ci](https://github.com/prakashsellathurai/entity/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/prakashsellathurai/entity/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/entityagent)](https://pypi.org/project/entityagent/)
[![Python version](https://img.shields.io/pypi/pyversions/entityagent)](https://pypi.org/project/entityagent/)


## Architecture
This agent uses a local Large Language Model (LLM) powered by Ollama. By default, it connects to a locally running Ollama server and uses the default model (e.g., `llama3`). All data and interactions remain private and on your local machine.

The core components are:
- **Agent Logic:** The main Python application that orchestrates tasks.
- **LLM Service:** An Ollama server running a local model (e.g., Llama 3).
- **Platform Interaction:** Modules for interacting with the specific operating system's terminal and applications.


## Getting Started
### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running (default: `ollama serve`)
- A downloaded Ollama model (default: `llama3`, run `ollama run llama3` to download)



### Installation
#### From PyPI (recommended)

```bash
pip install entityagent
```

#### From source

```bash
git clone https://github.com/prakashsellathurai/entity
cd entity
pip install .
```


### Running the Agent (Default Ollama)


You can run the agent from the command line (it will use the default Ollama model):


```bash
entity-agent
```
or
```bash
python -m entityAgent.runtime
```
## TODO / Roadmap

- [x] Allow configuration of LLM model (e.g., choose `llama3`, `mistral`, etc.)
- [x] Add support for configuring LLM server URL/port
- [ ] Add UI options (CLI, Web, GUI)
- [x] Add configuration file for user preferences
- [ ] Extend platform interaction capabilities




## Configuration

You can configure the Entity Agent using a `config.yaml` file or environment variables.

### Configuration File
Create a `config.yaml` file in your current directory or in `~/.entity/config.yaml`.

```yaml
model: llama3          # The Ollama model to use (default: llama3)
server_url: http://localhost:11434  # The Ollama server URL (optional)
```

### Environment Variables
Environment variables take precedence over the configuration file.

- `ENTITY_LLM_MODEL`: The Ollama model to use.
- `ENTITY_OLLAMA_URL`: The Ollama server URL.

## Usage

You can interact with the agent in two ways:

1.  **Natural Language:**
    ```
    > Tell me a joke.
    > What is the capital of France?
    ```

2.  **Commands:**
    -   **Execute a shell command:**
        ```
        > run: ls -l
        ```
    -   **List running processes:**
        ```
        > run: list_processes
        ```

## Testing

To run the test suite, execute the following command:

```bash
pytest
```
