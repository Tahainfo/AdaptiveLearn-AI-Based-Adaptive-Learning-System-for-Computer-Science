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
#
# ORDER MATTERS for JSON-heavy requests:
#   - gpt-oss-20b and gemma-4 produce clean output with no thinking preamble.
#   - Nemotron / other reasoning models output a chain-of-thought before JSON;
#     they still work but need _extract_json to scan from the end.
_DEFAULT_MODELS = [
    "openai/gpt-oss-20b:free",                  # clean output, no thinking trace
    "google/gemma-4-31b-it:free",               # 31B Google model, also clean
    "nvidia/nemotron-3-super-120b-a12b:free",  # thinking model — needs more tokens
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
    explanation = await _call_openrouter(prompt, max_tokens=300, api_key=api_key, _caller="explain")
    return ExplainResponse(explanation=explanation)


# =============================================================================
# LEARNING GUIDE  — POST /ai/learning-guide
# =============================================================================

class QuestionResult(BaseModel):
    question: str
    student_answer: str
    correct_answer: str
    is_correct: bool
    concept_name: str = ""


class LearningGuideRequest(BaseModel):
    test_title: str = "Diagnostic Test"
    questions: list[QuestionResult]


class WeakArea(BaseModel):
    concept: str
    gap: str


class KeyLesson(BaseModel):
    title: str
    content: str
    tip: str = ""


class LearningGuideResponse(BaseModel):
    summary: str
    weak_areas: list[WeakArea]
    key_lessons: list[KeyLesson]
    action_plan: list[str]
    strengths: str


def _build_guide_prompt(req: LearningGuideRequest) -> str:
    wrong = [q for q in req.questions if not q.is_correct]
    right = [q for q in req.questions if q.is_correct]
    total = len(req.questions)
    score_pct = round(len(right) / total * 100) if total else 0

    wrong_block = "\n".join(
        f'  - Question: "{q.question}"\n'
        f'    Student answered: "{q.student_answer}" | Correct: "{q.correct_answer}"'
        + (f' [Concept: {q.concept_name}]' if q.concept_name else '')
        for q in wrong
    ) or "  (none — perfect score!)"

    right_block = "\n".join(
        f'  - "{q.question}"' + (f' [Concept: {q.concept_name}]' if q.concept_name else '')
        for q in right
    ) or "  (none)"

    return f"""Tu es un professeur expert en informatique. Tu rédiges un guide d'apprentissage personnalisé pour un élève.

L'élève vient de terminer un test de diagnostic sur : {req.test_title}
Score : {len(right)}/{total} ({score_pct}%)

Réponses INCORRECTES ({len(wrong)}) :
{wrong_block}

Réponses CORRECTES ({len(right)}) :
{right_block}

Génère un objet JSON — sans texte supplémentaire, sans balises markdown — correspondant EXACTEMENT à ce schéma :
{{
  "summary": "<2-3 phrases d'évaluation honnête et encourageante, en s'adressant directement à l'élève avec 'tu'>",
  "weak_areas": [
    {{"concept": "<nom court du concept>", "gap": "<1 phrase décrivant la lacune spécifique révélée, en utilisant 'tu'>"}}
  ],
  "key_lessons": [
    {{"title": "<titre court de la leçon>", "content": "<explication du concept en 2-3 phrases, en utilisant 'tu'>", "tip": "<1 astuce mémo ou conseil pratique>"}}
  ],
  "action_plan": ["<étape concrète et actionnable, formulée avec 'tu'>", ...],
  "strengths": "<1-2 phrases sur ce que l'élève maîtrise clairement, en utilisant 'tu'>"
}}

Règles STRICTES :
- Toutes les valeurs textuelles doivent être rédigées EN FRANÇAIS.
- S'adresser TOUJOURS à l'élève directement avec "tu" (jamais "l'élève" ni "the student").
- weak_areas : une entrée par lacune DISTINCTE (max 5). Si score parfait, lister les points à approfondir.
- key_lessons : 3 à 5 leçons, chacune enseignant quelque chose révélé par les mauvaises réponses.
- action_plan : 3 à 5 étapes concrètes (ex : "Relis le chapitre sur les variables", "Fais 5 exercices sur les boucles").
- strengths : toujours trouver quelque chose de positif, même avec un score de 0%.
- Langue claire adaptée à un élève de lycée ou de première année universitaire.
- Produire UNIQUEMENT l'objet JSON, rien d'autre."""


def _extract_json(text: str) -> dict:
    """
    Extract a JSON object from model output that may contain surrounding text
    (e.g. a chain-of-thought reasoning trace before the actual JSON).

    Strategy: scan BACKWARDS from the last '}' to find its matching '{' using
    a brace-depth counter.  This always picks up the final, complete JSON object
    even when the model has written paragraphs of reasoning before it.
    """
    import json, re

    text = text.strip()

    # Strip markdown code fences if present
    text = re.sub(r'```(?:json)?', '', text)

    # Fast path — try parsing the whole text first (clean models)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # Find the LAST closing brace
    end = text.rfind('}')
    if end == -1:
        raise ValueError("No closing brace '}' found in model output")

    # Walk backwards to find the matching opening brace
    depth = 0
    start = -1
    for i in range(end, -1, -1):
        ch = text[i]
        if ch == '}':
            depth += 1
        elif ch == '{':
            depth -= 1
            if depth == 0:
                start = i
                break

    if start == -1:
        raise ValueError("Could not find matching opening brace '{' in model output")

    candidate = text[start:end + 1]
    return json.loads(candidate)


async def _call_openrouter(prompt: str, max_tokens: int, api_key: str,
                          _caller: str = "") -> str:
    """Shared waterfall caller — returns raw content string."""
    or_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "AdaptiveLearn",
    }
    last_error = "All models unavailable — please try again later."
    tag = f"[ai/{_caller}]" if _caller else "[ai]"

    async with httpx.AsyncClient(timeout=60.0) as client:
        for model in _model_list():
            print(f"{tag} Trying model: {model}")
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.4,
            }
            try:
                response = await client.post(OPENROUTER_API_URL, json=payload, headers=or_headers)
            except httpx.TimeoutException:
                last_error = f"Model {model} timed out."
                print(f"{tag} {last_error}")
                continue
            except httpx.RequestError as exc:
                raise HTTPException(status_code=502, detail=f"Could not reach AI service: {exc}")

            print(f"{tag} HTTP {response.status_code} from {model}")

            if response.status_code == 200:
                data = response.json()
                try:
                    content = data["choices"][0]["message"]["content"]
                    finish  = data["choices"][0].get("finish_reason", "?")
                    print(f"{tag} finish_reason={finish}  content={'<null>' if content is None else f'{len(content)} chars'}")

                    if content is None:
                        last_error = f"Model {model} returned null content (finish_reason={finish}). Trying next."
                        print(f"{tag} {last_error}")
                        continue

                    if finish == "length":
                        # Response was cut off — the JSON is incomplete and will
                        # likely parse as a partial inner object.  Skip to a
                        # model with a shorter output or no reasoning trace.
                        last_error = (
                            f"Model {model} hit token limit before completing the response "
                            f"(finish_reason=length, {len(content)} chars). Trying next model."
                        )
                        print(f"{tag} {last_error}")
                        continue

                    print(f"{tag} Raw response (first 300 chars): {content[:300]!r}")
                    return content.strip()
                except (KeyError, IndexError, AttributeError) as exc:
                    last_error = f"Unexpected response structure from {model}: {exc}  keys={list(data.keys())}"
                    print(f"{tag} {last_error}")
                    continue

            try:
                err_body = response.json()
            except Exception:
                err_body = {}

            if _is_provider_rate_limit(err_body):
                last_error = f"Model {model} is rate-limited upstream."
                print(f"{tag} {last_error} Trying next model.")
                continue

            detail = (err_body.get("error") or {}).get("message", response.text)
            raise HTTPException(status_code=502, detail=f"AI service error ({model}): {detail}")

    raise HTTPException(status_code=503, detail=last_error)


