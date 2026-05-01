"""
PyInstaller build script for SubAligner Engine
Builds the Python engine into a standalone executable
"""
import subprocess
import sys
import platform
from pathlib import Path


def build():
    """Build the engine as a standalone executable"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Determine output name based on target
    if system == "darwin":
        if machine == "arm64":
            target_suffix = "aarch64-apple-darwin"
        else:
            target_suffix = "x86_64-apple-darwin"
    elif system == "windows":
        target_suffix = "x86_64-pc-windows-msvc"
    else:
        target_suffix = f"{machine}-unknown-linux"

    output_name = f"subaligner-engine-{target_suffix}"

    print(f"Building for: {system} {machine}")
    print(f"Output name: {output_name}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", output_name,
        "--clean",
        "--noconfirm",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "torchaudio",
        "--hidden-import", "torch",
        "main.py",
    ]

    subprocess.run(cmd, check=True)

    # Copy to Tauri binaries directory
    dist_dir = Path("dist")
    tauri_bin_dir = Path("../src-tauri/binaries")
    tauri_bin_dir.mkdir(exist_ok=True)

    ext = ".exe" if system == "windows" else ""
    src = dist_dir / f"{output_name}{ext}"

    if src.exists():
        import shutil
        dest = tauri_bin_dir / f"{output_name}{ext}"
        shutil.copy2(src, dest)
        print(f"Copied to: {dest}")
    else:
        print(f"ERROR: Built file not found at {src}")
        sys.exit(1)


if __name__ == "__main__":
    build()
