"""
Diagnostic test routes.

Questions come exclusively from admin-created exercises
(is_diagnostic=1, created_by_admin_id IS NOT NULL).
No hardcoded questions, no AI fallback.
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from backend.models.database_models import DiagnosticTestRequest, DiagnosticResult
from backend.routes.auth import get_current_student
from backend.database.db import get_db_connection
import json

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


@router.get("/concepts")
async def get_concepts(authorization: Optional[str] = Header(None)):
    """Get all available concepts for diagnostic."""
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
        {"id": row[0], "name": row[1], "domain": row[2], "description": row[3]}
        for row in concepts
    ]


@router.get("/questions/{concept_id}")
async def get_diagnostic_questions_for_concept(
    concept_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Return admin-created diagnostic exercises for a concept.

    Returns [] when no admin diagnostic exercises exist yet —
    the frontend interprets an empty list as "not available".
    """
    student_id = get_current_student(authorization)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM concepts WHERE id = ?", (concept_id,))
    concept = cursor.fetchone()
    if not concept:
        conn.close()
        raise HTTPException(status_code=404, detail="Concept not found")

    cursor.execute("""
        SELECT id, title, exercise_prompt, exercise_type, content_json, explanation
        FROM exercises
        WHERE concept_id            = ?
          AND is_diagnostic         = 1
          AND is_active             = 1
          AND created_by_admin_id IS NOT NULL
          AND exercise_type         IN ('mcq', 'true_false', 'short_answer')
        ORDER BY RANDOM()
        LIMIT 10
    """, (concept_id,))

    rows = cursor.fetchall()
    conn.close()

    questions = []
    for ex_id, title, exercise_prompt, exercise_type, content_json_str, explanation in rows:
        content = {}
        if content_json_str:
            try:
                content = json.loads(content_json_str)
            except (json.JSONDecodeError, TypeError):
                pass

        expl = content.get("explanation") or explanation or ""

        if exercise_type == "mcq":
            question_text = content.get("question") or exercise_prompt or title
            options = content.get("options", [])
            correct_option = content.get("correct_option", 0)
            if not options:
                continue
            questions.append({
                "id": ex_id,
                "question": question_text,
                "input_type": "radio",
                "options": options,
                "correct_index": correct_option,
                "explanation": expl,
            })

        elif exercise_type == "true_false":
            question_text = content.get("statement") or exercise_prompt or title
            correct_option = 0 if content.get("correct_answer", True) else 1
            questions.append({
                "id": ex_id,
                "question": question_text,
                "input_type": "radio",
                "options": ["True", "False"],
                "correct_index": correct_option,
                "explanation": expl,
            })

        elif exercise_type == "short_answer":
            question_text = content.get("question") or exercise_prompt or title
            correct_answer = content.get("correct_answer", "")
            alternative_answers = content.get("alternative_answers", [])
            questions.append({
                "id": ex_id,
                "question": question_text,
                "input_type": "text",
                "correct_answer": correct_answer,
                "alternative_answers": alternative_answers,
                "explanation": expl,
            })

    return questions


@router.post("/submit/{concept_id}", response_model=DiagnosticResult)
async def submit_diagnostic(
    concept_id: int,
    test_data: DiagnosticTestRequest,
    authorization: Optional[str] = Header(None)
):
    """Submit diagnostic answers for a single concept."""
    student_id = get_current_student(authorization)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM concepts WHERE id = ?", (concept_id,))
    concept = cursor.fetchone()
    if not concept:
        conn.close()
        raise HTTPException(status_code=404, detail="Concept not found")

    concept_name = concept[0]

    if not test_data.answers:
        conn.close()
        raise HTTPException(status_code=400, detail="No answers provided")

    correct_count = 0
    total_count = len(test_data.answers)

    for answer in test_data.answers:
        cursor.execute("""
            SELECT exercise_type, content_json FROM exercises
            WHERE id                   = ?
              AND concept_id           = ?
              AND is_diagnostic        = 1
              AND created_by_admin_id IS NOT NULL
        """, (answer.question_id, concept_id))

        row = cursor.fetchone()
        if not row or not row[1]:
            continue

        try:
            exercise_type, content_json_str = row
            content = json.loads(content_json_str)
            if exercise_type == "mcq":
                correct = content.get("correct_option", -1) == answer.selected_index
            elif exercise_type == "true_false":
                correct_bool = content.get("correct_answer", True)
                correct_idx = 0 if correct_bool else 1
                correct = correct_idx == answer.selected_index
            elif exercise_type == "short_answer":
                student_text = (answer.text_answer or "").strip().lower()
                expected = content.get("correct_answer", "").strip().lower()
                alternatives = [a.strip().lower() for a in content.get("alternative_answers", [])]
                correct = student_text == expected or student_text in alternatives
            else:
                correct = False
            if correct:
                correct_count += 1
        except (json.JSONDecodeError, TypeError):
            pass

    score = (correct_count / total_count * 100) if total_count > 0 else 0
    mastery_level = min(1.0, max(0.0, score / 100.0))

    cursor.execute("""
        INSERT INTO diagnostic_attempts (student_id, concept_id, score, answers)
        VALUES (?, ?, ?, ?)
    """, (student_id, concept_id, score,
          json.dumps([a.dict() for a in test_data.answers])))

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
        "mastery_level": mastery_level,
    }


