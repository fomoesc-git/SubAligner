"""
PyInstaller build script for SubAligner Engine
Builds the Python engine into a standalone executable
"""
import argparse
import os
import subprocess
import sys
import platform
import shutil
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def find_binary(name: str) -> str | None:
    """Find a binary on the system PATH"""
    return shutil.which(name)


def build(skip_pyinstaller: bool = False):
    """Build the engine as a standalone executable"""
    os.chdir(SCRIPT_DIR)

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

    if not skip_pyinstaller:
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

        # Bundle ffmpeg and ffprobe if available (required for offline use)
        for binary_name in ["ffmpeg", "ffprobe"]:
            binary_path = find_binary(binary_name)
            if binary_path:
                cmd.extend(["--add-binary", f"{binary_path}{os.pathsep}."])
                print(f"Found {binary_name}: {binary_path}")
            else:
                print(f"WARNING: {binary_name} not found on system. "
                      f"Audio processing may not work offline.")

        env = os.environ.copy()
        env.setdefault("PYINSTALLER_CONFIG_DIR", str(SCRIPT_DIR / ".pyinstaller-cache"))
        env.setdefault("MPLCONFIGDIR", str(SCRIPT_DIR / ".matplotlib-cache"))
        Path(env["PYINSTALLER_CONFIG_DIR"]).mkdir(exist_ok=True)
        Path(env["MPLCONFIGDIR"]).mkdir(exist_ok=True)
        subprocess.run(cmd, check=True, env=env)

    # Copy to the engine resource directory bundled by Tauri.
    dist_dir = Path("dist")
    engine_bin_dir = Path("bin")
    engine_bin_dir.mkdir(exist_ok=True)

    ext = ".exe" if system == "windows" else ""
    src = dist_dir / f"{output_name}{ext}"

    if src.exists():
        dest = engine_bin_dir / f"{output_name}{ext}"
        shutil.copy2(src, dest)
        print(f"Copied to: {dest}")
    else:
        print(f"ERROR: Built file not found at {src}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build SubAligner engine executable")
    parser.add_argument(
        "--skip-pyinstaller",
        action="store_true",
        help="Only copy an existing dist executable into engine/bin",
    )
    args = parser.parse_args()
    build(skip_pyinstaller=args.skip_pyinstaller)
