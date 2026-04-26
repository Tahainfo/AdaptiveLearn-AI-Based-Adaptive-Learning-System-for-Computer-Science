"""
Prompt templates for AI interactions.
Diagnostic questions are no longer hardcoded here —
they are managed by admins through the exercises table (is_diagnostic=1).
"""

DIAGNOSTIC_PROMPT_TEMPLATE = """You are a diagnostic assessor for Moroccan high school students.

CONCEPT: {concept}

Generate 3 diagnostic questions to assess the students's understanding of this concept.

The questions should:
1. Test foundational understanding
2. Be clear and unambiguous
3. Have 4 multiple choice options

RESPONSE FORMAT:
[
    {{
        "question": "Question text?",
        "options": ["A", "B", "C", "D"],
        "correct_index": 0,
        "explanation": "Why A is correct"
    }},
    ...
]

CONCEPT BACKGROUND:
- For Algorithmics: Focus on logic, control flow, data structures
- For Networks: Focus on protocols, addressing, layers
- Use real-world examples relevant to Morocco

Respond with ONLY the JSON array."""

EXERCISE_GENERATION_TEMPLATE = """You are an expert tutor for Moroccan high school students.

STUDENT STATUS:
- Concept: {concept}
- Current Mastery: {mastery_percent}%
- Difficulty Level: {difficulty}
- Common Mistakes: {mistakes}

Generate a {difficulty} exercise that:
1. Targets {concept}
2. Addresses their common mistakes
3. Builds their mastery progressively
4. Includes pseudocode when relevant

RESPONSE FORMAT:
{{
    "exercise": "Exercise description and question",
    "hints": ["Hint 1", "Hint 2", "Hint 3"],
    "solution": "Complete solution in pseudocode or step-by-step",
    "explanation": "Why this solution works and key concepts",
    "difficulty": "{difficulty}"
}}

Respond with ONLY the JSON object."""

ERROR_ANALYSIS_TEMPLATE = """Analyze this student's error:

CONCEPT: {concept}
CORRECT ANSWER: {correct_answer}
STUDENT ANSWER: {student_answer}

Identify:
1. Is the answer correct?
2. What type of error? (conceptual/procedural/careless)
3. Root cause
4. Helpful feedback

RESPONSE FORMAT:
{{
    "is_correct": true/false,
    "error_type": "none|conceptual|procedural|careless",
    "root_cause": "Explanation of why the error occurred",
    "feedback": "Encouraging and specific feedback",
    "hint": "What to try next"
}}

Respond with ONLY the JSON object."""

HINT_TEMPLATE = """Generate {hint_level} hint for this exercise:

EXERCISE: {exercise}
CONCEPT: {concept}
HINT_LEVEL: {hint_level} (1=basic, 2=intermediate, 3=almost answer)

The hint should:
- Not give away the answer directly
- Guide thinking towards the solution
- Be encouraging and concise

Respond with ONLY the hint text."""
