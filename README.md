
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
- [x] Add UI options (CLI, Web, GUI)
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

You can interact with the agent via the Command Line Interface (CLI) or the Web Interface.

### 1. Command Line Interface (CLI)

Start the agent in your terminal:

```bash
entity-agent
```

**Natural Language Interaction:**
Simply type your request.
```
> Tell me a joke about programming.
> Summarize the current directory contents.
```

**System Commands:**
You can ask the agent to execute system commands.
```
> run: ls -la
> run: echo "Hello World" > hello.txt
```

**Process Management:**
View running processes.
```
> run: list_processes
```

### 2. Web Interface

The Entity Agent comes with a built-in Web UI for a more visual experience.

**Starting the Web UI:**

```bash
entity-agent --web
```
Or using python:
```bash
python -m entityAgent.runtime --web
```

Open your browser and navigate to: `http://localhost:8000`

**Features:**
- **Chat Interface:** Interact with the LLM just like in the terminal.
- **Command Execution:** Run shell commands directly from the web interface.
- **Process Viewer:** View a list of active system processes.

### 3. Use Cases

Here are some examples of what you can do with Entity Agent:

#### 📁 File Management
- **Create files:** "Create a python script named `hello.py` that prints 'Hello'."
- **Organize:** "List all PDF files in the Downloads folder." (requires appropriate command usage)

#### 💻 System Control
- **Check Status:** "List all running processes."
- **Execute:** "Run `ipconfig` (Windows) or `ifconfig` (Linux/macOS) to check network settings."

#### 🧠 AI Assistance
- **Coding Help:** "Write a function to calculate the Fibonacci sequence."
- **General Knowledge:** "Explain the theory of relativity."

## Testing

To run the test suite, execute the following command:

```bash
pytest
```

### Checking Code Coverage

To check code coverage locally:

```bash
pip install pytest-cov
pytest --cov=entityAgent tests/
```
