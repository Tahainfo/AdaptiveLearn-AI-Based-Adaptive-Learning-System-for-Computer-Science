"""
Diagnostic test routes
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, List
from backend.models.database_models import (
    DiagnosticQuestion, DiagnosticTestRequest, DiagnosticResult, DiagnosticAnswer
)
from backend.routes.auth import get_current_student
from backend.database.db import get_db_connection
from backend.services.ai_engine import AIEngine
from backend.utils.prompts import get_diagnostic_questions
import json

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])

@router.get("/concepts")
async def get_concepts(authorization: Optional[str] = Header(None)):
    """Get all available concepts for diagnostic"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, domain, description
        FROM concepts
        ORDER BY domain, name
    """)
    
    concepts = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": row[0],
            "name": row[1],
            "domain": row[2],
            "description": row[3]
        }
        for row in concepts
    ]

@router.get("/questions/{concept_id}")
async def get_diagnostic_questions_for_concept(
    concept_id: int,
    authorization: Optional[str] = Header(None)
):
    """Get diagnostic questions for a concept"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get concept name
    cursor.execute("SELECT name FROM concepts WHERE id = ?", (concept_id,))
    concept = cursor.fetchone()
    conn.close()
    
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    
    concept_name = concept[0]
    
    # Try to get pre-built questions
    questions = get_diagnostic_questions(concept_name)
    
    if not questions:
        # Fall back to AI generation
        try:
            ai_engine = AIEngine()
            questions = ai_engine.generate_diagnostic_questions(concept_name)
        except Exception as e:
            print(f"Error generating questions: {e}")
            questions = [{
                "question": f"Question about {concept_name}?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_index": 0,
                "explanation": "Review the concept materials"
            }]
    
    # Add IDs
    for i, q in enumerate(questions):
        q['id'] = i
    
    return questions

@router.post("/submit/{concept_id}", response_model=DiagnosticResult)
async def submit_diagnostic(
    concept_id: int,
    test_data: DiagnosticTestRequest,
    authorization: Optional[str] = Header(None)
):
    """Submit diagnostic test answers"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify concept exists
    cursor.execute("SELECT name FROM concepts WHERE id = ?", (concept_id,))
    concept = cursor.fetchone()
    
    if not concept:
        conn.close()
        raise HTTPException(status_code=404, detail="Concept not found")
    
    concept_name = concept[0]
    
    # Get questions
    questions = get_diagnostic_questions(concept_name)
    if not questions:
        # Fallback
        questions = [{
            "id": 0,
            "correct_index": 0,
            "explanation": ""
        }]
    
    # Calculate score
    correct_count = 0
    total_count = len(test_data.answers)
    
    for answer in test_data.answers:
        question_id = answer.question_id
        if question_id < len(questions):
            if questions[question_id]['correct_index'] == answer.selected_index:
                correct_count += 1
    
    score = (correct_count / total_count * 100) if total_count > 0 else 0
    
    # Convert score to mastery level
    mastery_level = min(1.0, max(0.0, score / 100.0))
    
    # Store result
    cursor.execute("""
        INSERT INTO diagnostic_attempts
        (student_id, concept_id, score, answers)
        VALUES (?, ?, ?, ?)
    """, (student_id, concept_id, score, json.dumps([a.dict() for a in test_data.answers])))
    
    # Initialize or update mastery
    cursor.execute("""
        INSERT OR REPLACE INTO mastery_state
        (student_id, concept_id, mastery_level, attempts_count, correct_count)
        VALUES (?, ?, ?, 1, ?)
    """, (student_id, concept_id, mastery_level, correct_count))
    
    conn.commit()
    conn.close()
    
    return {
        "concept_id": concept_id,
        "concept_name": concept_name,
        "score": score,
        "mastery_level": mastery_level
    }

@router.get("/results/{concept_id}")
async def get_diagnostic_results(
    concept_id: int,
    authorization: Optional[str] = Header(None)
):
    """Get student's diagnostic results for a concept"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT da.score, da.created_at, c.name
        FROM diagnostic_attempts da
        JOIN concepts c ON da.concept_id = c.id
        WHERE da.student_id = ? AND da.concept_id = ?
        ORDER BY da.created_at DESC
        LIMIT 1
    """, (student_id, concept_id))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="No diagnostic results found")
    
    return {
        "concept_name": result[2],
        "score": result[0],
        "taken_at": result[1],
        "mastery_level": min(1.0, max(0.0, result[0] / 100.0))
    }

@router.post("/submit")
async def submit_sequence_diagnostic(
    test_data: DiagnosticTestRequest,
    authorization: Optional[str] = Header(None)
):
    """Submit diagnostic test answers for a sequence (multiple concepts)"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    results = []
    
    # Group answers by concept
    concept_answers = {}
    for answer in test_data.answers:
        concept_id = getattr(answer, 'concept_id', None)
        if concept_id:
            if concept_id not in concept_answers:
                concept_answers[concept_id] = []
            concept_answers[concept_id].append(answer)
    
    # Process each concept
    for concept_id, answers in concept_answers.items():
        # Get concept name
        cursor.execute("SELECT name FROM concepts WHERE id = ?", (concept_id,))
        concept = cursor.fetchone()
        
        if not concept:
            continue
        
        concept_name = concept[0]
        
        # Get questions for this concept
        questions = get_diagnostic_questions(concept_name)
        if not questions:
            questions = [{
                "id": 0,
                "correct_index": 0,
                "explanation": ""
            }]
        
        # Calculate score
        correct_count = 0
        total_count = len(answers)
        
        for answer in answers:
            question_id = getattr(answer, 'question_id', answer.question_id) if hasattr(answer, 'question_id') else 0
            if question_id < len(questions):
                if questions[question_id]['correct_index'] == answer.selected_index:
                    correct_count += 1
        
        score = (correct_count / total_count * 100) if total_count > 0 else 0
        mastery_level = min(1.0, max(0.0, score / 100.0))
        
        # Store result
        cursor.execute("""
            INSERT INTO diagnostic_attempts
            (student_id, concept_id, score, answers)
            VALUES (?, ?, ?, ?)
        """, (student_id, concept_id, score, json.dumps([{'question_id': getattr(a, 'question_id', 0), 'selected_index': a.selected_index} for a in answers])))
        
        # Initialize or update mastery
        cursor.execute("""
            INSERT OR REPLACE INTO mastery_state
            (student_id, concept_id, mastery_level, attempts_count, correct_count)
            VALUES (?, ?, ?, 1, ?)
        """, (student_id, concept_id, mastery_level, correct_count))
        
        results.append({
            "concept_id": concept_id,
            "concept_name": concept_name,
            "score": score,
            "mastery_level": mastery_level
        })
    
    conn.commit()
    conn.close()
    
    return results if results else [{"message": "No concepts found in answers"}]
