"""
Exercise routes - Main learning interface
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional, List
from backend.models.database_models import (
    ExerciseAttemptRequest, ExerciseAttemptResponse, MasteryProfile, MistakePattern
)
from backend.routes.auth import get_current_student
from backend.database.db import get_db_connection, get_db
from backend.services.student_model import StudentModel
from backend.services.error_analyzer import ErrorAnalyzer
from backend.services.ai_engine import AIEngine
from backend.services.recommendation import RecommendationEngine
from backend.models.database_models import AIRequest
import json

router = APIRouter(prefix="/exercise", tags=["exercise"])

@router.get("/next")
async def get_next_exercise(authorization: Optional[str] = Header(None)):
    """Get the next recommended exercise for student"""
    student_id = get_current_student(authorization)
    
    with get_db() as conn:
        # Get recommendation
        recommender = RecommendationEngine(conn)
        recommendation = recommender.get_next_recommendation(student_id)
        
        # If diagnostic test needed, return that
        if recommendation['action'] == 'diagnostic_test':
            return {
                "type": "diagnostic",
                "message": "Let's start with a diagnostic test to understand your current level",
                "recommendation": recommendation
            }
        
        # Otherwise, get exercise
        concept_id = recommendation.get('concept_id')
        
        if not concept_id:
            raise HTTPException(status_code=400, detail="Unable to determine next exercise")
        
        # Get student profile for AI
        student_model = StudentModel(conn)
        mastery_profile = student_model.get_student_mastery_profile(student_id)
        
        # Get mistake patterns
        error_analyzer = ErrorAnalyzer(conn)
        mistakes = error_analyzer.get_mistake_patterns(student_id)
        
        # Get difficulty level
        difficulty = student_model.get_difficulty_level(student_id, concept_id)
        
        # Get concept name
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM concepts WHERE id = ?", (concept_id,))
        concept = cursor.fetchone()
        concept_name = concept[0] if concept else "Unknown"
        
        # Prepare AI request
        mastery_profiles = []
        for concept_name, data in mastery_profile.items():
            mastery_profiles.append(MasteryProfile(
                concept_name=concept_name,
                mastery_level=data['mastery_level'],
                attempts=data['attempts'],
                correct=data['correct']
            ))
        
        mistake_patterns = [
            MistakePattern(
                concept=m['concept'],
                mistake_type=m['mistake_type'],
                frequency=m['frequency'],
                last_example=""
            )
            for m in mistakes
        ]
        
        ai_request = AIRequest(
            concept_mastery=mastery_profiles,
            mistake_patterns=mistake_patterns,
            weak_concept=concept_name,
            difficulty_level=difficulty,
            goal="generate targeted exercise"
        )
        
        # Generate exercise using Claude
        ai_engine = AIEngine()
        exercise_data = ai_engine.generate_adaptive_exercise(ai_request)
        
        # Store exercise in database
        cursor.execute("""
            INSERT INTO exercises
            (concept_id, title, description, difficulty, exercise_prompt, solution, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            concept_id,
            concept_name,
            "Adaptive Exercise",
            difficulty,
            exercise_data.get('exercise', ''),
            exercise_data.get('solution', ''),
            exercise_data.get('explanation', '')
        ))
        conn.commit()
        
        exercise_id = cursor.lastrowid
        
        return {
            "type": "exercise",
            "exercise_id": exercise_id,
            "concept_id": concept_id,
            "concept_name": concept_name,
            "difficulty": difficulty,
            "exercise": exercise_data.get('exercise', ''),
            "hints": exercise_data.get('hints', []),
            "recommendation": recommendation
        }

@router.post("/submit")
async def submit_exercise_answer(
    answer_data: ExerciseAttemptRequest,
    authorization: Optional[str] = Header(None)
):
    """Submit exercise answer"""
    student_id = get_current_student(authorization)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get exercise
        cursor.execute("""
            SELECT solution, concept_id FROM exercises WHERE id = ?
        """, (answer_data.exercise_id,))
        
        exercise = cursor.fetchone()
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        solution, concept_id = exercise
        
        # Analyze answer
        error_analyzer = ErrorAnalyzer(conn)
        analysis = error_analyzer.classify_error(
            answer_data.student_answer,
            solution,
            "Exercise"
        )
        
        is_correct = analysis.get('is_correct', False)
        error_type = analysis.get('error_type')
        
        # Record attempt
        cursor.execute("""
            INSERT INTO exercise_attempts
            (student_id, exercise_id, student_answer, is_correct, error_type)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, answer_data.exercise_id, answer_data.student_answer, is_correct, error_type))
        
        # Log mistake if incorrect
        if not is_correct:
            error_analyzer.log_mistake(
                student_id,
                concept_id,
                error_type or 'unknown',
                answer_data.student_answer[:100]
            )
        
        # Update mastery
        student_model = StudentModel(conn)
        new_mastery = student_model.update_mastery_level(student_id, concept_id, is_correct)
        
        conn.commit()
        
        # Generate feedback
        feedback = "Well done! You've mastered this concept." if is_correct else \
                  f"Not quite right. This is a {error_type} error. Try again!"
        
        return {
            "is_correct": is_correct,
            "error_type": error_type,
            "feedback": feedback,
            "new_mastery": new_mastery,
            "hint": analysis.get('details', 'Keep practicing!')
        }

@router.get("/hint/{exercise_id}")
async def get_hint(
    exercise_id: int,
    hint_level: Optional[int] = 1,
    authorization: Optional[str] = Header(None)
):
    """Get a hint for an exercise"""
    student_id = get_current_student(authorization)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # This would normally be generated by AI
        # For now, return pre-generated hints
        hints = [
            "Start by understanding what the problem is asking",
            "Work through the logic step by step",
            "Check if your solution handles edge cases"
        ]
        
        if hint_level > 3:
            hint_level = 3
        if hint_level < 1:
            hint_level = 1
        
        return {
            "hint": hints[hint_level - 1],
            "level": hint_level,
            "message": "Remember: the solution should follow the concept principles we've taught."
        }

@router.get("/stats")
async def get_exercise_stats(
    authorization: Optional[str] = Header(None)
):
    """Get student's exercise statistics"""
    student_id = get_current_student(authorization)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute("""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM exercise_attempts
            WHERE student_id = ?
        """, (student_id,))
        
        total, correct = cursor.fetchone()
        total = total or 0
        correct = correct or 0
        
        # Stats by concept
        cursor.execute("""
            SELECT c.name, COUNT(*) as attempts,
                   SUM(CASE WHEN ea.is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM exercise_attempts ea
            JOIN exercises e ON ea.exercise_id = e.id
            JOIN concepts c ON e.concept_id = c.id
            WHERE ea.student_id = ?
            GROUP BY c.id, c.name
            ORDER BY attempts DESC
        """, (student_id,))
        
        by_concept = []
        for row in cursor.fetchall():
            concept_name, attempts, concept_correct = row
            by_concept.append({
                "concept": concept_name,
                "attempts": attempts,
                "correct": concept_correct or 0,
                "accuracy": (concept_correct / attempts * 100) if attempts else 0
            })
        
        return {
            "total_attempts": total,
            "total_correct": correct,
            "overall_accuracy": (correct / total * 100) if total else 0,
            "by_concept": by_concept
        }
