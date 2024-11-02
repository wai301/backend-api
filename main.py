from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, chat, profile, system
from database import engine
import models
from logging_config import logger

# Create tables
models.Base.metadata.create_all(bind=engine)

# เพิ่ม root_path="/api"
app = FastAPI(
    title="School Chat API",
    description="API for school chat application",
    version="1.0.0",
    root_path="/api"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://matchfortalk.web.app",
        "https://matchfortalk.firebaseapp.com",
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])
app.include_router(system.router, prefix="/system", tags=["System"])

@app.get("/")
def read_root():
    return {
        "status": "ok", 
        "message": "School Chat API Server is running",
        "version": "1.0.0",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        reload=True  # ใช้สำหรับ development
    )