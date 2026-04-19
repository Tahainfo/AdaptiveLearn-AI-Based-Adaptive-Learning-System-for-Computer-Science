"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

# --- Student Models ---
class StudentCreate(BaseModel):
    username: str
    email: str
    password: str

class StudentLogin(BaseModel):
    username: str
    password: str

class StudentResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: str

# --- Module & Sequence Models ---
class ConceptInSequence(BaseModel):
    id: int
    name: str
    domain: str
    description: Optional[str]
    hours: int

class SequenceResponse(BaseModel):
    id: int
    title: str
    order_index: int
    concepts: List[ConceptInSequence] = []

class ModuleResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    order_index: int
    sequences: List[SequenceResponse] = []

# --- Concept Models ---
class ConceptResponse(BaseModel):
    id: int
    name: str
    domain: str
    description: Optional[str]

# --- Mastery Models ---
class MasteryStateResponse(BaseModel):
    student_id: int
    concept_id: int
    concept_name: str
    mastery_level: float
    attempts_count: int
    correct_count: int

# --- Exercise Models ---
class ExerciseAttemptRequest(BaseModel):
    exercise_id: int
    student_answer: str

class ExerciseAttemptResponse(BaseModel):
    id: int
    is_correct: bool
    error_type: Optional[str]
    feedback: str

# --- AI Models ---
class MasteryProfile(BaseModel):
    """Student's mastery across concepts"""
    concept_name: str
    mastery_level: float
    attempts: int
    correct: int

class MistakePattern(BaseModel):
    """Detected student mistake patterns"""
    concept: str
    mistake_type: str  # conceptual, procedural, careless
    frequency: int
    last_example: str

class AIRequest(BaseModel):
    """Request sent to Claude API"""
    concept_mastery: List[MasteryProfile]
    mistake_patterns: List[MistakePattern]
    weak_concept: str
    difficulty_level: str
    goal: str

class AIResponse(BaseModel):
    """Response from Claude API"""
    exercise: str
    hints: List[str]
    solution: str
    explanation: str
    difficulty: str

# --- Diagnostic Models ---
class DiagnosticQuestion(BaseModel):
    id: int
    concept_id: int
    question: str
    options: List[str]
    correct_answer_index: int

class DiagnosticAnswer(BaseModel):
    question_id: int
    selected_index: int
    concept_id: Optional[int] = None

class DiagnosticTestRequest(BaseModel):
    answers: List[DiagnosticAnswer]

class DiagnosticResult(BaseModel):
    concept_id: int
    concept_name: str
    score: float
    mastery_level: float

# --- Dashboard Models ---
class DashboardResponse(BaseModel):
    student: StudentResponse
    mastery_states: List[MasteryStateResponse]
    recent_attempts: List[Dict]

# --- Error Models ---
class ErrorAnalysisRequest(BaseModel):
    exercise_id: int
    student_answer: str
    correct_answer: str
    concept_id: int

class ErrorAnalysisResponse(BaseModel):
    error_type: str
    explanation: str
    suggestion: str
