from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
import os
import models, schemas
from database import engine, get_db
from pydantic import BaseModel, Json

# สร้างฐานข้อมูล
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ตั้งค่าความปลอดภัย
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# เก็บข้อมูลผู้ใช้ที่กำลังรอแชท
waiting_users = []
# เก็บข้อมูลห้องแชท
active_chats = {}
# เก็บข้อมูลผู้ใช้ที่ออนไลน์
online_users = {}

# Schemas สำหรับ Profile
class ProfileUpdate(BaseModel):
    displayName: Optional[str] = None
    bio: Optional[str] = None
    interests: List[str] = []

class ProfileStats(BaseModel):
    chatCount: int = 0
    friendCount: int = 0
    activeTime: int = 0

class Profile(BaseModel):
    displayName: Optional[str]
    school: str
    bio: Optional[str]
    interests: List[str] = []
    stats: ProfileStats
    picture_url: Optional[str] = None

# ฟังก์ชันเช็คสถานะออนไลน์
def update_user_status(user_id: int):
    online_users[user_id] = datetime.now()

def is_user_online(user_id: int) -> bool:
    if user_id not in online_users:
        return False
    return datetime.now() - online_users[user_id] < timedelta(minutes=5)

# ฟังก์ชันสร้าง token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ฟังก์ชันตรวจสอบ token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Routes

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Server is running"}

