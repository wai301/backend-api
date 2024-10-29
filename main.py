# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
import os
import random  # เพิ่ม import random
import models, schemas
from database import engine, get_db

# สร้างฐานข้อมูล
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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

# ฟังก์ชันเช็คสถานะออนไลน์
def update_user_status(user_id: int):
    online_users[user_id] = datetime.now()
    print(f"Updated online status for user {user_id}")  # เพิ่ม log

def is_user_online(user_id: int) -> bool:
    if user_id not in online_users:
        return False
    is_online = datetime.now() - online_users[user_id] < timedelta(minutes=5)
    print(f"User {user_id} online status: {is_online}")  # เพิ่ม log
    return is_online

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
    print(f"User logged in: {user.username}")  # เพิ่ม log

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Profile Routes
@app.get("/profile", response_model=schemas.Profile)
async def get_profile(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "school": current_user.school
    }

@app.post("/profile/update")
async def update_profile(
    profile_update: schemas.ProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if profile_update.email:
            existing_user = db.query(models.User).filter(
                models.User.email == profile_update.email,
                models.User.id != current_user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="อีเมลนี้ถูกใช้งานแล้ว"
                )
            current_user.email = profile_update.email
            
        if profile_update.school:
            current_user.school = profile_update.school
            
        db.commit()
        db.refresh(current_user)
        
        return {
            "status": "success",
            "message": "อัพเดทข้อมูลสำเร็จ",
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "school": current_user.school
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

# Chat Routes
@app.post("/start-chat")
async def start_chat(school: str, current_user: models.User = Depends(get_current_user)):
    print(f"Starting chat for {current_user.username} from {school}")  # เพิ่ม log
    update_user_status(current_user.id)

    # เช็คว่าผู้ใช้ไม่ได้อยู่ในแชทอื่น
    for chat_id, chat in active_chats.items():
        if current_user.id in [chat['user1'].id, chat['user2'].id]:
            raise HTTPException(status_code=400, detail="You are already in a chat")

    # ลบตัวเองจาก waiting list ถ้ามี
    waiting_users[:] = [u for u in waiting_users if u['user'].id != current_user.id]

    # หาคู่สนทนาที่อยู่โรงเรียนเดียวกัน
    available_users = []
    for waiting_user in waiting_users:
        if (waiting_user['school'] == school and 
            waiting_user['user'].id != current_user.id and 
            is_user_online(waiting_user['user'].id)):
            available_users.append(waiting_user)

    print(f"Available users for {school}: {[u['user'].username for u in available_users]}")

    if available_users:
        # สุ่มเลือกคนที่จะคุยด้วย
        waiting_user = random.choice(available_users)
        chat_id = f"{current_user.id}-{waiting_user['user'].id}"
        
        print(f"Matched: {current_user.username} with {waiting_user['user'].username}")
        
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

    # ถ้ายังไม่มีคน ให้เข้าคิวรอ
    print(f"No match found, {current_user.username} waiting")
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

    print(f"Message sent in chat {chat_id}: {message}")
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

    print(f"User {current_user.username} left chat {chat_id}")
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

# Debug Routes
@app.get("/debug/waiting-users")
async def get_waiting_users_debug(current_user: models.User = Depends(get_current_user)):
    return {
        "waiting_users": [
            {
                "username": u['user'].username,
                "school": u['school'],
                "online": is_user_online(u['user'].id)
            }
            for u in waiting_users
        ],
        "active_chats": [
            {
                "chat_id": chat_id,
                "users": [chat['user1'].username, chat['user2'].username],
                "school": chat['school']
            }
            for chat_id, chat in active_chats.items()
        ]
    }

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

# System Status Routes
@app.get("/system-status")
async def get_system_status(current_user: models.User = Depends(get_current_user)):
    return {
        "waiting_users_count": len(waiting_users),
        "active_chats_count": len(active_chats),
        "online_users_count": len(online_users),
        "current_time": datetime.now().isoformat()
    }

# Reset Routes (Debug Only)
@app.post("/debug/reset-chat")
async def reset_chat(current_user: models.User = Depends(get_current_user)):
    waiting_users.clear()
    active_chats.clear()
    return {"status": "reset_complete"}

# Error Handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "status": "error",
        "message": exc.detail,
        "status_code": exc.status_code
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)