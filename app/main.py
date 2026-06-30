from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import JSONResponse

from app.api import auth, project, server ,node ,link
from app.models import User, Device, Project
from app.services.Gns3.server import start_gns3_server, stop_gns3_server
from app.core.exceptions import GNS3UnreachableException, GNS3RequestException




app = FastAPI(
    title="NetCTRL API",
    description="Web-based network device management platform",
    version="0.1.0",
    redoc_url=None,
)

# ── Global exception handlers ──────────────────────────────────────────────

@app.exception_handler(GNS3UnreachableException)
async def gns3_unreachable_handler(request: Request, exc: GNS3UnreachableException):
    return JSONResponse(
        status_code=503,
        content={"success": False, "message": str(exc), "data": None}
    )

@app.exception_handler(GNS3RequestException)
async def gns3_request_handler(request: Request, exc: GNS3RequestException):
    return JSONResponse(
        status_code=502,
        content={"success": False, "message": exc.detail, "data": None}
    )

@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "data": None}
    )

# ── Middleware & routers ───────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(project.router)
app.include_router(server.router)
app.include_router(node.router)
app.include_router(link.router)


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="NetCTRL API Docs",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
    )

@app.get("/")
def root():
    return {"success": True, "message": "NetCTRL API is running", "data": None}