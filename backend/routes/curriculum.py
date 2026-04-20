"""
Curriculum routes - Modules, Sequences, and Concepts
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, List
from backend.models.database_models import (
    ModuleResponse, SequenceResponse, ConceptInSequence, ConceptResponse
)
from backend.routes.auth import get_current_student
from backend.database.db import get_db_connection

router = APIRouter(prefix="/curriculum", tags=["curriculum"])

@router.get("/modules")
async def get_all_modules(authorization: Optional[str] = Header(None)):
    """Get all modules for the dashboard"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, description, order_index
        FROM modules
        ORDER BY order_index
    """)
    
    modules = cursor.fetchall()
    
    result = []
    for module in modules:
        module_data = {
            "id": module[0],
            "title": module[1],
            "description": module[2],
            "order_index": module[3],
            "sequences": []
        }
        
        # Get sequences for this module
        cursor.execute("""
            SELECT id, title, order_index
            FROM sequences
            WHERE module_id = ?
            ORDER BY order_index
        """, (module[0],))
        
        sequences = cursor.fetchall()
        for seq in sequences:
            seq_data = {
                "id": seq[0],
                "title": seq[1],
                "order_index": seq[2],
                "concepts": []
            }
            
            # Get concepts for this sequence with mastery levels
            cursor.execute("""
                SELECT c.id, c.name, c.domain, c.description, c.hours, 
                       COALESCE(m.mastery_level, 0.0) as mastery_level,
                       COALESCE(m.attempts_count, 0) as attempts_count,
                       COALESCE(m.correct_count, 0) as correct_count
                FROM concepts c
                LEFT JOIN mastery_state m ON c.id = m.concept_id AND m.student_id = ?
                WHERE c.sequence_id = ?
                ORDER BY c.id
            """, (student_id, seq[0]))
            
            concepts = cursor.fetchall()
            for concept in concepts:
                seq_data["concepts"].append({
                    "id": concept[0],
                    "name": concept[1],
                    "domain": concept[2],
                    "description": concept[3],
                    "hours": concept[4],
                    "mastery_level": concept[5],
                    "attempts_count": concept[6],
                    "correct_count": concept[7]
                })
            
            module_data["sequences"].append(seq_data)
        
        result.append(module_data)
    
    conn.close()
    return result

@router.get("/modules/{module_id}")
async def get_module_details(
    module_id: int,
    authorization: Optional[str] = Header(None)
):
    """Get a specific module with all its sequences"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, description, order_index
        FROM modules
        WHERE id = ?
    """, (module_id,))
    
    module = cursor.fetchone()
    if not module:
        conn.close()
        raise HTTPException(status_code=404, detail="Module not found")
    
    module_data = {
        "id": module[0],
        "title": module[1],
        "description": module[2],
        "order_index": module[3],
        "sequences": []
    }
    
    # Get sequences for this module
    cursor.execute("""
        SELECT id, title, order_index
        FROM sequences
        WHERE module_id = ?
        ORDER BY order_index
    """, (module_id,))
    
    sequences = cursor.fetchall()
    for seq in sequences:
        seq_data = {
            "id": seq[0],
            "title": seq[1],
            "order_index": seq[2],
            "concepts": []
        }
        
        # Get concepts for this sequence with mastery levels
        cursor.execute("""
            SELECT c.id, c.name, c.domain, c.description, c.hours,
                   COALESCE(m.mastery_level, 0.0) as mastery_level,
                   COALESCE(m.attempts_count, 0) as attempts_count,
                   COALESCE(m.correct_count, 0) as correct_count
            FROM concepts c
            LEFT JOIN mastery_state m ON c.id = m.concept_id AND m.student_id = ?
            WHERE c.sequence_id = ?
            ORDER BY c.id
        """, (student_id, seq[0]))
        
        concepts = cursor.fetchall()
        for concept in concepts:
            seq_data["concepts"].append({
                "id": concept[0],
                "name": concept[1],
                "domain": concept[2],
                "description": concept[3],
                "hours": concept[4],
                "mastery_level": concept[5],
                "attempts_count": concept[6],
                "correct_count": concept[7]
            })
        
        module_data["sequences"].append(seq_data)
    
    conn.close()
    return module_data

@router.get("/sequences/{sequence_id}")
async def get_sequence_details(
    sequence_id: int,
    authorization: Optional[str] = Header(None)
):
    """Get a specific sequence with all its concepts and mastery levels"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, module_id, title, order_index
        FROM sequences
        WHERE id = ?
    """, (sequence_id,))
    
    sequence = cursor.fetchone()
    if not sequence:
        conn.close()
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    seq_data = {
        "id": sequence[0],
        "module_id": sequence[1],
        "title": sequence[2],
        "order_index": sequence[3],
        "concepts": []
    }
    
    # Get concepts for this sequence with mastery levels
    cursor.execute("""
        SELECT c.id, c.name, c.domain, c.description, c.hours,
               COALESCE(m.mastery_level, 0.0) as mastery_level,
               COALESCE(m.attempts_count, 0) as attempts_count,
               COALESCE(m.correct_count, 0) as correct_count
        FROM concepts c
        LEFT JOIN mastery_state m ON c.id = m.concept_id AND m.student_id = ?
        WHERE c.sequence_id = ?
        ORDER BY c.id
    """, (student_id, sequence_id))
    
    concepts = cursor.fetchall()
    for concept in concepts:
        seq_data["concepts"].append({
            "id": concept[0],
            "name": concept[1],
            "domain": concept[2],
            "description": concept[3],
            "hours": concept[4],
            "mastery_level": concept[5],
            "attempts_count": concept[6],
            "correct_count": concept[7]
        })
    
    conn.close()
    return seq_data

@router.get("/concepts-by-sequence/{sequence_id}")
async def get_concepts_by_sequence(
    sequence_id: int,
    authorization: Optional[str] = Header(None)
):
    """Get all concepts (notions) for a specific sequence with mastery levels"""
    student_id = get_current_student(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.id, c.name, c.domain, c.description, c.hours,
               COALESCE(m.mastery_level, 0.0) as mastery_level,
               COALESCE(m.attempts_count, 0) as attempts_count,
               COALESCE(m.correct_count, 0) as correct_count
        FROM concepts c
        LEFT JOIN mastery_state m ON c.id = m.concept_id AND m.student_id = ?
        WHERE c.sequence_id = ?
        ORDER BY c.id
    """, (student_id, sequence_id))
    
    concepts = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": concept[0],
            "name": concept[1],
            "domain": concept[2],
            "description": concept[3],
            "hours": concept[4],
            "mastery_level": concept[5],
            "attempts_count": concept[6],
            "correct_count": concept[7]
        }
        for concept in concepts
    ]
