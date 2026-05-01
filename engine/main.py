"""
SubAligner Engine - Python FastAPI Sidecar
AI-powered forced alignment + silence removal
"""
import sys
import argparse
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import align, audio, silence, export, model

app = FastAPI(title="SubAligner Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(align.router, prefix="/api")
app.include_router(audio.router, prefix="/api")
app.include_router(silence.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(model.router, prefix="/api")


@app.post("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


def main():
    parser = argparse.ArgumentParser(description="SubAligner Engine")
    parser.add_argument("--port", type=int, default=9580, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    uvicorn.run(
        "main:app" if args.reload else app,
        host=args.host,
        port=args.port,
        log_level="info",
        reload=args.reload,
        reload_dirs=["."] if args.reload else None,
        timeout_keep_alive=600,
        limit_max_requests=None,
        workers=1,  # Single worker — torch is not thread-safe
    )


if __name__ == "__main__":
    main()
