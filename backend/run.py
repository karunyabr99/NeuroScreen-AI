import uvicorn
import os
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
import sys
from pathlib import Path

# Add current and parent directory to path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"🚀 Starting NeuroScreen AI Backend on http://{host}:{port}")
    print(f"📖 OpenAPI Swagger UI available at http://{host}:{port}/docs")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