@router.get("/results/{concept_id}")
async def get_diagnostic_results(
    concept_id: int,
    authorization: Optional[str] = Header(None)
):
    """Get the most recent diagnostic result for a concept."""
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
        "mastery_level": min(1.0, max(0.0, result[0] / 100.0)),
    }


@router.post("/submit")
async def submit_sequence_diagnostic(
    test_data: DiagnosticTestRequest,
    authorization: Optional[str] = Header(None)
):
    """Submit diagnostic answers for a full sequence (multiple concepts)."""
    student_id = get_current_student(authorization)

    if not test_data.answers:
        raise HTTPException(status_code=400, detail="No answers provided")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Group answers by concept_id
    concept_answers: dict = {}
    for answer in test_data.answers:
        cid = getattr(answer, "concept_id", None)
        if cid:
            concept_answers.setdefault(cid, []).append(answer)

    results = []

    for concept_id, answers in concept_answers.items():
        cursor.execute("SELECT name FROM concepts WHERE id = ?", (concept_id,))
        concept = cursor.fetchone()
        if not concept:
            continue

        concept_name = concept[0]
        correct_count = 0
        total_count = len(answers)

        for answer in answers:
            cursor.execute("""
                SELECT exercise_type, content_json FROM exercises
                WHERE id                   = ?
                  AND concept_id           = ?
                  AND is_diagnostic        = 1
                  AND created_by_admin_id IS NOT NULL
            """, (answer.question_id, concept_id))

            row = cursor.fetchone()
            if not row or not row[1]:
                continue

            try:
                exercise_type, content_json_str = row
                content = json.loads(content_json_str)
                if exercise_type == "mcq":
                    correct = content.get("correct_option", -1) == answer.selected_index
                elif exercise_type == "true_false":
                    correct_bool = content.get("correct_answer", True)
                    correct_idx = 0 if correct_bool else 1
                    correct = correct_idx == answer.selected_index
                elif exercise_type == "short_answer":
                    student_text = (answer.text_answer or "").strip().lower()
                    expected = content.get("correct_answer", "").strip().lower()
                    alternatives = [a.strip().lower() for a in content.get("alternative_answers", [])]
                    correct = student_text == expected or student_text in alternatives
                else:
                    correct = False
                if correct:
                    correct_count += 1
            except (json.JSONDecodeError, TypeError):
                pass

        score = (correct_count / total_count * 100) if total_count > 0 else 0
        mastery_level = min(1.0, max(0.0, score / 100.0))

        cursor.execute("""
            INSERT INTO diagnostic_attempts (student_id, concept_id, score, answers)
            VALUES (?, ?, ?, ?)
        """, (student_id, concept_id, score,
              json.dumps([{"question_id": a.question_id,
                           "selected_index": a.selected_index}
                          for a in answers])))

        cursor.execute("""
            INSERT OR REPLACE INTO mastery_state
                (student_id, concept_id, mastery_level, attempts_count, correct_count)
            VALUES (?, ?, ?, 1, ?)
        """, (student_id, concept_id, mastery_level, correct_count))

        results.append({
            "concept_id": concept_id,
            "concept_name": concept_name,
            "score": score,
            "mastery_level": mastery_level,
        })

    conn.commit()
    conn.close()

    return results if results else [{"message": "No valid concept answers found"}]
