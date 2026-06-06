#!/usr/bin/env python3
import os
import json
import logging
import asyncio
import httpx
import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except Exception:
    CHROMA_AVAILABLE = False

app = FastAPI(title="function-gemma", version="0.1.0")
logger = logging.getLogger("function-gemma")
logging.basicConfig(level=logging.INFO)

# Simple local chroma client (if available)
CHROMA_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./data/chroma")
chroma_client = None
if CHROMA_AVAILABLE:
    try:
        # Newer chroma versions have changed client initialization. Try to initialize
        # with a minimal Settings object and fall back gracefully if it fails.
        settings = Settings(persist_directory=CHROMA_DIR)
        chroma_client = chromadb.Client(settings)
    except Exception as e:
        logger.warning("Chroma initialization failed: %s. Chroma features disabled.", e)
        chroma_client = None
        CHROMA_AVAILABLE = False

class ExecuteRequest(BaseModel):
    function_name: str
    parameters: dict = {}

class EmbedRequest(BaseModel):
    texts: list
    ids: list = None

@app.get("/health")
async def health():
    return {"status": "ok", "chroma_available": CHROMA_AVAILABLE}

def run_ollama_text(prompt: str, model: str = os.environ.get("REHOBOAM_LLM_MODEL", "granite3:3b")) -> str:
    """Run Ollama model to generate text output. Uses ollama CLI."""
    try:
        # Use --quiet or similar if available
        completed = subprocess.run(["ollama", "run", model, "--prompt", prompt], capture_output=True, text=True, timeout=30)
        if completed.returncode != 0:
            logger.error("ollama error: %s", completed.stderr)
            raise RuntimeError(completed.stderr.strip() or "ollama failed")
        return completed.stdout.strip()
    except FileNotFoundError:
        logger.warning("ollama not found on PATH; falling back to mock")
        return f"[mock response] {prompt[:120]}"

def run_ollama_embed(text: str, model: str = os.environ.get("REHOBOAM_EMBED_MODEL", "granite3:embed-3b")) -> list:
    """Call ollama embed; fallback to deterministic pseudo-random vector if unavailable"""
    try:
        completed = subprocess.run(["ollama", "embed", model, text], capture_output=True, text=True, timeout=30)
        if completed.returncode == 0 and completed.stdout:
            # Expect JSON array or whitespace-separated floats
            out = completed.stdout.strip()
            try:
                return json.loads(out)
            except Exception:
                # try split
                return [float(x) for x in out.split() if x]
        else:
            logger.warn("ollama embed failed, stderr=%s", completed.stderr)
    except FileNotFoundError:
        logger.warn("ollama CLI not found; using fallback embedding")

    # Fallback deterministic embedding
    import hashlib
    import struct
    h = hashlib.sha256(text.encode('utf-8')).digest()
    return [
        float(int.from_bytes(h[i : i + 2], 'big') % 1000) / 1000.0
        for i in range(0, min(len(h), 256), 2)
    ]

@app.post("/execute")
async def execute(req: ExecuteRequest):
    """Execute a function using the LLM or local handlers."""
    logger.info("execute request: %s", req.function_name)

    # For MVP: if function_name starts with 'llm:' we ask the LLM; otherwise, we forward to LLM to simulate execution
    if req.function_name.startswith("llm:"):
        prompt = f"Execute function {req.function_name} with parameters {json.dumps(req.parameters)} and return a JSON-serializable result.\nReturn only JSON."
        out = run_ollama_text(prompt)
        try:
            return {"success": True, "result": json.loads(out)}
        except Exception:
            return {"success": True, "result": out}

    # Default: simple pass-through
    prompt = f"You are FunctionGemma. Run function {req.function_name} with parameters {json.dumps(req.parameters)} and return the results as JSON." 
    out = run_ollama_text(prompt)
    try:
        return {"success": True, "result": json.loads(out)}
    except Exception:
        return {"success": True, "result": out}

@app.post("/embed")
async def embed(req: EmbedRequest):
    if not CHROMA_AVAILABLE:
        # compute embeddings but don't store
        vectors = [run_ollama_embed(t) for t in req.texts]
        return {"success": True, "vectors": vectors}

    # ensure collection exists
    collection_name = os.environ.get("CHROMA_COLLECTION", "rehoboam-embeddings")
    try:
        col = chroma_client.get_collection(collection_name)
    except Exception:
        # Newer Chroma clients may require a named parameter for create_collection
        try:
            col = chroma_client.create_collection(name=collection_name)
        except TypeError:
            col = chroma_client.create_collection(collection_name)

    ids = req.ids or [f"id-{i}" for i in range(len(req.texts))]
    vectors = [run_ollama_embed(t) for t in req.texts]

    # upsert into chroma (newer clients handle persistence automatically)
    col.upsert(ids=ids, metadatas=[{"source": "function-gemma"}] * len(ids), documents=req.texts, embeddings=vectors)

    return {"success": True, "upserted": len(ids)}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.environ.get("PORT", 3111)), log_level="info")
