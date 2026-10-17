"""Run the local CLI demo or the configured Neuro-SAN agent network."""

import argparse
import asyncio
import os
from pathlib import Path
import subprocess
import sys

from demo_cli import main as cli_main

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = PROJECT_ROOT / "registries" / "scheme_navigator_manifest.hocon"


def run_agent_network() -> int:
    """Start Neuro-SAN Studio with this project's manifest and coded tools."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("python-dotenv is required for agent mode; install project requirements first.", file=sys.stderr)
        return 1

    load_dotenv(PROJECT_ROOT / ".env", override=False)
    environment = os.environ.copy()

    manifest = Path(environment.get("AGENT_MANIFEST_FILE", str(DEFAULT_MANIFEST)))
    if not manifest.is_absolute():
        manifest = PROJECT_ROOT / manifest
    tool_path = Path(environment.get("AGENT_TOOL_PATH", "coded_tools"))
    if not tool_path.is_absolute():
        tool_path = PROJECT_ROOT / tool_path

    environment["AGENT_MANIFEST_FILE"] = str(manifest.resolve())
    environment["AGENT_TOOL_PATH"] = str(tool_path.resolve())
    existing_pythonpath = environment.get("PYTHONPATH", "")
    pythonpath_entries = [str(PROJECT_ROOT)]
    if existing_pythonpath:
        pythonpath_entries.append(existing_pythonpath)
    environment["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)

    command = [sys.executable, "-m", "neuro_san_studio", "run"]
    print("Starting the Scheme Navigator Neuro-SAN network and nsflow UI...")
    print(f"Manifest: {manifest.resolve()}")
    try:
        return subprocess.run(command, cwd=PROJECT_ROOT, env=environment, check=False).returncode
    except FileNotFoundError:
        print("Neuro-SAN Studio is not installed in this Python environment.", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Scheme Navigator demo and Neuro-SAN agent network")
    parser.add_argument(
        "--agent",
        action="store_true",
        help="Start the configured Neuro-SAN server and nsflow UI",
    )
    args = parser.parse_args()

    if args.agent:
        return run_agent_network()
    asyncio.run(cli_main())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
