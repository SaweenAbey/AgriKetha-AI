"""
AgriKetha-AI Unified Launch Script
Starts the Backend and all 3 AI Agent microservices in one place.
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
AGENTS_DIR = ROOT_DIR / "ai-agents"

sys.path.insert(0, str(BACKEND_DIR))
from app.services.agent_manager import start_all_agents, stop_all_agents

def main():
    print("=" * 60)
    print("🌾 Starting AgriKetha-AI Multi-Agent System (Unified)")
    print("=" * 60)

    # 1. Start all 3 agent microservices
    start_all_agents()

    print("[AgriKetha] Waiting 3s for agent microservices to warm up...")
    time.sleep(3)

    # 2. Start the Backend server (port 8000)
    print("[AgriKetha] Starting Backend Orchestrator on http://0.0.0.0:8000...")
    try:
        import uvicorn
        from app.core.config import settings
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=False,
        )
    except KeyboardInterrupt:
        print("\n[AgriKetha] Shutting down all services...")
    finally:
        stop_all_agents()
        print("[AgriKetha] All services stopped.")

if __name__ == "__main__":
    main()
