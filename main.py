from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
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
SECRET_KEY = "your-secret-key"
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

def is_user_online(user_id: int) -> bool:
    if user_id not in online_users:
        return False
    # ถ้าไม่มีการอัพเดทสถานะเกิน 5 นาที ถือว่าออฟไลน์
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

# หน้าแรก
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

    # อัพเดทสถานะออนไลน์เมื่อล็อกอิน
    update_user_status(user.id)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# อัพเดทสถานะออนไลน์
@app.post("/update-status")
async def update_online_status(current_user: models.User = Depends(get_current_user)):
    update_user_status(current_user.id)
    return {"status": "updated"}

# ดูจำนวนคนออนไลน์
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

# เริ่มแชท
@app.post("/start-chat")
async def start_chat(school: str, current_user: models.User = Depends(get_current_user)):
    # อัพเดทสถานะออนไลน์
    update_user_status(current_user.id)

    # เช็คว่าผู้ใช้อยู่ในการแชทอื่นหรือไม่
    for chat_id, chat in active_chats.items():
        if current_user.id in [chat['user1'].id, chat['user2'].id]:
            raise HTTPException(status_code=400, detail="You are already in a chat")

    # ลบผู้ใช้จาก waiting list ถ้ามี
    waiting_users[:] = [u for u in waiting_users if u['user'].id != current_user.id]

    # หาคู่สนทนาที่ออนไลน์
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

    # ถ้าไม่เจอคู่สนทนาที่ออนไลน์
    waiting_users.append({
        'user': current_user,
        'school': school
    })
    return {"status": "waiting"}

# ส่งข้อความ
@app.post("/send-message/{chat_id}")
async def send_message(
    chat_id: str,
    message: str,
    current_user: models.User = Depends(get_current_user)
):
    # อัพเดทสถานะออนไลน์
    update_user_status(current_user.id)

    if chat_id not in active_chats:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat = active_chats[chat_id]
    if current_user.id not in [chat['user1'].id, chat['user2'].id]:
        raise HTTPException(status_code=403, detail="You are not in this chat")

    # เช็คว่าคู่สนทนายังออนไลน์อยู่ไหม
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

# ดูข้อความในแชท
@app.get("/chat-messages/{chat_id}")
async def get_messages(
    chat_id: str,
    current_user: models.User = Depends(get_current_user)
):
    # อัพเดทสถานะออนไลน์
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

# ออกจากแชท
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

# เช็คสถานะการรอ
@app.get("/waiting-status")
async def get_waiting_status(current_user: models.User = Depends(get_current_user)):
    # อัพเดทสถานะออนไลน์
    update_user_status(current_user.id)

    for user in waiting_users:
        if user['user'].id == current_user.id:
            return {"status": "waiting", "school": user['school']}
    
    # เช็คว่าอยู่ในแชทไหม
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

# รายงานผู้ใช้
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

    # บันทึกการรายงาน
    report = models.Report(
        reporter_id=current_user.id,
        reported_id=reported_user.id,
        reason=reason,
        created_at=datetime.now()
    )
    db.add(report)
    db.commit()

    return {"status": "reported"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)