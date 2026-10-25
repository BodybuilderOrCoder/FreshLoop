import os

from app.routers.products import router as products_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="FreshLoop API",
    description="Backend API for the FreshLoop grocery e-commerce platform.",
    version="1.0.0",
)

# Configure allowed frontend origins through the environment.
# For local development, allow the common Vite and Next.js origins.
_default_origins = (
    "http://localhost:3000,"
    "http://127.0.0.1:3000,"
    "http://localhost:5173,"
    "http://127.0.0.1:5173"
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        _default_origins,
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(products_router)

@app.get("/health", tags=["Health"])
def health_check():
    """Return the basic application health status."""
    return {
        "status": "ok",
        "service": "FreshLoop API",
    }
