"""
Main FastAPI Application
Adaptive Learning System for Moroccan High School Students
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

load_dotenv()

# Import routes
from backend.routes.auth import router as auth_router
from backend.routes.diagnostic import router as diagnostic_router
from backend.routes.exercise import router as exercise_router
from backend.routes.analytics import router as analytics_router
from backend.routes.curriculum import router as curriculum_router
from backend.routes.admin import router as admin_router
from backend.routes.ai import router as ai_router

# Initialize database
from backend.database.db import init_db, insert_default_concepts

app = FastAPI(
    title="Adaptive Learning System",
    description="AI-powered learning platform for Moroccan high school students",
    version="1.0.0"
)

# CORS middleware
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    init_db()
    insert_default_concepts()
    print("✅ Database initialized")

# Include routers
app.include_router(auth_router)
app.include_router(curriculum_router)
app.include_router(diagnostic_router)
app.include_router(exercise_router)
app.include_router(analytics_router)
app.include_router(admin_router)
app.include_router(ai_router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/api/version")
async def get_version():
    """Get API version"""
    return {"version": "1.0.0"}

# Serve frontend static files (optional)
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    try:
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    except Exception as e:
        print(f"Note: Frontend directory not found for static mounting: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
