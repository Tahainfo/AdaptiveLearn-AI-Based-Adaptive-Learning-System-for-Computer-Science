"""
Admin Interface Routes - Complete CRUD for Users, Exercises, Analytics
Requires admin role for access
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, List
import json
from datetime import datetime

from backend.models.admin_models import (
    AdminStudentCreate, AdminStudentUpdate, AdminPasswordReset, AdminStudentResponse,
    AdminExerciseCreate, AdminExerciseUpdate, AdminExerciseResponse,
    AdminLogResponse, AdminAnalyticsResponse, AdminDashboardResponse,
    ExerciseTemplateCreate, ExerciseTemplateResponse
)
from backend.utils.rbac import (
    require_admin, log_admin_action, verify_user_exists,
    verify_concept_exists, verify_sequence_exists, verify_module_exists,
    get_admin_username, get_student_mastery_stats, get_exercise_stats
)
from backend.utils.auth import hash_password
from backend.database.db import get_db_connection
from backend.routes.auth import get_current_student

router = APIRouter(prefix="/admin", tags=["admin"])

# =============================================================================
# STUDENT MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/students")
async def create_student(
    student_data: AdminStudentCreate,
    admin_id: int = Depends(require_admin)
):
    """Create a new student account (admin only)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if username/email already exists
    cursor.execute("SELECT id FROM students WHERE username = ? OR email = ?", 
                  (student_data.username, student_data.email))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # Hash password
    password_hash = hash_password(student_data.password)
    
    try:
        cursor.execute("""
            INSERT INTO students (username, email, password_hash, role, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (student_data.username, student_data.email, password_hash, student_data.role.value))
        
        conn.commit()
        new_student_id = cursor.lastrowid
        
        # Initialize mastery for this student
        cursor.execute("SELECT id FROM concepts")
        concepts = cursor.fetchall()
        for concept in concepts:
            cursor.execute("""
                INSERT INTO mastery_state 
                (student_id, concept_id, mastery_level, attempts_count, correct_count)
                VALUES (?, ?, 0.0, 0, 0)
            """, (new_student_id, concept[0]))
        conn.commit()
        
        # Log action
        log_admin_action(
            admin_id=admin_id,
            action_type="create_student",
            entity="student",
            entity_id=new_student_id,
            target_user_id=new_student_id,
            details={"username": student_data.username, "role": student_data.role.value}
        )
        
        return {
            "id": new_student_id,
            "username": student_data.username,
            "email": student_data.email,
            "role": student_data.role.value,
            "message": "Student created successfully"
        }
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/students/{student_id}")
async def get_student_details(
    student_id: int,
    admin_id: int = Depends(require_admin)
) -> AdminStudentResponse:
    """Get detailed view of a student"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, email, role, is_active, created_at
        FROM students WHERE id = ?
    """, (student_id,))
    
    student = cursor.fetchone()
    if not student:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get exercise stats
    cursor.execute("""
        SELECT COUNT(*) as exercises_completed
        FROM exercise_attempts WHERE student_id = ?
    """, (student_id,))
    exercises_completed = cursor.fetchone()[0]
    
    conn.close()
    
    # Get mastery stats
    mastery_stats = get_student_mastery_stats(student_id)
    
    # Log action
    log_admin_action(
        admin_id=admin_id,
        action_type="view_student_progress",
        entity="student",
        entity_id=student_id,
        target_user_id=student_id
    )
    
    return AdminStudentResponse(
        id=student[0],
        username=student[1],
        email=student[2],
        role=student[3],
        is_active=bool(student[4]),
        created_at=student[5],
        total_exercises_completed=exercises_completed,
        average_mastery=mastery_stats.get("average_mastery", 0.0)
    )

@router.get("/students")
async def list_students(
    skip: int = 0,
    limit: int = 50,
    admin_id: int = Depends(require_admin)
):
    """List all students with pagination"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, email, role, is_active, created_at
        FROM students
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, (limit, skip))
    
    students = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM students")
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "students": [
            {
                "id": s[0],
                "username": s[1],
                "email": s[2],
                "role": s[3],
                "is_active": bool(s[4]),
                "created_at": s[5]
            }
            for s in students
        ]
    }

