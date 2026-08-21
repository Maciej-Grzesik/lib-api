import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.books.views import router as books_router
from app.core import lifespan
from app.core.config import get_settings
from app.probe.views import router as probe_router

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Library API",
    version="0.1.0",
    description="Library API",
    openapi_url="/openapi.json",
    docs_url="/",
    lifespan=lifespan.lifespan,
)

app.include_router(books_router, prefix="/books", tags=["books"])
app.include_router(probe_router, prefix="/probe", tags=["probe"])

# Guards against HTTP Host Header attacks
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=get_settings().http.allowed_hosts,
)

# Sets all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=[
        str(origin).rstrip("/") for origin in get_settings().http.backend_cors_origins
    ],
)
