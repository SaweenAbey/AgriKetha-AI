import asyncio
import atexit
import os
import signal
import socket
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

from app.core.logging_config import logger

# Root of the AgriKetha project
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AI_AGENTS_DIR = PROJECT_ROOT / "ai-agents"

AGENT_CONFIGS = [
    {
        "name": "query-agent",
        "port": 8001,
        "dir": AI_AGENTS_DIR / "query-agent",
        "entry": "app.main:app",
        "custom_venv": AI_AGENTS_DIR / "query-agent" / "venv",
    },
    {
        "name": "vision-agent",
        "port": 8002,
        "dir": AI_AGENTS_DIR / "vision-agent",
        "entry": "app.main:app",
        "custom_venv": AI_AGENTS_DIR / "vision-agent" / "venv",
    },
    {
        "name": "research-agent",
        "port": 8004,
        "dir": AI_AGENTS_DIR / "research-agent",
        "entry": "app.main:app",
        "custom_venv": AI_AGENTS_DIR / "research-agent" / "venv",
    },
]

_agent_processes: Dict[str, subprocess.Popen] = {}


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if an agent is already listening on the given port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def get_python_executable_for_agent(config: dict) -> str:
    """Find the best Python executable for a given agent microservice."""
    custom_venv = config.get("custom_venv")
    if custom_venv and custom_venv.exists():
        if sys.platform == "win32":
            exe = custom_venv / "Scripts" / "python.exe"
        else:
            exe = custom_venv / "bin" / "python"
        if exe.exists():
            return str(exe)

    # Check root .venv
    root_venv = PROJECT_ROOT / ".venv"
    if root_venv.exists():
        if sys.platform == "win32":
            exe = root_venv / "Scripts" / "python.exe"
        else:
            exe = root_venv / "bin" / "python"
        if exe.exists():
            return str(exe)

    # Fallback to current running Python interpreter
    return sys.executable


def start_agent_process(config: dict) -> Optional[subprocess.Popen]:
    """Start a single agent microservice in the background if not already running."""
    name = config["name"]
    port = config["port"]
    agent_dir = config["dir"]
    entry = config["entry"]

    if not agent_dir.exists():
        logger.warning("Agent directory not found: %s", agent_dir)
        return None

    if is_port_in_use(port):
        logger.info("Agent [%s] is already running on port %d.", name, port)
        return None

    python_exe = get_python_executable_for_agent(config)
    cmd = [
        python_exe,
        "-m",
        "uvicorn",
        entry,
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(agent_dir)
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        # On Windows, spawn without popping up new CMD windows
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW

        proc = subprocess.Popen(
            cmd,
            cwd=str(agent_dir),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )

        _agent_processes[name] = proc
        logger.info(
            "Auto-started agent [%s] on port %d (PID: %d) using %s",
            name,
            port,
            proc.pid,
            python_exe,
        )
        return proc

    except Exception as exc:
        logger.error("Failed to auto-start agent [%s]: %s", name, exc)
        return None


def start_all_agents():
    """Start all 3 AI agent microservices (Query, Vision, Research)."""
    logger.info("Auto-initializing all AgriKetha AI Agent microservices...")
    for config in AGENT_CONFIGS:
        start_agent_process(config)


def stop_all_agents():
    """Terminate any child agent processes spawned by this manager."""
    for name, proc in list(_agent_processes.items()):
        try:
            if proc.poll() is None:
                logger.info("Stopping auto-started agent [%s] (PID: %d)...", name, proc.pid)
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
        except Exception as exc:
            logger.warning("Error stopping agent [%s]: %s", name, exc)
    _agent_processes.clear()


# Register cleanup on interpreter exit
atexit.register(stop_all_agents)
