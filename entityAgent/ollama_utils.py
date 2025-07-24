import sys
import subprocess

def ensure_ollama_installed():
    try:
        import ollama
        return True
    except ImportError:
        print("Ollama Python package not found. Attempting to install ollama...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ollama"])
        try:
            import ollama
            return True
        except ImportError:
            print("Failed to install ollama Python package. Please install it manually.")
            return False

def ensure_ollama_cli_and_model(model_name="llama3"):
    # Check if ollama CLI is installed
    result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Ollama CLI not found. Attempting to download and install Ollama...")
        import platform
        import shutil
        system = platform.system().lower()
        try:
            if system == "linux":
                # Download and install Ollama for Linux (x86_64)
                import tempfile
                import tarfile
                import urllib.request
                ollama_url = "https://ollama.com/download/ollama-linux-amd64.tar.gz"
                with tempfile.TemporaryDirectory() as tmpdir:
                    tar_path = f"{tmpdir}/ollama.tar.gz"
                    urllib.request.urlretrieve(ollama_url, tar_path)
                    with tarfile.open(tar_path, "r:gz") as tar:
                        tar.extractall(tmpdir)
                    bin_path = shutil.move(f"{tmpdir}/ollama", "/usr/local/bin/ollama")
                subprocess.run(["chmod", "+x", "/usr/local/bin/ollama"])
                print("Ollama CLI installed to /usr/local/bin/ollama.")
            elif system == "darwin":
                # macOS: use Homebrew if available, else print instructions
                if shutil.which("brew"):
                    subprocess.check_call(["brew", "install", "ollama"])
                else:
                    print("Please install Homebrew and run: brew install ollama, or download from https://ollama.com/download")
                    sys.exit(1)
            elif system == "windows":
                print("Please download and install Ollama for Windows from https://ollama.com/download and ensure it is in your PATH.")
                sys.exit(1)
            else:
                print(f"Unsupported OS: {system}. Please install Ollama manually from https://ollama.com/download.")
                sys.exit(1)
        except Exception as e:
            print(f"Automatic Ollama CLI installation failed: {e}\nPlease install manually from https://ollama.com/download.")
            sys.exit(1)
    # Check if model is present
    model_list = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if model_name not in model_list.stdout:
        print(f"Downloading model '{model_name}'...")
        pull_result = subprocess.run(["ollama", "pull", model_name], capture_output=True, text=True)
        if pull_result.returncode != 0:
            print(f"Failed to download model '{model_name}': {pull_result.stderr}")
            sys.exit(1)
    return True
