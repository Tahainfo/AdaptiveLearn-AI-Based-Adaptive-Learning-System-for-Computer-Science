"""
AI explanation route.

Proxies explanation requests to OpenRouter so the API key never
reaches the browser.  One endpoint:

    POST /ai/explain
    { concept_name, question_text, exercise_type,
      student_answer, correct_answer, is_correct }
    → { explanation: str }
"""

import os
import httpx
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from backend.routes.auth import get_current_student

router = APIRouter(prefix="/ai", tags=["ai"])

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class ExplainRequest(BaseModel):
    concept_name: str
    question_text: str
    exercise_type: str          # "mcq" | "true_false" | "short_answer"
    student_answer: str         # human-readable text of what the student picked/typed
    correct_answer: str         # human-readable text of the correct answer
    is_correct: bool


class ExplainResponse(BaseModel):
    explanation: str


def _build_prompt(req: ExplainRequest) -> str:
    verdict = "answered correctly" if req.is_correct else "answered incorrectly"
    wrong_part = (
        ""
        if req.is_correct
        else (
            f'\nThe student chose: "{req.student_answer}"\n'
            f"Briefly explain what misconception or gap likely led to that mistake."
        )
    )

    return (
        f"You are a friendly computer-science tutor helping a student review a diagnostic quiz.\n\n"
        f"Concept: {req.concept_name}\n"
        f"Question: {req.question_text}\n"
        f"Correct answer: {req.correct_answer}\n"
        f"The student {verdict}.{wrong_part}\n\n"
        f"Write a clear, concise explanation (2–4 sentences) of WHY the correct answer is right. "
        f"Use plain language suitable for a high-school or early-university student. "
        f"Do not repeat the question. Do not use markdown headers."
    )


@router.post("/explain", response_model=ExplainResponse)
async def explain_answer(
    body: ExplainRequest,
    authorization: Optional[str] = Header(None),
):
    """Generate an AI explanation for a diagnostic question answer."""
    # Require authenticated student (just validates token, id not used)
    get_current_student(authorization)

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="AI explanations are not configured. Ask the administrator to set OPENROUTER_API_KEY.",
        )

    model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": _build_prompt(body)}],
        "max_tokens": 300,
        "temperature": 0.5,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "AdaptiveLearn",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(OPENROUTER_API_URL, json=payload, headers=headers)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timed out. Please try again.")
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach AI service: {exc}")

    if response.status_code != 200:
        try:
            err = response.json()
            detail = err.get("error", {}).get("message", response.text)
        except Exception:
            detail = response.text
        raise HTTPException(status_code=502, detail=f"AI service error: {detail}")

    data = response.json()
    try:
        explanation = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Unexpected response format from AI service.")

    return ExplainResponse(explanation=explanation)
