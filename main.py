from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, chat, profile, system
from firebase_config import db  # เปลี่ยนเป็น import firebase
from logging_config import logger

# Initialize FastAPI
app = FastAPI(
    title="School Chat API",
    description="API for school chat application",
    version="1.0.0"
    # ลบ root_path="/api"
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

# Startup Event
@app.on_event("startup")
async def startup_event():
    """Check database connection on startup"""
    try:
        # เช็คการเชื่อมต่อ Firebase
        db.collection('test').document('test').set({
            'test': 'Connection successful'
        })
        logger.info("Firebase connection successful")
    except Exception as e:
        logger.error(f"Firebase connection failed: {e}")
        raise

# Include routers with prefix
app.include_router(
    auth.router,
    prefix="/api",
    tags=["Authentication"]
)
app.include_router(
    chat.router,
    prefix="/api/chat",
    tags=["Chat"]
)
app.include_router(
    profile.router,
    prefix="/api/profile",
    tags=["Profile"]
)
app.include_router(
    system.router,
    prefix="/api/system",
    tags=["System"]
)

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
        reload=True
    )