@router.put("/students/{student_id}")
async def update_student(
    student_id: int,
    update_data: AdminStudentUpdate,
    admin_id: int = Depends(require_admin)
):
    """Update student information"""
    if not verify_user_exists(student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build dynamic update query
    updates = []
    params = []
    
    if update_data.email is not None:
        updates.append("email = ?")
        params.append(update_data.email)
    if update_data.username is not None:
        updates.append("username = ?")
        params.append(update_data.username)
    if update_data.is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if update_data.is_active else 0)
    if update_data.role is not None:
        updates.append("role = ?")
        params.append(update_data.role.value)
    
    if not updates:
        conn.close()
        return {"message": "No updates provided"}
    
    params.append(student_id)
    
    try:
        query = f"UPDATE students SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        
        log_admin_action(
            admin_id=admin_id,
            action_type="update_student",
            entity="student",
            entity_id=student_id,
            target_user_id=student_id,
            details=update_data.dict(exclude_unset=True)
        )
        
        return {"message": "Student updated successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/students/{student_id}/reset-password")
async def reset_password(
    student_id: int,
    password_data: AdminPasswordReset,
    admin_id: int = Depends(require_admin)
):
    """Admin reset student password"""
    if not verify_user_exists(student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    
    if password_data.new_password != password_data.new_password_confirm:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    if len(password_data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(password_data.new_password)
    
    try:
        cursor.execute(
            "UPDATE students SET password_hash = ? WHERE id = ?",
            (password_hash, student_id)
        )
        conn.commit()
        
        log_admin_action(
            admin_id=admin_id,
            action_type="reset_password",
            entity="student",
            entity_id=student_id,
            target_user_id=student_id
        )
        
        return {"message": "Password reset successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.delete("/students/{student_id}")
async def delete_student(
    student_id: int,
    admin_id: int = Depends(require_admin)
):
    """Delete a student (soft delete - mark inactive)"""
    if not verify_user_exists(student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Prevent self-deletion
    if student_id == admin_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE students SET is_active = 0 WHERE id = ?",
            (student_id,)
        )
        conn.commit()
        
        log_admin_action(
            admin_id=admin_id,
            action_type="delete_student",
            entity="student",
            entity_id=student_id,
            target_user_id=student_id
        )
        
        return {"message": "Student deleted successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# =============================================================================
# EXERCISE MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/exercises")
async def create_exercise(
    exercise_data: AdminExerciseCreate,
    admin_id: int = Depends(require_admin)
):
    """Create a new exercise"""
    # Validate foreign keys
    if not verify_module_exists(exercise_data.module_id):
        raise HTTPException(status_code=404, detail="Module not found")
    if not verify_sequence_exists(exercise_data.sequence_id):
        raise HTTPException(status_code=404, detail="Sequence not found")
    if not verify_concept_exists(exercise_data.concept_id):
        raise HTTPException(status_code=404, detail="Concept not found")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO exercises 
            (title, description, concept_id, difficulty, exercise_type, 
             is_diagnostic, error_type_targeted, content_json, explanation, 
             created_by_admin_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            exercise_data.title,
            exercise_data.description,
            exercise_data.concept_id,
            exercise_data.difficulty,
            exercise_data.exercise_type.value,
            1 if exercise_data.is_diagnostic else 0,
            exercise_data.error_type_targeted.value if exercise_data.error_type_targeted else None,
            json.dumps(exercise_data.content_json),
            exercise_data.explanation,
            admin_id,
            1 if exercise_data.is_active else 0
        ))
        
        conn.commit()
        exercise_id = cursor.lastrowid
        
        log_admin_action(
            admin_id=admin_id,
            action_type="create_exercise",
            entity="exercise",
            entity_id=exercise_id,
            details={
                "title": exercise_data.title,
                "type": exercise_data.exercise_type.value,
                "concept_id": exercise_data.concept_id
            }
        )
        
        return {
            "id": exercise_id,
            "message": "Exercise created successfully"
        }
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/exercises/{exercise_id}")
async def get_exercise(
    exercise_id: int,
    admin_id: int = Depends(require_admin)
) -> AdminExerciseResponse:
    """Get exercise details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, description, concept_id, difficulty, exercise_type,
               is_diagnostic, error_type_targeted, content_json, explanation,
               created_by_admin_id, is_active, created_at
        FROM exercises WHERE id = ?
    """, (exercise_id,))
    
    exercise = cursor.fetchone()
    if not exercise:
        conn.close()
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    conn.close()
    
    # Get stats
    stats = get_exercise_stats(exercise_id)
    
    # Get concept info
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sequence_id FROM concepts WHERE id = ?", (exercise[3],))
    concept_result = cursor.fetchone()
    conn.close()
    
    return AdminExerciseResponse(
        id=exercise[0],
        title=exercise[1],
        description=exercise[2],
        module_id=0,  # Need to fetch from concept->sequence->module
        sequence_id=concept_result[0] if concept_result else 0,
        concept_id=exercise[3],
        difficulty=exercise[4],
        exercise_type=exercise[5],
        is_diagnostic=bool(exercise[6]),
        error_type_targeted=exercise[7],
        is_active=bool(exercise[11]),
        created_by_admin_id=exercise[10],
        created_at=exercise[12],
        attempt_count=stats["total_attempts"],
        success_rate=stats["success_rate"]
    )

@router.get("/exercises")
async def list_exercises(
    concept_id: Optional[int] = None,
    exercise_type: Optional[str] = None,
    is_diagnostic: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    admin_id: int = Depends(require_admin)
):
    """List exercises with filters"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, title, exercise_type, difficulty, is_diagnostic, is_active, created_by_admin_id FROM exercises WHERE 1=1"
    params = []
    
    if concept_id:
        query += " AND concept_id = ?"
        params.append(concept_id)
    if exercise_type:
        query += " AND exercise_type = ?"
        params.append(exercise_type)
    if is_diagnostic is not None:
        query += " AND is_diagnostic = ?"
        params.append(1 if is_diagnostic else 0)
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, skip])
    
    cursor.execute(query, params)
    exercises = cursor.fetchall()
    
    # Get total count
    count_query = "SELECT COUNT(*) FROM exercises WHERE 1=1"
    count_params = []
    if concept_id:
        count_query += " AND concept_id = ?"
        count_params.append(concept_id)
    if exercise_type:
        count_query += " AND exercise_type = ?"
        count_params.append(exercise_type)
    if is_diagnostic is not None:
        count_query += " AND is_diagnostic = ?"
        count_params.append(1 if is_diagnostic else 0)
    
    cursor.execute(count_query, count_params)
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "exercises": [
            {
                "id": e[0],
                "title": e[1],
                "exercise_type": e[2],
                "difficulty": e[3],
                "is_diagnostic": bool(e[4]),
                "is_active": bool(e[5]),
                "created_by_admin_id": e[6]
            }
            for e in exercises
        ]
    }

@router.put("/exercises/{exercise_id}")
async def update_exercise(
    exercise_id: int,
    update_data: AdminExerciseUpdate,
    admin_id: int = Depends(require_admin)
):
    """Update exercise"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM exercises WHERE id = ?", (exercise_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    updates = []
    params = []
    
    if update_data.title is not None:
        updates.append("title = ?")
        params.append(update_data.title)
    if update_data.description is not None:
        updates.append("description = ?")
        params.append(update_data.description)
    if update_data.difficulty is not None:
        updates.append("difficulty = ?")
        params.append(update_data.difficulty)
    if update_data.exercise_type is not None:
        updates.append("exercise_type = ?")
        params.append(update_data.exercise_type.value)
    if update_data.is_diagnostic is not None:
        updates.append("is_diagnostic = ?")
        params.append(1 if update_data.is_diagnostic else 0)
    if update_data.error_type_targeted is not None:
        updates.append("error_type_targeted = ?")
        params.append(update_data.error_type_targeted.value)
    if update_data.content_json is not None:
        updates.append("content_json = ?")
        params.append(json.dumps(update_data.content_json))
    if update_data.explanation is not None:
        updates.append("explanation = ?")
        params.append(update_data.explanation)
    if update_data.is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if update_data.is_active else 0)
    
    if not updates:
        conn.close()
        return {"message": "No updates provided"}
    
    params.append(exercise_id)
    
    try:
        query = f"UPDATE exercises SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        
        log_admin_action(
            admin_id=admin_id,
            action_type="update_exercise",
            entity="exercise",
            entity_id=exercise_id
        )
        
        return {"message": "Exercise updated successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/exercises/{exercise_id}/activate")
async def activate_exercise(
    exercise_id: int,
    admin_id: int = Depends(require_admin)
):
    """Activate an exercise"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE exercises SET is_active = 1 WHERE id = ?", (exercise_id,))
    conn.commit()
    conn.close()
    
    log_admin_action(
        admin_id=admin_id,
        action_type="activate_exercise",
        entity="exercise",
        entity_id=exercise_id
    )
    
    return {"message": "Exercise activated"}

@router.post("/exercises/{exercise_id}/deactivate")
async def deactivate_exercise(
    exercise_id: int,
    admin_id: int = Depends(require_admin)
):
    """Deactivate an exercise"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE exercises SET is_active = 0 WHERE id = ?", (exercise_id,))
    conn.commit()
    conn.close()
    
    log_admin_action(
        admin_id=admin_id,
        action_type="deactivate_exercise",
        entity="exercise",
        entity_id=exercise_id
    )
    
    return {"message": "Exercise deactivated"}

# =============================================================================
# ADMIN LOGS & ANALYTICS
# =============================================================================

@router.get("/logs")
async def get_admin_logs(
    skip: int = 0,
    limit: int = 50,
    admin_id: int = Depends(require_admin)
):
    """Get admin action logs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT l.id, l.admin_id, s.username, l.action_type, l.entity, 
               l.entity_id, l.target_user_id, l.details, l.timestamp
        FROM admin_logs l
        JOIN students s ON l.admin_id = s.id
        ORDER BY l.timestamp DESC
        LIMIT ? OFFSET ?
    """, (limit, skip))
    
    logs = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM admin_logs")
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "logs": [
            {
                "id": l[0],
                "admin_id": l[1],
                "admin_username": l[2],
                "action_type": l[3],
                "entity": l[4],
                "entity_id": l[5],
                "target_user_id": l[6],
                "details": json.loads(l[7]) if l[7] else None,
                "timestamp": l[8]
            }
            for l in logs
        ]
    }