# สมัครสมาชิก
@app.post("/register", response_model=schemas.User)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    print(f"Received registration request: {user.dict()}")

    try:
        db_user = db.query(models.User).filter(models.User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")

        hashed_password = pwd_context.hash(user.password)
        db_user = models.User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            school=user.school
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"User registered successfully: {db_user.username}")
        
        # อัพเดทสถานะออนไลน์เมื่อสมัครสมาชิก
        update_user_status(db_user.id)
        return db_user

    except Exception as e:
        print(f"Error during registration: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ล็อกอิน
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    update_user_status(user.id)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Profile Routes
@app.get("/profile", response_model=Profile)
async def get_profile(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    
    if not profile:
        profile = models.UserProfile(
            user_id=current_user.id,
            display_name=current_user.username,
            interests=[]
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return {
        "displayName": profile.display_name,
        "school": current_user.school,
        "bio": profile.bio,
        "interests": profile.interests,
        "stats": {
            "chatCount": profile.chat_count,
            "friendCount": profile.friend_count,
            "activeTime": profile.active_time
        },
        "picture_url": profile.picture_url
    }

@app.post("/profile/update")
async def update_profile(
    profile_update: ProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    
    if not profile:
        profile = models.UserProfile(user_id=current_user.id)
        db.add(profile)
    
    if profile_update.displayName is not None:
        profile.display_name = profile_update.displayName
    if profile_update.bio is not None:
        profile.bio = profile_update.bio
    profile.interests = profile_update.interests

    db.commit()
    return {"status": "success"}

@app.post("/profile/picture")
async def update_profile_picture(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        filename = f"user_{current_user.id}_{int(datetime.now().timestamp())}{os.path.splitext(file.filename)[1]}"
        
        UPLOAD_DIR = "static/uploads"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb+") as file_object:
            file_object.write(file.file.read())
        
        profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
        if not profile:
            profile = models.UserProfile(user_id=current_user.id)
            db.add(profile)
        
        profile.picture_url = f"/static/uploads/{filename}"
        db.commit()

        return {"url": profile.picture_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat Routes
@app.post("/start-chat")
async def start_chat(school: str, current_user: models.User = Depends(get_current_user)):
    update_user_status(current_user.id)

    for chat_id, chat in active_chats.items():
        if current_user.id in [chat['user1'].id, chat['user2'].id]:
            raise HTTPException(status_code=400, detail="You are already in a chat")

    waiting_users[:] = [u for u in waiting_users if u['user'].id != current_user.id]

    for waiting_user in waiting_users:
        if (waiting_user['school'] == school and 
            waiting_user['user'].id != current_user.id and 
            is_user_online(waiting_user['user'].id)):
            
            chat_id = f"{current_user.id}-{waiting_user['user'].id}"
            active_chats[chat_id] = {
                'user1': current_user,
                'user2': waiting_user['user'],
                'school': school,
                'messages': [],
                'started_at': datetime.now()
            }
            waiting_users.remove(waiting_user)
            return {
                "status": "matched",
                "chat_id": chat_id,
                "partner": {
                    "username": waiting_user['user'].username,
                    "school": school,
                    "online": True
                }
            }

    waiting_users.append({
        'user': current_user,
        'school': school
    })
    return {"status": "waiting"}

@app.post("/send-message/{chat_id}")
async def send_message(
    chat_id: str,
    message: str,
    current_user: models.User = Depends(get_current_user)
):
    update_user_status(current_user.id)

    if chat_id not in active_chats:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat = active_chats[chat_id]
    if current_user.id not in [chat['user1'].id, chat['user2'].id]:
        raise HTTPException(status_code=403, detail="You are not in this chat")

    partner = chat['user2'] if current_user.id == chat['user1'].id else chat['user1']
    if not is_user_online(partner.id):
        raise HTTPException(status_code=400, detail="Partner is offline")

    new_message = {
        'content': message,
        'sender_id': current_user.id,
        'sender_username': current_user.username,
        'timestamp': datetime.now().isoformat()
    }
    chat['messages'].append(new_message)

    return {
        "status": "sent",
        "message": new_message
    }

@app.get("/chat-messages/{chat_id}")
async def get_messages(
    chat_id: str,
    current_user: models.User = Depends(get_current_user)
):
    update_user_status(current_user.id)

    if chat_id not in active_chats:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat = active_chats[chat_id]
    if current_user.id not in [chat['user1'].id, chat['user2'].id]:
        raise HTTPException(status_code=403, detail="You are not in this chat")

    partner = chat['user2'] if current_user.id == chat['user1'].id else chat['user1']
    partner_online = is_user_online(partner.id)

    return {
        "messages": chat['messages'],
        "partner": {
            "username": partner.username,
            "school": chat['school'],
            "online": partner_online
        }
    }

@app.post("/leave-chat/{chat_id}")
async def leave_chat(
    chat_id: str,
    current_user: models.User = Depends(get_current_user)
):
    if chat_id not in active_chats:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat = active_chats[chat_id]
    if current_user.id not in [chat['user1'].id, chat['user2'].id]:
        raise HTTPException(status_code=403, detail="You are not in this chat")

    del active_chats[chat_id]
    return {"status": "left"}

@app.get("/waiting-status")
async def get_waiting_status(current_user: models.User = Depends(get_current_user)):
    update_user_status(current_user.id)

    for user in waiting_users:
        if user['user'].id == current_user.id:
            return {"status": "waiting", "school": user['school']}
    
    for chat_id, chat in active_chats.items():
        if current_user.id in [chat['user1'].id, chat['user2'].id]:
            partner = chat['user2'] if current_user.id == chat['user1'].id else chat['user1']
            return {
                "status": "in_chat",
                "chat_id": chat_id,
                "partner": {
                    "username": partner.username,
                    "school": chat['school'],
                    "online": is_user_online(partner.id)
                }
            }
    
    return {"status": "not_waiting"}

# Online Status Routes
@app.post("/update-status")
async def update_online_status(current_user: models.User = Depends(get_current_user)):
    update_user_status(current_user.id)
    return {"status": "updated"}

@app.get("/online-users/{school}")
async def get_online_users(
    school: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    online_count = 0
    users = db.query(models.User).filter(models.User.school == school).all()
    for user in users:
        if is_user_online(user.id):
            online_count += 1

    return {
        "school": school,
        "online_users": online_count
    }

# Report Routes
@app.post("/report-user/{reported_username}")
async def report_user(
    reported_username: str,
    reason: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reported_user = db.query(models.User).filter(models.User.username == reported_username).first()
    if not reported_user:
        raise HTTPException(status_code=404, detail="User not found")

    report = models.Report(
        reporter_id=current_user.id,
        reported_id=reported_user.id,
        reason=reason,
        created_at=datetime.now()
    )
    db.add(report)
    db.commit()

    return {"status": "reported"}

# Profile Stats Update Route
@app.post("/profile/stats/update")
async def update_stats(
    chatCount: Optional[int] = None,
    activeTime: Optional[int] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    
    if not profile:
        profile = models.UserProfile(user_id=current_user.id)
        db.add(profile)
    
    if chatCount is not None:
        profile.chat_count = chatCount
    if activeTime is not None:
        profile.active_time = activeTime
    
    db.commit()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)