@router.post("/learning-guide", response_model=LearningGuideResponse)
async def get_learning_guide(
    body: LearningGuideRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Generate a personalised learning guide from all diagnostic answers.
    Analyses mistakes collectively and returns structured study advice.
    """
    import json as _json

    get_current_student(authorization)

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="AI not configured.")

    if not body.questions:
        raise HTTPException(status_code=400, detail="No questions provided.")

    prompt = _build_guide_prompt(body)
    print(f"[ai/guide] Sending prompt ({len(prompt)} chars) for test: {body.test_title!r}")
    raw = await _call_openrouter(prompt, max_tokens=4000, api_key=api_key, _caller="guide")

    try:
        data = _extract_json(raw)
    except (ValueError, _json.JSONDecodeError) as exc:
        print(f"[ai/guide] JSON parse failed: {exc}\nRaw:\n{raw[:500]}")
        raise HTTPException(status_code=502, detail="AI returned malformed response. Please try again.")

    # ── Diagnostic log — shows exactly what the model returned ──────────────
    print(f"[ai/guide] Parsed JSON top-level keys: {list(data.keys())}")
    print(f"[ai/guide]   summary      : {str(data.get('summary', '<missing>'))[:120]!r}")
    print(f"[ai/guide]   weak_areas   : {len(data.get('weak_areas') or [])} items  → {data.get('weak_areas', '<missing>')!r}"[:200])
    print(f"[ai/guide]   key_lessons  : {len(data.get('key_lessons') or [])} items")
    print(f"[ai/guide]   action_plan  : {len(data.get('action_plan') or [])} items")
    print(f"[ai/guide]   strengths    : {str(data.get('strengths', '<missing>'))[:120]!r}")
    # ────────────────────────────────────────────────────────────────────────

    # Normalise & validate the parsed structure with safe defaults
    weak_areas = [
        WeakArea(concept=w.get("concept", ""), gap=w.get("gap", ""))
        for w in (data.get("weak_areas") or [])
        if w.get("concept")
    ]
    key_lessons = [
        KeyLesson(
            title=k.get("title", ""),
            content=k.get("content", ""),
            tip=k.get("tip", ""),
        )
        for k in (data.get("key_lessons") or [])
        if k.get("title")
    ]
    action_plan = [s for s in (data.get("action_plan") or []) if isinstance(s, str) and s.strip()]

    result = LearningGuideResponse(
        summary=data.get("summary", ""),
        weak_areas=weak_areas,
        key_lessons=key_lessons,
        action_plan=action_plan,
        strengths=data.get("strengths", ""),
    )
    print(f"[ai/guide] Final response — summary={'YES' if result.summary else 'EMPTY'}, "
          f"weak_areas={len(result.weak_areas)}, key_lessons={len(result.key_lessons)}, "
          f"action_plan={len(result.action_plan)}, strengths={'YES' if result.strengths else 'EMPTY'}")
    return result


# =============================================================================
# CORRECTIVE EXERCISES  — POST /ai/corrective-exercises
# =============================================================================

class WrongQuestion(BaseModel):
    concept: str
    question: str
    correct_answer: str


class CorrectiveExercisesRequest(BaseModel):
    test_title: str = "Diagnostic Test"
    wrong_questions: list[WrongQuestion]


class CorrectiveExercise(BaseModel):
    question: str
    options: list[str]
    correct_index: int
    explanation: str


class CorrectiveExercisesResponse(BaseModel):
    exercises: list[CorrectiveExercise]


def _build_corrective_prompt(req: CorrectiveExercisesRequest) -> str:
    blocks = "\n".join(
        f'  - Concept : "{q.concept}" | Question d\'origine : "{q.question}" | Bonne réponse : "{q.correct_answer}"'
        for q in req.wrong_questions
    )
    n = min(max(len(req.wrong_questions), 3), 5)

    return f"""Tu es un professeur expert en informatique. Tu crées des exercices correctifs ciblés pour un élève.

L'élève a raté les questions suivantes dans un test sur : {req.test_title}

Questions ratées :
{blocks}

Génère exactement {n} exercices QCM (4 choix chacun) pour consolider les lacunes identifiées.

Réponds UNIQUEMENT avec cet objet JSON (pas de markdown, pas de texte supplémentaire) :
{{
  "exercises": [
    {{
      "question": "<question pédagogique directe>",
      "options": ["<choix A>", "<choix B>", "<choix C>", "<choix D>"],
      "correct_index": <0|1|2|3>,
      "explanation": "<1-2 phrases expliquant pourquoi c'est correct, en tutoyant l'élève>"
    }}
  ]
}}

Règles STRICTES :
- Toutes les valeurs textuelles EN FRANÇAIS
- Toujours tutoyer l'élève dans les explications ("tu")
- correct_index = indice 0-3 de la bonne réponse dans options
- Les 4 options doivent être plausibles et représentatives d'erreurs classiques
- Chaque exercice cible UNE lacune identifiée ci-dessus
- UNIQUEMENT le JSON, rien d'autre"""


@router.post("/corrective-exercises", response_model=CorrectiveExercisesResponse)
async def get_corrective_exercises(
    body: CorrectiveExercisesRequest,
    authorization: Optional[str] = Header(None),
):
    """Generate targeted MCQ corrective exercises based on the student's wrong answers."""
    import json as _json

    get_current_student(authorization)

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="AI not configured.")

    if not body.wrong_questions:
        raise HTTPException(status_code=400, detail="No wrong questions provided.")

    prompt = _build_corrective_prompt(body)
    raw = await _call_openrouter(prompt, max_tokens=2000, api_key=api_key, _caller="corrective")

    try:
        data = _extract_json(raw)
    except (ValueError, _json.JSONDecodeError) as exc:
        print(f"[ai/corrective] JSON parse failed: {exc}\nRaw:\n{raw[:500]}")
        raise HTTPException(status_code=502, detail="AI returned malformed response. Please try again.")

    exercises = [
        CorrectiveExercise(
            question=e.get("question", ""),
            options=list(e.get("options", [])),
            correct_index=int(e.get("correct_index", 0)),
            explanation=e.get("explanation", ""),
        )
        for e in (data.get("exercises") or [])
        if e.get("question") and e.get("options") and len(e.get("options", [])) >= 2
    ]

    if not exercises:
        raise HTTPException(status_code=502, detail="AI returned no exercises. Please try again.")

    return CorrectiveExercisesResponse(exercises=exercises)
