"""
AI explanation route.

Proxies explanation requests to OpenRouter so the API key never
reaches the browser.  One endpoint:

    POST /ai/explain
    { concept_name, question_text, exercise_type,
      student_answer, correct_answer, is_correct }
    → { explanation: str }

Tries a waterfall of free models — skips any that are rate-limited
(429) and moves on to the next until one succeeds.
"""

import os
import httpx
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from backend.routes.auth import get_current_student

router = APIRouter(prefix="/ai", tags=["ai"])

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Ordered fallback list — all free tier, tested working.
# Override the first choice via OPENROUTER_MODEL env var.
_DEFAULT_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",  # 120B, 262K ctx — best quality
    "google/gemma-4-31b-it:free",               # 31B Google model
    "openai/gpt-oss-20b:free",                  # lightweight but reliable
    "openrouter/auto",                           # last resort: OR auto-routes
]


class ExplainRequest(BaseModel):
    concept_name: str
    question_text: str
    exercise_type: str       # "mcq" | "true_false" | "short_answer"
    student_answer: str      # human-readable text of what the student picked/typed
    correct_answer: str      # human-readable text of the correct answer
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
            "Briefly explain what misconception or gap likely led to that mistake."
        )
    )

    return (
        "You are a friendly computer-science tutor helping a student review a diagnostic quiz.\n\n"
        f"Concept: {req.concept_name}\n"
        f"Question: {req.question_text}\n"
        f"Correct answer: {req.correct_answer}\n"
        f"The student {verdict}.{wrong_part}\n\n"
        "Write a clear, concise explanation (2–4 sentences) of WHY the correct answer is right. "
        "Use plain language suitable for a high-school or early-university student. "
        "Do not repeat the question. Do not use markdown headers."
    )


def _model_list() -> list[str]:
    """Return the model waterfall, with the env-var override at the front."""
    env_model = os.getenv("OPENROUTER_MODEL", "").strip()
    if env_model and env_model not in _DEFAULT_MODELS:
        return [env_model] + _DEFAULT_MODELS
    if env_model and env_model in _DEFAULT_MODELS:
        # promote the chosen model to the front
        rest = [m for m in _DEFAULT_MODELS if m != env_model]
        return [env_model] + rest
    return list(_DEFAULT_MODELS)


def _is_provider_rate_limit(resp_json: dict) -> bool:
    """Return True when OpenRouter signals an upstream 429."""
    err = resp_json.get("error", {})
    code = err.get("code")
    raw  = (err.get("metadata") or {}).get("raw", "")
    return code == 429 or "rate-limited" in raw.lower() or "rate limited" in raw.lower()


@router.post("/explain", response_model=ExplainResponse)
async def explain_answer(
    body: ExplainRequest,
    authorization: Optional[str] = Header(None),
):
    """Generate an AI explanation for a diagnostic question answer."""
    get_current_student(authorization)

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="AI explanations are not configured. Ask the administrator to set OPENROUTER_API_KEY.",
        )

    prompt = _build_prompt(body)
    or_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "AdaptiveLearn",
    }

    last_error = "All models unavailable — please try again later."

    async with httpx.AsyncClient(timeout=25.0) as client:
        for model in _model_list():
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.5,
            }

            try:
                response = await client.post(OPENROUTER_API_URL, json=payload, headers=or_headers)
            except httpx.TimeoutException:
                last_error = f"Model {model} timed out."
                continue
            except httpx.RequestError as exc:
                raise HTTPException(status_code=502, detail=f"Could not reach AI service: {exc}")

            if response.status_code == 200:
                data = response.json()
                try:
                    explanation = data["choices"][0]["message"]["content"].strip()
                    return ExplainResponse(explanation=explanation)
                except (KeyError, IndexError):
                    last_error = f"Unexpected response from {model}."
                    continue

            # Parse the error body
            try:
                err_body = response.json()
            except Exception:
                err_body = {}

            if _is_provider_rate_limit(err_body):
                # Try next model in the waterfall
                last_error = f"Model {model} is rate-limited upstream."
                print(f"[ai] {last_error} Trying next model.")
                continue

            # Any other non-200 — surface it directly
            detail = (err_body.get("error") or {}).get("message", response.text)
            raise HTTPException(status_code=502, detail=f"AI service error ({model}): {detail}")

    raise HTTPException(status_code=503, detail=last_error)
