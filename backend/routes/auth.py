"""
Authentication routes
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from backend.models.database_models import StudentCreate, StudentLogin, StudentResponse
from backend.utils.auth import hash_password, verify_password, TokenStore
from backend.database.db import get_db_connection
import sqlite3

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=StudentResponse)
async def register(student: StudentCreate):
    """Register a new student"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if student exists
    cursor.execute("SELECT id FROM students WHERE username = ? OR email = ?", 
                   (student.username, student.email))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Student already exists")
    
    # Hash password and create student
    password_hash = hash_password(student.password)
    
    try:
        cursor.execute("""
            INSERT INTO students (username, email, password_hash)
            VALUES (?, ?, ?)
        """, (student.username, student.email, password_hash))
        conn.commit()
        
        student_id = cursor.lastrowid
    except sqlite3.IntegrityError as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    
    return {
        "id": student_id,
        "username": student.username,
        "email": student.email,
        "created_at": ""
    }

@router.post("/login")
async def login(credentials: StudentLogin):
    """Login a student"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, password_hash FROM students WHERE username = ?", 
                   (credentials.username,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    student_id, password_hash = result
    
    if not verify_password(credentials.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token = TokenStore.create_token(student_id)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "student_id": student_id
    }

@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout a student"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")
    
    token = authorization.replace("Bearer ", "")
    TokenStore.invalidate_token(token)
    
    return {"message": "Logged out successfully"}

def get_current_student(authorization: Optional[str] = Header(None)) -> int:
    """Dependency to get current student from token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = authorization.replace("Bearer ", "")
    student_id = TokenStore.verify_token(token)
    
    if not student_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return student_id
