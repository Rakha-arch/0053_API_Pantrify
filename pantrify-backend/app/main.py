import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
import mysql.connector
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

load_dotenv()
app = FastAPI(title="Pantrify API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
JWT_SECRET = os.getenv("JWT_SECRET", "pantrify-development-secret")

class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class CategoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None

def connection():
    return mysql.connector.connect(host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT", "3306")), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), database=os.getenv("DB_NAME"))

def token_for(user: dict) -> str:
    payload = {"id": user["id"], "email": user["email"], "role": user["role"], "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token diperlukan")
    try:
        return jwt.decode(authorization[7:], JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid atau sudah kedaluwarsa")

def query(sql, params=(), fetch=False):
    conn = connection(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        result = cursor.fetchall() if fetch else cursor.lastrowid
        conn.commit(); return result
    finally:
        cursor.close(); conn.close()

@app.get("/")
@app.get("/api/")
@app.get("/api/health")
def health():
    try: query("SELECT 1")
    except mysql.connector.Error:
        raise HTTPException(status_code=503, detail="Gagal terhubung ke database")
    return {"status": "success", "message": "Pantrify REST API & MySQL Database berjalan normal!"}

@app.post("/api/auth/register", status_code=201)
def register(body: RegisterRequest):
    if query("SELECT id FROM users WHERE email = %s", (body.email,), True):
        raise HTTPException(status_code=409, detail="Email sudah terdaftar")
    hashed = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    user = {"id": query("INSERT INTO users (name,email,password_hash,role) VALUES (%s,%s,%s,%s)", (body.name, body.email, hashed, "user")), "name": body.name, "email": body.email, "role": "user"}
    return {"status": "success", "data": {"user": user, "token": token_for(user)}}

@app.post("/api/auth/login")
def login(body: LoginRequest):
    rows = query("SELECT id,name,email,password_hash,role FROM users WHERE email=%s", (body.email,), True)
    if not rows or not bcrypt.checkpw(body.password.encode(), rows[0]["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Email atau password salah")
    row = rows[0]; user = {k: row[k] for k in ("id", "name", "email", "role")}
    return {"status": "success", "data": {"user": user, "token": token_for(user)}}

@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    rows = query("SELECT id,name,email,role,created_at FROM users WHERE id=%s", (user["id"],), True)
    if not rows: raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return {"status": "success", "data": rows[0]}

@app.get("/api/categories")
def categories(user=Depends(current_user)):
    return {"status": "success", "data": query("SELECT id,name,description,created_at FROM categories ORDER BY name", fetch=True)}

@app.post("/api/categories", status_code=201)
def create_category(body: CategoryRequest, user=Depends(current_user)):
    category_id = query("INSERT INTO categories (name,description) VALUES (%s,%s)", (body.name.strip(), body.description))
    return {"status": "success", "data": {"id": category_id, "name": body.name.strip(), "description": body.description}}

@app.delete("/api/categories/{category_id}", status_code=204)
def delete_category(category_id: int, user=Depends(current_user)):
    rows = query("SELECT id FROM categories WHERE id=%s", (category_id,), True)
    if not rows: raise HTTPException(status_code=404, detail="Kategori tidak ditemukan")
    query("DELETE FROM categories WHERE id=%s", (category_id,))
