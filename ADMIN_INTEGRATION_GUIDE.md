# 🏗️ ADMIN INTERFACE INTEGRATION GUIDE

## Overview

This guide walks through the complete extension of AdaptiveLearn with role-based access control (RBAC) and a comprehensive admin interface. The system maintains **100% backward compatibility** with existing student functionality.

---

## 📋 TABLE OF CONTENTS

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Database Migration](#database-migration)
4. [Authentication & RBAC](#authentication--rbac)
5. [Admin Capabilities](#admin-capabilities)
6. [Exercise Types & JSON Schema](#exercise-types--json-schema)
7. [Recommendation Engine](#recommendation-engine-updates)
8. [Admin Frontend Usage](#admin-frontend-usage)
9. [Testing Guide](#testing-guide)
10. [Troubleshooting](#troubleshooting)

---

## 🚀 QUICK START

### Step 1: Apply Database Migration

```bash
# In your database tool (DB Browser, etc.), run this SQL:
# File: data/admin_migration.sql

# Or from Python:
python -c "
import sqlite3
with open('data/admin_migration.sql', 'r') as f:
    conn = sqlite3.connect('data/adaptive_learning.db')
    conn.executescript(f.read())
    conn.commit()
    print('✅ Migration complete')
"
```

### Step 2: Create First Admin Account

```bash
# Via Python REPL or script:
import sqlite3
import hashlib

conn = sqlite3.connect('data/adaptive_learning.db')
cursor = conn.cursor()

username = "admin"
email = "admin@adaptivelearn.com"
password = "AdminPassword123"

password_hash = hashlib.sha256(password.encode()).hexdigest()

cursor.execute("""
    UPDATE students SET role = 'admin' WHERE username = ?
""", (username,))

# Or create new admin:
cursor.execute("""
    INSERT INTO students (username, email, password_hash, role, is_active)
    VALUES (?, ?, ?, 'admin', 1)
""", (username, email, password_hash))

conn.commit()
conn.close()

print(f"✅ Admin created: {username}")
```

### Step 3: Start Server

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 4: Access Admin Dashboard

Open browser: `http://localhost:8000/admin.html`

Login with admin credentials created in Step 2.

---

## 🏛️ ARCHITECTURE OVERVIEW

### New Components Added

```
backend/
├── routes/
│   └── admin.py .......................... NEW: All admin endpoints
├── models/
│   └── admin_models.py ................... NEW: Pydantic models for admin
├── utils/
│   └── rbac.py ........................... NEW: Role-based access control
└── services/
    └── recommendation_extended.py ........ NEW: Error-aware recommendations

frontend/
├── admin.html ............................ NEW: Admin dashboard UI
└── js/
    ├── admin-api.js ...................... NEW: Admin API client
    └── admin-app.js ...................... NEW: Admin dashboard logic
└── css/
    └── admin-style.css ................... NEW: Admin styling

data/
└── admin_migration.sql ................... NEW: Database schema extension
```

### Database Changes

```
Modified tables:
- students (added: role, is_active)
- exercises (added: exercise_type, is_diagnostic, error_type_targeted, content_json, created_by_admin_id, is_active)
- diagnostic_attempts (added: error_types_detected, classification)

New tables:
- admin_logs
- exercise_templates
- admin_settings
```

---

## 🗄️ DATABASE MIGRATION

### What's New

1. **Role System**
   - `students.role`: 'student' or 'admin'
   - `students.is_active`: Active/inactive status

2. **Exercise Management**
   - `exercises.exercise_type`: MCQ, Short Answer, Long Answer, True/False, Drag&Drop, Match Lines
   - `exercises.content_json`: Flexible JSON for exercise content
   - `exercises.error_type_targeted`: Target specific error types
   - `exercises.is_diagnostic`: Mark as diagnostic test
   - `exercises.created_by_admin_id`: Track creator

3. **Audit Trail**
   - `admin_logs`: Complete action history
   - Tracks all CRUD operations with timestamps

### Migration Verification

```python
# Verify migration worked:
import sqlite3

conn = sqlite3.connect('data/adaptive_learning.db')
cursor = conn.cursor()

# Check students table has new columns
cursor.execute("PRAGMA table_info(students)")
columns = {row[1] for row in cursor.fetchall()}
assert 'role' in columns, "Missing 'role' column"
assert 'is_active' in columns, "Missing 'is_active' column"

# Check exercises table
cursor.execute("PRAGMA table_info(exercises)")
columns = {row[1] for row in cursor.fetchall()}
assert 'exercise_type' in columns, "Missing 'exercise_type' column"
assert 'content_json' in columns, "Missing 'content_json' column"

# Check new tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = {row[0] for row in cursor.fetchall()}
assert 'admin_logs' in tables, "Missing 'admin_logs' table"

conn.close()
print("✅ All database changes verified!")
```

---

## 🔐 AUTHENTICATION & RBAC

### JWT Token Payload

The JWT token now includes role:

```json
{
  "sub": "username",
  "student_id": 1,
  "role": "admin",
  "iat": 1234567890,
  "exp": 1234571490
}
```

### Role-Based Access

All admin routes require the `require_admin()` dependency:

```python
from backend.utils.rbac import require_admin

@router.post("/admin/students")
async def create_student(
    data: AdminStudentCreate,
    admin_id: int = Depends(require_admin)  # ← Enforces admin role
):
    # ... only admins can access
    pass
```

### Checking Roles in Frontend

```javascript
// Check if current user is admin
const token = localStorage.getItem('token');
const payload = JSON.parse(atob(token.split('.')[1]));

if (payload.role === 'admin') {
    // Show admin dashboard
} else {
    // Show student dashboard
}
```

---

## 👥 ADMIN CAPABILITIES

### 1. Student Management

**Endpoints:**

```
POST   /admin/students                    # Create student
GET    /admin/students                    # List all students
GET    /admin/students/{student_id}      # Get student details
PUT    /admin/students/{student_id}      # Update student
POST   /admin/students/{student_id}/reset-password  # Reset password
DELETE /admin/students/{student_id}      # Deactivate student
```

**Example:**

```bash
# Create student
curl -X POST http://localhost:8000/admin/students \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student1",
    "email": "student1@example.com",
    "password": "SecurePass123",
    "role": "student"
  }'
```

### 2. Exercise Management

**Endpoints:**

```
POST   /admin/exercises                   # Create exercise
GET    /admin/exercises                   # List exercises (with filters)
GET    /admin/exercises/{exercise_id}     # Get exercise details
PUT    /admin/exercises/{exercise_id}     # Update exercise
POST   /admin/exercises/{exercise_id}/activate     # Activate
POST   /admin/exercises/{exercise_id}/deactivate   # Deactivate
```

**Exercise Types Supported:**

- `mcq` - Multiple Choice Question
- `short_answer` - Short text answer
- `long_answer` - Long essay/answer
- `true_false` - True/False statement
- `drag_drop` - Drag & drop ordering
- `match_lines` - Match two lists

### 3. Analytics & Logs

**Endpoints:**

```
GET    /admin/dashboard                   # Dashboard overview
GET    /admin/analytics                   # Detailed analytics
GET    /admin/logs                        # Admin action logs
```

---

## 📝 EXERCISE TYPES & JSON SCHEMA

Each exercise type stores content in a JSON schema:

### MCQ (Multiple Choice)

```json
{
  "question": "What is 2+2?",
  "options": ["3", "4", "5"],
  "correct_option": 1,
  "explanation": "2+2 equals 4"
}
```

### Short Answer

```json
{
  "question": "What is the capital of France?",
  "correct_answer": "Paris",
  "alternative_answers": ["paris", "PARIS"],
  "explanation": "France's capital is Paris"
}
```

### Long Answer

```json
{
  "question": "Explain the OSI model",
  "expected_keywords": ["layers", "protocol", "application", "physical"],
  "rubric": "Look for understanding of 7 layers...",
  "explanation": "The OSI model has 7 layers..."
}
```

### True/False

```json
{
  "statement": "The Earth is flat",
  "correct_answer": false,
  "explanation": "The Earth is a sphere..."
}
```

### Drag & Drop

```json
{
  "question": "Order the steps of the algorithm",
  "items": ["Initialize", "Process", "Output", "End"],
  "correct_order": [0, 1, 2, 3],
  "explanation": "This is the correct order..."
}
```

### Match Lines

```json
{
  "question": "Match concepts to definitions",
  "left_items": ["Variable", "Function", "Loop"],
  "right_items": ["Repeated execution", "Reusable code block", "Data container"],
  "correct_pairs": [[0, 2], [1, 1], [2, 0]],
  "explanation": "Correct mappings are..."
}
```

---

## 🧠 RECOMMENDATION ENGINE UPDATES

### Error-Type Targeting

The recommendation engine now routes students to targeted exercises based on diagnostic error classification:

```python
from backend.services.recommendation_extended import RecommendationEngine

engine = RecommendationEngine(db_connection)

# After diagnostic test with error classification
errors = ["conceptual", "procedural"]  # Detected errors
recommendation = engine.get_next_recommendation(
    student_id=1,
    diagnostic_errors=errors
)

# Returns:
# {
#   "action": "error_targeted_exercise",
#   "concept_id": 5,
#   "concept_name": "Loops",
#   "target_error_type": "conceptual",
#   "priority": "high",
#   "exercise_source": "admin",  # Prioritizes admin exercises
#   "reason": "You showed conceptual misunderstandings..."
# }
```

### Exercise Prioritization

```python
# Get exercises for a student, prioritizing error-type targeted ones
exercises = engine.get_targeted_exercises(
    student_id=1,
    concept_id=5,
    error_type="conceptual",
    limit=5
)

# Returns exercises in this order:
# 1. Admin-created exercises targeted for "conceptual" errors
# 2. AI-generated exercises targeted for "conceptual" errors
# 3. Admin exercises (general)
# 4. AI exercises (general)
```

---

## 🖥️ ADMIN FRONTEND USAGE

### Dashboard Features

1. **Dashboard Tab**
   - System statistics
   - Student mastery distribution
   - Recent admin actions

2. **Students Tab**
   - List all students
   - Create new student
   - View detailed progress
   - Reset password
   - Deactivate account

3. **Exercises Tab**
   - List all exercises
   - Create exercise by type
   - Filter by difficulty/type
   - Activate/deactivate exercises
   - View exercise statistics

4. **Analytics Tab**
   - System-wide metrics
   - Weakest concepts
   - Most common errors
   - Diagnostic completion rate

5. **Logs Tab**
   - Complete audit trail
   - Filter by action type
   - Search logs

### Creating an Exercise (Step-by-Step)

1. Click "Exercises" tab
2. Click "+ Create Exercise"
3. Fill in basic info:
   - Title
   - Difficulty level
   - Exercise type
   - Target concept
   - Error type (optional)
4. Dynamic fields appear based on exercise type
5. Click "Create Exercise"

Example: Creating an MCQ
```
Title: "What is an algorithm?"
Difficulty: medium
Type: mcq (Multiple Choice)
Concept: "Algorithms - Definition"
Error Type: conceptual
```
Fields shown:
- Question: "What is an algorithm?"
- Options: "Step-by-step procedure, Math formula, Programming language"
- Correct option: 0

---

## ✅ TESTING GUIDE

### 1. Test RBAC

```python
import requests

# Test 1: Student cannot access admin routes
student_token = "student_token_here"
response = requests.get(
    "http://localhost:8000/admin/students",
    headers={"Authorization": f"Bearer {student_token}"}
)
assert response.status_code == 403, "Should be forbidden for students"

# Test 2: Admin can access
admin_token = "admin_token_here"
response = requests.get(
    "http://localhost:8000/admin/students",
    headers={"Authorization": f"Bearer {admin_token}"}
)
assert response.status_code == 200, "Should be allowed for admins"
```

### 2. Test Student Creation

```python
import requests

admin_token = "admin_token_here"

response = requests.post(
    "http://localhost:8000/admin/students",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test123!",
        "role": "student"
    }
)

assert response.status_code == 200
new_student = response.json()
print(f"✅ Created student: {new_student['id']}")
```

### 3. Test Exercise Creation

```python
import requests
import json

admin_token = "admin_token_here"

content_json = {
    "question": "What is Python?",
    "options": ["A snake", "A programming language", "A type of food"],
    "correct_option": 1
}

response = requests.post(
    "http://localhost:8000/admin/exercises",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={
        "title": "Python Basics",
        "description": "Test exercise",
        "module_id": 1,
        "sequence_id": 1,
        "concept_id": 1,
        "difficulty": "easy",
        "exercise_type": "mcq",
        "is_diagnostic": False,
        "error_type_targeted": None,
        "content_json": content_json
    }
)

assert response.status_code == 200
print(f"✅ Created exercise: {response.json()['id']}")
```

### 4. Test Error-Type Routing

```python
from backend.services.recommendation_extended import RecommendationEngine
from backend.database.db import get_db_connection

conn = get_db_connection()
engine = RecommendationEngine(conn)

# Simulate diagnostic with errors
recommendation = engine.get_next_recommendation(
    student_id=1,
    diagnostic_errors=["conceptual", "procedural"]
)

print(f"Action: {recommendation['action']}")
print(f"Target Error: {recommendation['target_error_type']}")
print(f"Exercise Source: {recommendation['exercise_source']}")

# Should prioritize admin exercises for error type
assert recommendation['exercise_source'] in ['admin', 'ai']
conn.close()
```

---

## 🐛 TROUBLESHOOTING

### Issue: "Admin access required" for admin account

**Solution:**
```python
# Verify admin role in database
import sqlite3

conn = sqlite3.connect('data/adaptive_learning.db')
cursor = conn.cursor()

cursor.execute("SELECT id, username, role FROM students WHERE username = 'admin'")
result = cursor.fetchone()

if result[2] != 'admin':
    cursor.execute("UPDATE students SET role = 'admin' WHERE id = ?", (result[0],))
    conn.commit()
    print(f"✅ Fixed: Set {result[1]} to admin role")
else:
    print("✅ Admin role is correct")

conn.close()
```

### Issue: "Cannot find admin route" 404

**Solution:**
Make sure `admin_router` is imported and included in `main.py`:

```python
# In backend/main.py
from backend.routes.admin import router as admin_router

# ...

app.include_router(admin_router)  # Must be included
```

### Issue: JWT token doesn't include role

**Solution:**
Update authentication to include role in token payload. Check `backend/routes/auth.py`:

```python
# Create token payload with role
payload = {
    "sub": username,
    "student_id": student_id,
    "role": student_role,  # Add this
    "iat": iat,
    "exp": exp
}
```

### Issue: Admin dashboard page doesn't load

**Solution:**
1. Check admin.html exists in `/frontend/admin.html`
2. Check admin-api.js and admin-app.js exist in `/frontend/js/`
3. Check admin-style.css exists in `/frontend/css/`
4. Clear browser cache: `Ctrl+Shift+Delete`

### Issue: Exercise creation fails with JSON error

**Solution:**
Ensure `content_json` is a valid dictionary matching the exercise type schema. Validate before sending:

```python
import json

content = {
    "question": "...",
    "options": [...],
    "correct_option": 0
}

# Verify it's valid JSON
json_str = json.dumps(content)
print(f"✅ Valid JSON: {json_str}")
```

---

## 📚 FILES SUMMARY

### New Files Created

| File | Purpose |
|------|---------|
| `backend/routes/admin.py` | All admin endpoints |
| `backend/models/admin_models.py` | Pydantic models for admin |
| `backend/utils/rbac.py` | RBAC utilities and logging |
| `backend/services/recommendation_extended.py` | Error-aware recommendations |
| `frontend/admin.html` | Admin dashboard HTML |
| `frontend/js/admin-api.js` | Admin API client |
| `frontend/js/admin-app.js` | Admin dashboard logic |
| `frontend/css/admin-style.css` | Admin dashboard styles |
| `data/admin_migration.sql` | Database schema extension |

### Modified Files

| File | Changes |
|------|---------|
| `backend/main.py` | Added admin router import and inclusion |
| `backend/routes/curriculum.py` | Added mastery_level to curriculum endpoints |

---

## 🎯 NEXT STEPS

1. **Apply the migration** to your database
2. **Create the first admin** account
3. **Test RBAC** with both student and admin accounts
4. **Create some exercises** through the admin dashboard
5. **Verify error-type routing** in recommendations
6. **Set up logging** to track admin actions

---

## 📞 SUPPORT

For issues or questions:
1. Check the **Troubleshooting** section above
2. Review database migration completeness
3. Verify all new files are in correct locations
4. Check browser console for JavaScript errors
5. Check server logs for backend errors

---

## ✨ FEATURES ADDED

✅ Role-based access control (RBAC)
✅ Complete student management
✅ Exercise creation with multiple types
✅ Error-type targeted exercises
✅ Admin action logging & audit trail
✅ System-wide analytics
✅ Admin dashboard
✅ Exercise prioritization
✅ Backward compatible (no breaking changes)

**System is ready for production use!**
