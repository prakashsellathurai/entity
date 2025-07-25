from __future__ import annotations

import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from typing import Final


class OllamaSetupError(RuntimeError):
    """Raised when automatic set-up cannot be completed."""


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """
    Wrapper around subprocess.run with sane defaults.
    Raises OllamaSetupError if the command fails and `check=True`.
    """
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise OllamaSetupError(
            f"Command '{' '.join(cmd)}' failed:\n{result.stderr or result.stdout}"
        )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 1. Python package handling
# ──────────────────────────────────────────────────────────────────────────────
def ensure_python_package(pkg_name: str = "ollama") -> None:
    """
    Ensure a Python package is importable, installing it via pip if necessary.
    """
    try:
        __import__(pkg_name)
    except ImportError:
        print(f"[INFO] Missing Python package '{pkg_name}'. Installing…")
        _run([sys.executable, "-m", "pip", "install", pkg_name])


# ──────────────────────────────────────────────────────────────────────────────
# 2. CLI handling
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class OllamaCLI:
    """
    Helper class that guarantees the Ollama CLI and a specific model exist.
    """

    model: str = "llama3"
    linux_url: str = os.environ.get("OLLAMA_LINUX_URL", "https://ollama.com/download/ollama-linux-amd64.tar.gz")

    # Computed attributes (populated at runtime)
    executable: str | None = None
    _system: Final[str] = platform.system().lower()

    # ── Public API ───────────────────────────────────────────────────────────
    def ensure_ready(self) -> None:
        """Main entry point called by user code."""
        self._locate_or_install_cli()
        self._verify_cli()
        self._ensure_model()
        self._ensure_server_running()

    # ── Internals ────────────────────────────────────────────────────────────
    # 2.1 Locate or install CLI
    def _locate_or_install_cli(self) -> None:
        self.executable = self._find_existing_cli() or self._try_auto_install()
        if not self.executable:
            raise OllamaSetupError(
                "Ollama CLI not found. Please install it from https://ollama.com/download"
            )

    def _find_existing_cli(self) -> str | None:
        """Return an existing CLI path if found, else None."""
        candidate = "ollama" if self._system != "windows" else "ollama.exe"

        # PATH lookup
        path_lookup = shutil.which(candidate)
        if path_lookup:
            return path_lookup

        # Windows default install dir
        if self._system == "windows":
            user_profile = os.environ.get("USERPROFILE")
            if user_profile:
                default = pathlib.Path(user_profile) / r"AppData\Local\Programs\Ollama\ollama.exe"
                if default.exists():
                    return str(default)

        return None

    def _try_auto_install(self) -> str | None:
        """
        Attempt silent install on Linux (tarball), macOS (Homebrew), or Windows (installer).
        Returns path to executable if successful, else None.
        """
        try:
            if self._system == "linux":
                return self._install_linux_tar()
            if self._system == "darwin":
                return self._install_via_brew()
            if self._system == "windows":
                return self._install_windows_exe()
        except Exception as exc:
            print(f"[WARN] Automatic CLI installation failed: {exc}")
        return None

    def _install_windows_exe(self) -> str:
        import urllib.error
        import ctypes
        win_url = os.environ.get(
            "OLLAMA_WINDOWS_URL",
            "https://ollama.com/download/OllamaSetup.exe"
        )
        with tempfile.TemporaryDirectory() as tmp:
            exe_path = pathlib.Path(tmp) / "OllamaSetup.exe"
            try:
                print(f"[INFO] Downloading Ollama CLI installer from {win_url}")
                urllib.request.urlretrieve(win_url, exe_path)
            except urllib.error.HTTPError as e:
                print(f"[ERROR] Failed to download Ollama CLI installer: HTTP {e.code} {e.reason}\nURL: {win_url}")
                raise OllamaSetupError(f"Failed to download Ollama CLI installer: {e}")
            except Exception as e:
                print(f"[ERROR] Unexpected error downloading Ollama CLI installer: {e}\nURL: {win_url}")
                raise OllamaSetupError(f"Failed to download Ollama CLI installer: {e}")
            print(f"[INFO] Running Ollama CLI installer...")
            # Try to run the installer silently, fallback to normal if not supported
            try:
                # Try silent install (if supported by installer)
                result = subprocess.run([str(exe_path), "/S"], capture_output=True)
                if result.returncode != 0:
                    print("[WARN] Silent install failed, running installer interactively...")
                    # Run interactively
                    if sys.platform == "win32":
                        # Use ShellExecute to show UAC prompt if needed
                        ctypes.windll.shell32.ShellExecuteW(None, "open", str(exe_path), None, None, 1)
                    else:
                        subprocess.Popen([str(exe_path)])
                    print("[INFO] Please complete the Ollama installation in the window that appears.")
                    input("Press Enter after installation is complete...")
                else:
                    print("[INFO] Ollama CLI installed successfully.")
            except Exception as e:
                print(f"[ERROR] Could not run Ollama installer: {e}")
                raise OllamaSetupError(f"Failed to run Ollama CLI installer: {e}")
            # After install, check for executable
            user_profile = os.environ.get("USERPROFILE")
            if user_profile:
                default = pathlib.Path(user_profile) / r"AppData\Local\Programs\Ollama\ollama.exe"
                if default.exists():
                    return str(default)
            # Try PATH
            path_lookup = shutil.which("ollama.exe")
            if path_lookup:
                return path_lookup
            raise OllamaSetupError("Ollama CLI installer completed, but ollama.exe not found. Please ensure it is installed and in your PATH.")

    # 2.2 Verify function
    def _verify_cli(self) -> None:
        """Ensure `ollama --version` works."""
        _run([self.executable, "--version"])

    # 2.3 Model availability
    def _ensure_model(self) -> None:
        models = _run([self.executable, "list"], check=False).stdout
        if self.model not in models:
            print(f"[INFO] Downloading Ollama model '{self.model}'…")
            _run([self.executable, "pull", self.model])

    # 2.4 Server availability
    def _ensure_server_running(self) -> None:
        try:
            import ollama

            ollama.list()
        except Exception:
            print("[INFO] Starting local Ollama server…")
            subprocess.Popen([self.executable, "run", self.model])
            time.sleep(5)  # allow startup
            import ollama

            ollama.list()

    # ── Platform-specific helpers ────────────────────────────────────────────
    def _install_linux_tar(self) -> str:
        # Use the official install script
        install_script_url = "https://ollama.com/install.sh"
        try:
            print(f"[INFO] Installing Ollama CLI using the official script: {install_script_url}")
            result = subprocess.run(
                ["sh", "-c", f"curl -fsSL {install_script_url} | sh"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"[ERROR] Ollama install script failed:\n{result.stderr or result.stdout}")
                raise OllamaSetupError("Ollama install script failed.")
            # After install, check for executable
            path_lookup = shutil.which("ollama")
            if path_lookup:
                print(f"[INFO] Installed Ollama CLI to {path_lookup}")
                return path_lookup
            raise OllamaSetupError("Ollama CLI installed, but not found in PATH.")
        except Exception as e:
            print(f"[ERROR] Failed to install Ollama CLI: {e}")
            raise OllamaSetupError(f"Failed to install Ollama CLI: {e}")

    def _install_via_brew(self) -> str:
        if not shutil.which("brew"):
            raise OllamaSetupError("Homebrew not found. Please install it manually.")
        _run(["brew", "install", "ollama"])
        return shutil.which("ollama")  # type: ignore[return-value]

# ──────────────────────────────────────────────────────────────────────────────
# 3. Standalone setup function for CLI installation
# ──────────────────────────────────────────────────────────────────────────────
def setup_ollama_cli(model: str = "llama3") -> None:
    """
    Standalone helper to set up the Ollama CLI for the current platform.
    Prints clear instructions if setup fails.
    """
    try:
        cli = OllamaCLI(model)
        cli._locate_or_install_cli()
        print(f"[SUCCESS] Ollama CLI is installed and ready at: {cli.executable}")
    except OllamaSetupError as e:
        print(f"[ERROR] Ollama CLI setup failed: {e}")
        if cli._system == "linux":
            print("[HINT] The default download URL may be broken. Set the environment variable OLLAMA_LINUX_URL to the correct tarball URL from https://ollama.com/download and re-run this script.")
        elif cli._system == "windows":
            print("[HINT] Download the Windows installer from https://ollama.com/download and run it manually if automatic setup fails.")
        elif cli._system == "darwin":
            print("[HINT] Try installing via Homebrew: brew install ollama")
        else:
            print("[HINT] Please install Ollama CLI manually for your platform.")

# ──────────────────────────────────────────────────────────────────────────────
# 4. High-level helper exposed to callers
# ──────────────────────────────────────────────────────────────────────────────
def ensure_ollama_ready(model: str = "llama3") -> None:
    """
    Convenience wrapper: ensure Python pkg, CLI, model and server are ready.
    """
    ensure_python_package("ollama")
    OllamaCLI(model).ensure_ready()


def uninstall_ollama_cli():
    """
    Uninstalls the Ollama CLI and related data.
    """
    system = platform.system().lower()
    try:
        if system == "windows":
            # Implement Windows uninstallation
            print("[INFO] Uninstalling Ollama CLI on Windows...")
            # 1. Locate installation directory
            user_profile = os.environ.get("USERPROFILE")
            if user_profile:
                ollama_dir = os.path.join(user_profile, "AppData", "Local", "Programs", "Ollama")
                # 2. Attempt to run uninstaller or delete directory
                uninstaller_path = os.path.join(ollama_dir, "Uninstall.exe") # Example name
                if os.path.exists(uninstaller_path):
                    print("[INFO] Running uninstaller...")
                    subprocess.run([uninstaller_path], check=True)
                elif os.path.exists(ollama_dir):
                    print(f"[INFO] Removing directory: {ollama_dir}")
                    shutil.rmtree(ollama_dir)
            # 3. Remove from PATH (requires modifying environment variables - not directly possible in script)
            print("[INFO] Please manually remove Ollama from your PATH environment variable.")

        elif system == "linux":
            # Implement Linux uninstallation
            print("[INFO] Uninstalling Ollama CLI on Linux...")
            # 1. Remove executable
            executable_path = "/usr/local/bin/ollama"  # Example path
            if os.path.exists(executable_path):
                print(f"[INFO] Removing executable: {executable_path}")
                os.remove(executable_path)
            # 2. Remove data directory
            data_dir = "/usr/share/ollama" # Example path
            if os.path.exists(data_dir):
                print(f"[INFO] Removing data directory: {data_dir}")
                shutil.rmtree(data_dir)

        elif system == "darwin":
            # Implement macOS uninstallation
            print("[INFO] Uninstalling Ollama CLI on macOS...")
            try:
                subprocess.run(["brew", "uninstall", "ollama"], check=True)
            except FileNotFoundError:
                print("[WARN] Homebrew not found. Please uninstall Ollama manually.")

        # Remove model data (all platforms)
        model_data_dir = os.path.expanduser("~/.ollama")
        if os.path.exists(model_data_dir):
            print(f"[INFO] Removing model data directory: {model_data_dir}")
            shutil.rmtree(model_data_dir)

        print("[SUCCESS] Ollama CLI uninstallation complete.")

    except Exception as e:
        print(f"[ERROR] Ollama CLI uninstallation failed: {e}")