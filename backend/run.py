import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn
from app.core.config import settings
from app.services.agent_manager import start_all_agents

if __name__ == "__main__":
    # Auto-start all 3 agent microservices
    try:
        start_all_agents()
    except Exception as exc:
        print(f"[AgriKetha] Warning: Could not auto-start AI agents: {exc}")

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )


