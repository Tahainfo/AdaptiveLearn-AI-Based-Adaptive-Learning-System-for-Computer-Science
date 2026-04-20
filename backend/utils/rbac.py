"""
Role-Based Access Control (RBAC) Middleware and Utilities
"""
from fastapi import HTTPException, status, Depends, Header
from typing import Optional, List, Callable
from functools import wraps
import json
from backend.routes.auth import get_current_student

# =============================================================================
# ROLE-BASED DEPENDENCY CHECKERS
# =============================================================================

async def require_admin(authorization: Optional[str] = Header(None)) -> int:
    """
    Dependency to check if current user is admin.
    Returns admin_id if valid, else raises 403.
    """
    student_id = get_current_student(authorization)
    
    # Query database to verify role
    from backend.database.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT role FROM students WHERE id = ?", (student_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or result[0] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return student_id

async def require_role(required_role: str):
    """
    Factory function to create a role-checking dependency
    Usage: @router.get("/admin/something", dependencies=[Depends(require_role("admin"))])
    """
    async def check_role(authorization: Optional[str] = Header(None)) -> int:
        student_id = get_current_student(authorization)
        
        from backend.database.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT role FROM students WHERE id = ?", (student_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or result[0] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{required_role.title()} access required"
            )
        
        return student_id
    
    return check_role

# =============================================================================
# ADMIN LOGGING UTILITY
# =============================================================================

def log_admin_action(
    admin_id: int,
    action_type: str,
    entity: str,
    entity_id: Optional[int] = None,
    target_user_id: Optional[int] = None,
    details: Optional[dict] = None
):
    """
    Log an admin action to admin_logs table
    
    Args:
        admin_id: Admin performing the action
        action_type: Type of action (create_student, update_exercise, etc.)
        entity: Entity type (student, exercise, diagnostic)
        entity_id: ID of the entity (if applicable)
        target_user_id: User affected by action (if different from admin)
        details: Additional JSON context
    """
    from backend.database.db import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO admin_logs 
            (admin_id, action_type, entity, entity_id, target_user_id, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            admin_id,
            action_type,
            entity,
            entity_id,
            target_user_id,
            json.dumps(details) if details else None
        ))
        conn.commit()
    except Exception as e:
        print(f"Error logging admin action: {e}")
    finally:
        conn.close()

# =============================================================================
# ADMIN UTILITY FUNCTIONS
# =============================================================================

def verify_user_exists(user_id: int) -> bool:
    """Check if a student exists"""
    from backend.database.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM students WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def verify_concept_exists(concept_id: int) -> bool:
    """Check if a concept exists"""
    from backend.database.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM concepts WHERE id = ?", (concept_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def verify_sequence_exists(sequence_id: int) -> bool:
    """Check if a sequence exists"""
    from backend.database.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM sequences WHERE id = ?", (sequence_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def verify_module_exists(module_id: int) -> bool:
    """Check if a module exists"""
    from backend.database.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM modules WHERE id = ?", (module_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_admin_username(admin_id: int) -> str:
    """Get admin's username"""
    from backend.database.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM students WHERE id = ?", (admin_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Unknown"

def get_student_mastery_stats(student_id: int) -> dict:
    """Get student's mastery statistics"""
    from backend.database.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            AVG(mastery_level) as avg_mastery,
            COUNT(*) as total_concepts,
            SUM(CASE WHEN mastery_level >= 0.7 THEN 1 ELSE 0 END) as strong_concepts,
            SUM(CASE WHEN mastery_level < 0.4 THEN 1 ELSE 0 END) as weak_concepts
        FROM mastery_state
        WHERE student_id = ?
    """, (student_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        return {
            "average_mastery": round(result[0], 2),
            "total_concepts": result[1],
            "strong_concepts": result[2],
            "weak_concepts": result[3]
        }
    else:
        return {
            "average_mastery": 0.0,
            "total_concepts": 0,
            "strong_concepts": 0,
            "weak_concepts": 0
        }

def get_exercise_stats(exercise_id: int) -> dict:
    """Get exercise statistics"""
    from backend.database.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_attempts,
            SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_attempts
        FROM exercise_attempts
        WHERE exercise_id = ?
    """, (exercise_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    total = result[0] if result and result[0] else 0
    correct = result[1] if result and result[1] else 0
    success_rate = (correct / total * 100) if total > 0 else 0.0
    
    return {
        "total_attempts": total,
        "correct_attempts": correct,
        "success_rate": round(success_rate, 2)
    }
