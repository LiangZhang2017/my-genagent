import os, time, json, uuid, logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .core import run_agent

# -------------------- Config --------------------
APP_NAME       = os.getenv("APP_NAME", "TutorAgent")
AGENT_VERSION  = os.getenv("AGENT_VERSION", "v1.0.0")
FRONTEND_DIR   = os.getenv("FRONTEND_DIR", "/srv/ui-dist")     # where Vite build lands (container)
CORS_ORIGINS   = os.getenv("CORS_ORIGINS", "*")                # comma-separated or "*"
MANIFEST_PATH  = os.getenv("MANIFEST_PATH", "/srv/agent.manifest.json")  # optional, for /manifest

# Optional health dependencies (set to "required" if you want stricter readiness)
REQUIRE_OPENAI = os.getenv("REQUIRE_OPENAI", "false").lower() in {"1","true","yes"}

# -------------------- Logging --------------------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(APP_NAME)

# -------------------- App --------------------
app = FastAPI(title=APP_NAME, version=AGENT_VERSION)

# CORS
origins = ["*"] if CORS_ORIGINS.strip() == "*" else [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Models --------------------
class InvokeInput(BaseModel):
    user_id: str = Field(..., description="End user id")
    input: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)

class ErrorPayload(BaseModel):
    error: str
    request_id: str
    detail: Optional[str] = None

# -------------------- Middleware --------------------
@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    req_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        # ensure we always return JSON on unhandled errors
        log.exception("Unhandled error [%s] %s", req_id, request.url.path)
        payload = ErrorPayload(error="internal_server_error", request_id=req_id, detail=str(e))
        return JSONResponse(status_code=500, content=payload.model_dump())
    dur_ms = int((time.time() - start) * 1000)
    response.headers["x-request-id"] = req_id
    response.headers["x-response-time-ms"] = str(dur_ms)
    log.info("%s %s %s %dms", request.method, request.url.path, req_id, dur_ms)
    return response

# -------------------- Health / Ready --------------------
@app.get("/healthz")
def healthz():
    """Liveness: process is up."""
    return {"status": "ok", "version": AGENT_VERSION, "name": APP_NAME}

@app.get("/readyz")
def readyz():
    """
    Readiness: check minimal dependencies.
    Tighten as needed (e.g., ping model providers, DB, tools).
    """
    problems = []
    if REQUIRE_OPENAI and not os.getenv("OPENAI_API_KEY"):
        problems.append("OPENAI_API_KEY missing")
    status = "ok" if not problems else "degraded"
    return {"status": status, "version": AGENT_VERSION, "problems": problems}

# -------------------- Optional: Manifest echo --------------------
@app.get("/manifest")
def manifest():
    """Return agent.manifest.json if present (useful for hub debugging)."""
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return JSONResponse(json.load(f))
    except FileNotFoundError:
        return JSONResponse({"warning": "manifest not found", "path": MANIFEST_PATH})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"manifest read failed: {e}")

# -------------------- Invoke --------------------
@app.post("/invoke")
def invoke(body: InvokeInput, request: Request):
    t0 = time.time()
    req_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    try:
        out = run_agent(body.user_id, body.input, body.context)
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Invoke error [%s]", req_id)
        raise HTTPException(status_code=500, detail=str(e))
    lat = int((time.time() - t0) * 1000)
    return {"output": out, "metrics": {"latency_ms": lat}, "version": AGENT_VERSION, "request_id": req_id}

# -------------------- Static UI (/ui) --------------------
if os.path.isdir(FRONTEND_DIR):
    log.info("Serving UI from %s at /ui", FRONTEND_DIR)
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")
else:
    log.warning("FRONTEND_DIR not found: %s (build UI or set FRONTEND_DIR)", FRONTEND_DIR)

    @app.get("/ui")
    def ui_missing():
        msg = (
            f"UI build not found at FRONTEND_DIR={FRONTEND_DIR}. "
            "Run your UI build (e.g., `npm run build`) and point FRONTEND_DIR to the built folder."
        )
        return PlainTextResponse(msg, status_code=404)

# -------------------- Root --------------------
@app.get("/")
def root():
    return {
        "name": APP_NAME,
        "version": AGENT_VERSION,
        "ui": "/ui",
        "health": "/healthz",
        "ready": "/readyz",
        "invoke": "/invoke",
        "manifest": "/manifest",
        "ok": True,
    }