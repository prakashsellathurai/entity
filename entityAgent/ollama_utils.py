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
    linux_url: str = "https://ollama.com/download/ollama-linux-amd64.tar.gz"

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
        Attempt silent install on Linux (tarball) or macOS (Homebrew).
        Returns path to executable if successful, else None.
        """
        try:
            if self._system == "linux":
                return self._install_linux_tar()
            if self._system == "darwin":
                return self._install_via_brew()
        except Exception as exc:
            print(f"[WARN] Automatic CLI installation failed: {exc}")
        return None

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
        with tempfile.TemporaryDirectory() as tmp:
            tar_path = pathlib.Path(tmp) / "ollama.tgz"
            urllib.request.urlretrieve(self.linux_url, tar_path)
            with tarfile.open(tar_path) as tar:
                tar.extractall(tmp)
            bin_path = pathlib.Path(tmp) / "ollama"
            dest = pathlib.Path("/usr/local/bin/ollama")
            shutil.move(bin_path, dest)
            dest.chmod(dest.stat().st_mode | 0o111)  # ensure executable
            print(f"[INFO] Installed Ollama CLI to {dest}")
            return str(dest)

    def _install_via_brew(self) -> str:
        if not shutil.which("brew"):
            raise OllamaSetupError("Homebrew not found. Please install it manually.")
        _run(["brew", "install", "ollama"])
        return shutil.which("ollama")  # type: ignore[return-value]


# ──────────────────────────────────────────────────────────────────────────────
# 3. High-level helper exposed to callers
# ──────────────────────────────────────────────────────────────────────────────
def ensure_ollama_ready(model: str = "llama3") -> None:
    """
    Convenience wrapper: ensure Python pkg, CLI, model and server are ready.
    """
    ensure_python_package("ollama")
    OllamaCLI(model).ensure_ready()