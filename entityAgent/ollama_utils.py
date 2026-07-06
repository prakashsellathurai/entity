from __future__ import annotations

import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from typing import Final


class OllamaSetupError(RuntimeError):
    """Raised when automatic set-up cannot be completed."""


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise OllamaSetupError(
            f"Command '{' '.join(cmd)}' failed:\n{result.stderr or result.stdout}"
        )
    return result


_SYSTEM: Final[str] = platform.system().lower()
_LINUX_URL: Final[str] = os.environ.get(
    "OLLAMA_LINUX_URL",
    "https://ollama.com/download/ollama-linux-amd64.tar.gz",
)
_WINDOWS_URL: Final[str] = os.environ.get(
    "OLLAMA_WINDOWS_URL",
    "https://ollama.com/download/OllamaSetup.exe",
)


# ──────────────────────────────────────────────────────────────────────────────
# 1. Python package handling
# ──────────────────────────────────────────────────────────────────────────────
def ensure_python_package(pkg_name: str = "ollama") -> None:
    try:
        __import__(pkg_name)
    except ImportError:
        print(f"[INFO] Missing Python package '{pkg_name}'. Installing\u2026")
        _run([sys.executable, "-m", "pip", "install", pkg_name])


# ──────────────────────────────────────────────────────────────────────────────
# 2. CLI discovery & installation
# ──────────────────────────────────────────────────────────────────────────────
def find_existing_cli() -> str | None:
    candidate = "ollama" if _SYSTEM != "windows" else "ollama.exe"
    path_lookup = shutil.which(candidate)
    if path_lookup:
        return path_lookup
    if _SYSTEM == "windows":
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            default = pathlib.Path(user_profile) / r"AppData\Local\Programs\Ollama\ollama.exe"
            if default.exists():
                return str(default)
    return None


def _install_windows_exe() -> str:
    import ctypes

    with tempfile.TemporaryDirectory() as tmp:
        exe_path = pathlib.Path(tmp) / "OllamaSetup.exe"
        try:
            print(f"[INFO] Downloading Ollama CLI installer from {_WINDOWS_URL}")
            _download_url(_WINDOWS_URL, exe_path)
        except urllib.error.HTTPError as e:
            raise OllamaSetupError(
                f"Failed to download Ollama CLI installer: HTTP {e.code} {e.reason}"
            )
        except Exception as e:
            raise OllamaSetupError(
                f"Failed to download Ollama CLI installer: {e}"
            ) from e
        print("[INFO] Running Ollama CLI installer\u2026")
        try:
            result = subprocess.run([str(exe_path), "/S"], capture_output=True)
            if result.returncode != 0:
                print("[WARN] Silent install failed, running installer interactively\u2026")
                if sys.platform == "win32":
                    ctypes.windll.shell32.ShellExecuteW(None, "open", str(exe_path), None, None, 1)
                else:
                    subprocess.Popen([str(exe_path)])
                print("[INFO] Please complete the Ollama installation in the window that appears.")
                input("Press Enter after installation is complete...")
        except Exception as e:
            raise OllamaSetupError(f"Could not run Ollama installer: {e}") from e
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            default = pathlib.Path(user_profile) / r"AppData\Local\Programs\Ollama\ollama.exe"
            if default.exists():
                return str(default)
        path_lookup = shutil.which("ollama.exe")
        if path_lookup:
            return path_lookup
        raise OllamaSetupError(
            "Ollama CLI installer completed, but ollama.exe not found."
        )


