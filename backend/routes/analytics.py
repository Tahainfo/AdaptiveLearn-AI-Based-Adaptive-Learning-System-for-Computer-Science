"""
Analytics and Dashboard routes
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from backend.routes.auth import get_current_student
from backend.database.db import get_db_connection
from backend.services.student_model import StudentModel
from backend.services.recommendation import RecommendationEngine

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard")
async def get_dashboard(authorization: Optional[str] = Header(None)):
    """Get student dashboard with progress overview"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Student info
    cursor.execute("""
        SELECT username, email, created_at FROM students WHERE id = ?
    """, (student_id,))
    
    student = cursor.fetchone()
    if not student:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Mastery state
    cursor.execute("""
        SELECT c.id, c.name, c.domain, m.mastery_level, m.attempts_count, m.correct_count
        FROM mastery_state m
        JOIN concepts c ON m.concept_id = c.id
        WHERE m.student_id = ?
        ORDER BY c.domain, c.name
    """, (student_id,))
    
    mastery_data = cursor.fetchall()
    
    mastery_states = []
    for row in mastery_data:
        mastery_states.append({
            'concept_id': row[0],
            'concept_name': row[1],
            'domain': row[2],
            'mastery_level': row[3],
            'attempts': row[4],
            'correct': row[5]
        })
    
    # Recent attempts
    cursor.execute("""
        SELECT c.name, ea.is_correct, ea.created_at
        FROM exercise_attempts ea
        JOIN exercises e ON ea.exercise_id = e.id
        JOIN concepts c ON e.concept_id = c.id
        WHERE ea.student_id = ?
        ORDER BY ea.created_at DESC
        LIMIT 5
    """, (student_id,))
    
    recent_attempts = []
    for row in cursor.fetchall():
        recent_attempts.append({
            'concept': row[0],
            'is_correct': bool(row[1]),
            'timestamp': row[2]
        })
    
    # Get statistics
    student_model = StudentModel(conn)
    stats = student_model.get_performance_stats(student_id)
    
    conn.close()
    
    return {
        'student': {
            'id': student_id,
            'username': student[0],
            'email': student[1],
            'created_at': student[2]
        },
        'mastery_states': mastery_states,
        'recent_attempts': recent_attempts,
        'statistics': stats
    }

@router.get("/progress")
async def get_progress(authorization: Optional[str] = Header(None)):
    """Get detailed progress by domain"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Group by domain
    cursor.execute("""
        SELECT c.domain, COUNT(*) as total_concepts,
               COUNT(CASE WHEN m.mastery_level >= 0.7 THEN 1 END) as mastered,
               COUNT(CASE WHEN m.mastery_level >= 0.4 AND m.mastery_level < 0.7 THEN 1 END) as developing,
               COUNT(CASE WHEN m.mastery_level < 0.4 THEN 1 END) as struggling,
               AVG(m.mastery_level) as avg_mastery
        FROM concepts c
        LEFT JOIN mastery_state m ON c.id = m.concept_id AND m.student_id = ?
        GROUP BY c.domain
        ORDER BY c.domain
    """, (student_id,))
    
    domains = []
    for row in cursor.fetchall():
        domain, total, mastered, developing, struggling, avg_mastery = row
        mastered = mastered or 0
        developing = developing or 0
        struggling = struggling or 0
        avg_mastery = avg_mastery or 0.0
        
        domains.append({
            'domain': domain,
            'total_concepts': total,
            'mastered': mastered,
            'developing': developing,
            'struggling': struggling,
            'average_mastery': round(avg_mastery, 3),
            'progress_percentage': (mastered / total * 100) if total else 0
        })
    
    conn.close()
    
    return {'domains': domains}

@router.get("/recommendations")
async def get_recommendations(authorization: Optional[str] = Header(None)):
    """Get personalized learning recommendations"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    
    # Study path for Algorithmics
    recommender = RecommendationEngine(conn)
    
    algo_path = recommender.recommend_study_path(student_id, 'Algorithmics')
    networks_path = recommender.recommend_study_path(student_id, 'Networks')
    
    # Get next recommendation
    next_rec = recommender.get_next_recommendation(student_id)
    
    conn.close()
    
    return {
        'algorithmics_path': algo_path,
        'networks_path': networks_path,
        'next_action': next_rec
    }

@router.get("/proficiency-by-concept")
async def get_proficiency_by_concept(authorization: Optional[str] = Header(None)):
    """Get mastery distribution across all concepts"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.name, c.domain, m.mastery_level, m.attempts_count
        FROM mastery_state m
        JOIN concepts c ON m.concept_id = c.id
        WHERE m.student_id = ?
        ORDER BY m.mastery_level DESC
    """, (student_id,))
    
    proficiency = []
    for row in cursor.fetchall():
        name, domain, mastery, attempts = row
        
        if mastery >= 0.7:
            level = 'Mastered'
        elif mastery >= 0.4:
            level = 'Developing'
        else:
            level = 'Struggling'
        
        proficiency.append({
            'concept': name,
            'domain': domain,
            'mastery_level': round(mastery, 3),
            'attempts': attempts,
            'level': level
        })
    
    conn.close()
    
    return {'concepts': proficiency}

@router.get("/learning-analytics")
async def get_learning_analytics(authorization: Optional[str] = Header(None)):
    """Get detailed learning analytics"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Time series data
    cursor.execute("""
        SELECT DATE(created_at) as study_date, COUNT(*) as exercises_done,
               SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers
        FROM exercise_attempts
        WHERE student_id = ?
        GROUP BY DATE(created_at)
        ORDER BY study_date DESC
        LIMIT 30
    """, (student_id,))
    
    daily_stats = []
    for row in cursor.fetchall():
        date, exercises, correct = row
        correct = correct or 0
        daily_stats.append({
            'date': date,
            'exercises_completed': exercises,
            'correct_answers': correct,
            'accuracy': (correct / exercises * 100) if exercises else 0
        })
    
    # Error type distribution
    cursor.execute("""
        SELECT error_type, COUNT(*) as count
        FROM exercise_attempts
        WHERE student_id = ? AND is_correct = 0
        GROUP BY error_type
        ORDER BY count DESC
    """, (student_id,))
    
    error_distribution = []
    for row in cursor.fetchall():
        error_type, count = row
        error_distribution.append({
            'error_type': error_type or 'unknown',
            'count': count
        })
    
    conn.close()
    
    return {
        'daily_activity': daily_stats,
        'error_distribution': error_distribution
    }