@router.get("/analytics")
async def get_analytics(
    admin_id: int = Depends(require_admin)
) -> AdminAnalyticsResponse:
    """Get system-wide analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total students
    cursor.execute("SELECT COUNT(*) FROM students WHERE role = 'student' AND is_active = 1")
    total_students = cursor.fetchone()[0]
    
    # Total exercises
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE is_active = 1")
    total_exercises = cursor.fetchone()[0]
    
    # Admin-created exercises
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE created_by_admin_id IS NOT NULL AND is_active = 1")
    admin_exercises = cursor.fetchone()[0]
    
    ai_exercises = total_exercises - admin_exercises
    
    # Average mastery
    cursor.execute("SELECT AVG(mastery_level) FROM mastery_state")
    avg_mastery = cursor.fetchone()[0] or 0.0
    
    # Weakest concepts
    cursor.execute("""
        SELECT c.id, c.name, AVG(m.mastery_level) as avg_mastery,
               COUNT(DISTINCT m.student_id) as weak_student_count
        FROM concepts c
        LEFT JOIN mastery_state m ON c.id = m.concept_id
        WHERE m.mastery_level < 0.5
        GROUP BY c.id, c.name
        ORDER BY avg_mastery ASC
        LIMIT 5
    """)
    
    weakest = []
    for row in cursor.fetchall():
        weakest.append({
            "concept_id": row[0],
            "concept_name": row[1],
            "average_mastery": round(row[2], 2) if row[2] else 0,
            "students_with_weakness": row[3],
            "students_with_strength": 0,
            "total_attempts": 0,
            "success_rate": 0
        })
    
    # Most common errors
    cursor.execute("""
        SELECT error_type, COUNT(*) as frequency
        FROM exercise_attempts
        WHERE error_type IS NOT NULL
        GROUP BY error_type
        ORDER BY frequency DESC
    """)
    
    errors = []
    for row in cursor.fetchall():
        errors.append({
            "error_type": row[0],
            "frequency": row[1],
            "student_count": 0,
            "concepts_affected": [],
            "avg_difficulty": 0
        })
    
    # Diagnostic completion
    cursor.execute("""
        SELECT COUNT(DISTINCT student_id) FROM diagnostic_attempts
    """)
    diagnostic_completions = cursor.fetchone()[0]
    diagnostic_rate = (diagnostic_completions / total_students * 100) if total_students > 0 else 0
    
    conn.close()
    
    return AdminAnalyticsResponse(
        total_students=total_students,
        total_exercises=total_exercises,
        admin_created_exercises=admin_exercises,
        ai_generated_exercises=ai_exercises,
        average_student_mastery=round(avg_mastery, 2),
        weakest_concepts=weakest,
        most_common_errors=errors,
        diagnostic_completion_rate=round(diagnostic_rate, 2),
        timestamp=datetime.now().isoformat()
    )

@router.get("/dashboard")
async def get_admin_dashboard(
    admin_id: int = Depends(require_admin)
) -> AdminDashboardResponse:
    """Get admin dashboard summary"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get stats
    cursor.execute("SELECT COUNT(*) FROM students WHERE role = 'student'")
    total_students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM students WHERE role = 'student' AND is_active = 1")
    active_students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE is_active = 1")
    total_exercises = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE created_by_admin_id IS NOT NULL AND is_active = 1")
    admin_exercises = cursor.fetchone()[0]
    
    # Recent logs
    cursor.execute("""
        SELECT l.id, l.admin_id, s.username, l.action_type, l.entity, 
               l.entity_id, l.target_user_id, l.details, l.timestamp
        FROM admin_logs l
        JOIN students s ON l.admin_id = s.id
        ORDER BY l.timestamp DESC
        LIMIT 10
    """)
    
    recent_logs = []
    for row in cursor.fetchall():
        recent_logs.append(AdminLogResponse(
            id=row[0],
            admin_id=row[1],
            admin_username=row[2],
            action_type=row[3],
            entity=row[4],
            entity_id=row[5],
            target_user_id=row[6],
            details=json.loads(row[7]) if row[7] else None,
            timestamp=row[8]
        ))
    
    # Mastery distribution
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN AVG(mastery_level) >= 0.7 THEN 1 ELSE 0 END) as excellent,
            SUM(CASE WHEN AVG(mastery_level) >= 0.4 AND AVG(mastery_level) < 0.7 THEN 1 ELSE 0 END) as good,
            SUM(CASE WHEN AVG(mastery_level) < 0.4 THEN 1 ELSE 0 END) as weak
        FROM (
            SELECT student_id, AVG(mastery_level) as avg_mastery
            FROM mastery_state
            GROUP BY student_id
        )
    """)
    
    mastery_dist = cursor.fetchone()
    distribution = {
        "excellent": mastery_dist[0] or 0,
        "good": mastery_dist[1] or 0,
        "weak": mastery_dist[2] or 0
    }
    
    # Most practiced concepts
    cursor.execute("""
        SELECT c.name, COUNT(*) as attempt_count
        FROM exercise_attempts ea
        JOIN exercises e ON ea.exercise_id = e.id
        JOIN concepts c ON e.concept_id = c.id
        GROUP BY c.id, c.name
        ORDER BY attempt_count DESC
        LIMIT 5
    """)
    
    most_practiced = [
        {"concept_name": row[0], "attempts": row[1]}
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return AdminDashboardResponse(
        total_students=total_students,
        active_students=active_students,
        total_exercises=total_exercises,
        admin_exercises_count=admin_exercises,
        recent_logs=recent_logs,
        student_mastery_distribution=distribution,
        most_practiced_concepts=most_practiced,
        timestamp=datetime.now().isoformat()
    )