def _install_linux_tar() -> str:
    install_script_url = "https://ollama.com/install.sh"
    try:
        print(f"[INFO] Installing Ollama CLI using the official script: {install_script_url}")
        result = subprocess.run(
            ["sh", "-c", f"curl -fsSL {install_script_url} | sh"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise OllamaSetupError(
                f"Ollama install script failed:\n{result.stderr or result.stdout}"
            )
        path_lookup = shutil.which("ollama")
        if path_lookup:
            return path_lookup
        raise OllamaSetupError("Ollama CLI installed, but not found in PATH.")
    except Exception as e:
        raise OllamaSetupError(f"Failed to install Ollama CLI: {e}") from e


def _install_via_brew() -> str:
    if not shutil.which("brew"):
        raise OllamaSetupError("Homebrew not found. Please install it manually.")
    _run(["brew", "install", "ollama"])
    return shutil.which("ollama")


def _download_url(url: str, dest: pathlib.Path) -> None:
    with urllib.request.urlopen(url) as response:
        with open(dest, "wb") as f:
            shutil.copyfileobj(response, f)


def auto_install_cli() -> str | None:
    try:
        if _SYSTEM == "linux":
            return _install_linux_tar()
        if _SYSTEM == "darwin":
            return _install_via_brew()
        if _SYSTEM == "windows":
            return _install_windows_exe()
    except Exception as exc:
        print(f"[WARN] Automatic CLI installation failed: {exc}")
    return None


def locate_or_install_cli() -> str:
    executable = find_existing_cli() or auto_install_cli()
    if not executable:
        raise OllamaSetupError(
            "Ollama CLI not found. Please install it from https://ollama.com/download"
        )
    return executable


# ──────────────────────────────────────────────────────────────────────────────
# 3. CLI verification and model/server management
# ──────────────────────────────────────────────────────────────────────────────
def verify_cli(executable: str) -> None:
    _run([executable, "--version"])


def ensure_model(executable: str, model: str) -> None:
    models = _run([executable, "list"], check=False).stdout
    if model not in models:
        print(f"[INFO] Downloading Ollama model '{model}'\u2026")
        _run([executable, "pull", model])


def ensure_server_running(executable: str, model: str) -> None:
    try:
        import ollama
        ollama.list()
    except Exception:
        print("[INFO] Starting local Ollama server\u2026")
        subprocess.Popen([executable, "run", model])
        time.sleep(5)
        import ollama
        ollama.list()


def ensure_cli_ready(model: str) -> None:
    executable = locate_or_install_cli()
    verify_cli(executable)
    ensure_model(executable, model)
    ensure_server_running(executable, model)


# ──────────────────────────────────────────────────────────────────────────────
# 4. Standalone setup / uninstall
# ──────────────────────────────────────────────────────────────────────────────
def setup_ollama_cli(model: str = "llama3") -> None:
    try:
        executable = locate_or_install_cli()
        print(f"[SUCCESS] Ollama CLI is installed and ready at: {executable}")
    except OllamaSetupError as e:
        print(f"[ERROR] Ollama CLI setup failed: {e}")
        _print_install_hints()


def _print_install_hints() -> None:
    if _SYSTEM == "linux":
        print(
            "[HINT] The default download URL may be broken. "
            "Set the environment variable OLLAMA_LINUX_URL to the correct "
            "tarball URL from https://ollama.com/download and re-run this script."
        )
    elif _SYSTEM == "windows":
        print(
            "[HINT] Download the Windows installer from https://ollama.com/download "
            "and run it manually if automatic setup fails."
        )
    elif _SYSTEM == "darwin":
        print("[HINT] Try installing via Homebrew: brew install ollama")
    else:
        print("[HINT] Please install Ollama CLI manually for your platform.")


def ensure_ollama_ready(model: str = "llama3") -> None:
    ensure_python_package("ollama")
    ensure_cli_ready(model)


def uninstall_ollama_cli() -> None:
    system = platform.system().lower()
    try:
        if system == "windows":
            print("[INFO] Uninstalling Ollama CLI on Windows...")
            user_profile = os.environ.get("USERPROFILE")
            if user_profile:
                ollama_dir = os.path.join(user_profile, "AppData", "Local", "Programs", "Ollama")
                uninstaller_path = os.path.join(ollama_dir, "Uninstall.exe")
                if os.path.exists(uninstaller_path):
                    print("[INFO] Running uninstaller...")
                    subprocess.run([uninstaller_path], check=True)
                elif os.path.exists(ollama_dir):
                    print(f"[INFO] Removing directory: {ollama_dir}")
                    shutil.rmtree(ollama_dir)
            print("[INFO] Please manually remove Ollama from your PATH environment variable.")
        elif system == "linux":
            print("[INFO] Uninstalling Ollama CLI on Linux...")
            for exe_path in ("/usr/local/bin/ollama", "/usr/bin/ollama"):
                if os.path.exists(exe_path):
                    print(f"[INFO] Removing executable: {exe_path}")
                    os.remove(exe_path)
            for data_dir in ("/usr/share/ollama", "/usr/local/share/ollama"):
                if os.path.exists(data_dir):
                    print(f"[INFO] Removing data directory: {data_dir}")
                    shutil.rmtree(data_dir)
        elif system == "darwin":
            print("[INFO] Uninstalling Ollama CLI on macOS...")
            try:
                subprocess.run(["brew", "uninstall", "ollama"], check=True)
            except FileNotFoundError:
                print("[WARN] Homebrew not found. Please uninstall Ollama manually.")
        model_data_dir = os.path.expanduser("~/.ollama")
        if os.path.exists(model_data_dir):
            print(f"[INFO] Removing model data directory: {model_data_dir}")
            shutil.rmtree(model_data_dir)
        print("[SUCCESS] Ollama CLI uninstallation complete.")
    except Exception as e:
        print(f"[ERROR] Ollama CLI uninstallation failed: {e}")
