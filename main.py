import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from passlib.context import CryptContext
from database import db, create_document, get_documents
from schemas import User, RequestItem, Location
from bson.objectid import ObjectId

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SignupPayload(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginPayload(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    photo_url: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "Backend is running"}

@app.get("/schema")
def schema_info():
    return {"collections": ["user", "requestitem"]}

@app.post("/auth/signup")
def signup(payload: SignupPayload):
    # check if user exists
    existing = db["user"].find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = pwd_context.hash(payload.password)
    user = User(name=payload.name, email=payload.email, password_hash=hashed, photo_url=None)
    user_id = create_document("user", user)
    return {"id": user_id, "email": payload.email, "name": payload.name}

@app.post("/auth/login")
def login(payload: LoginPayload):
    user = db["user"].find_one({"email": payload.email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not pwd_context.verify(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"id": str(user["_id"]), "email": user["email"], "name": user.get("name")}

@app.get("/profile/{user_id}")
def get_profile(user_id: str):
    try:
        user = db["user"].find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(user["_id"]), "email": user["email"], "name": user.get("name"), "photo_url": user.get("photo_url")}

@app.put("/profile/{user_id}")
def update_profile(user_id: str, payload: ProfileUpdate):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update:
        return {"updated": False}
    db["user"].update_one({"_id": oid}, {"$set": update})
    user = db["user"].find_one({"_id": oid})
    return {"id": str(user["_id"]), "email": user["email"], "name": user.get("name"), "photo_url": user.get("photo_url")}

@app.post("/request/text")
def send_text(user_id: str, text: str):
    item = RequestItem(user_id=user_id, type="text", text=text)
    req_id = create_document("requestitem", item)
    return {"id": req_id, "status": "ok"}

@app.post("/request/contact")
def send_contact(user_id: str, contact_name: str, contact_phone: str):
    item = RequestItem(user_id=user_id, type="contact", contact_name=contact_name, contact_phone=contact_phone)
    req_id = create_document("requestitem", item)
    return {"id": req_id, "status": "ok"}

@app.post("/request/location")
def send_location(user_id: str, lat: float, lng: float):
    loc = Location(lat=lat, lng=lng)
    item = RequestItem(user_id=user_id, type="location", location=loc)
    req_id = create_document("requestitem", item)
    return {"id": req_id, "status": "ok"}

@app.post("/request/photo")
async def send_photo(user_id: str = Form(...), file: UploadFile = File(...)):
    # In a real app, upload to storage (S3, etc.). Here we just store filename.
    content = await file.read()
    # Not storing binary; just simulate a URL/path
    photo_url = f"/uploads/{file.filename}"
    item = RequestItem(user_id=user_id, type="photo", photo_url=photo_url, meta={"size": len(content)})
    req_id = create_document("requestitem", item)
    return {"id": req_id, "status": "ok", "photo_url": photo_url}

@app.post("/request/voice")
async def send_voice(user_id: str = Form(...), file: UploadFile = File(...)):
    content = await file.read()
    voice_url = f"/uploads/{file.filename}"
    item = RequestItem(user_id=user_id, type="voice", voice_url=voice_url, meta={"size": len(content)})
    req_id = create_document("requestitem", item)
    return {"id": req_id, "status": "ok", "voice_url": voice_url}

@app.get("/requests/{user_id}")
def list_requests(user_id: str):
    docs = get_documents("requestitem", {"user_id": user_id}, limit=100)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            collections = db.list_collection_names()
            response["collections"] = collections[:10]
            response["database"] = "✅ Connected & Working"
            response["connection_status"] = "Connected"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
