"""
Extended Pydantic models for Admin Interface and RBAC
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# =============================================================================
# ENUMS
# =============================================================================
class RoleEnum(str, Enum):
    STUDENT = "student"
    ADMIN = "admin"

class ExerciseTypeEnum(str, Enum):
    MCQ = "mcq"
    DRAG_DROP = "drag_drop"
    MATCH_LINES = "match_lines"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    TRUE_FALSE = "true_false"

class ErrorTypeEnum(str, Enum):
    CONCEPTUAL = "conceptual"
    PROCEDURAL = "procedural"
    CARELESS = "careless"

class AdminActionEnum(str, Enum):
    CREATE_STUDENT = "create_student"
    UPDATE_STUDENT = "update_student"
    DELETE_STUDENT = "delete_student"
    RESET_PASSWORD = "reset_password"
    CREATE_EXERCISE = "create_exercise"
    UPDATE_EXERCISE = "update_exercise"
    DELETE_EXERCISE = "delete_exercise"
    ACTIVATE_EXERCISE = "activate_exercise"
    DEACTIVATE_EXERCISE = "deactivate_exercise"
    VIEW_STUDENT_PROGRESS = "view_student_progress"
    VIEW_ANALYTICS = "view_analytics"

# =============================================================================
# EXERCISE CONTENT SCHEMAS (JSON Structure)
# =============================================================================
class MCQContent(BaseModel):
    question: str
    options: List[str]
    correct_option: int  # Index of correct option
    explanation: Optional[str] = None

class DragDropContent(BaseModel):
    question: str
    items: List[str]
    correct_order: List[int]  # Indices showing correct order
    explanation: Optional[str] = None

class MatchLinesContent(BaseModel):
    question: str
    left_items: List[str]
    right_items: List[str]
    correct_pairs: List[tuple]  # [(left_idx, right_idx), ...]
    explanation: Optional[str] = None

class ShortAnswerContent(BaseModel):
    question: str
    correct_answer: str
    alternative_answers: List[str] = []
    explanation: Optional[str] = None

class LongAnswerContent(BaseModel):
    question: str
    expected_keywords: List[str]
    rubric: Optional[str] = None
    explanation: Optional[str] = None

class TrueFalseContent(BaseModel):
    statement: str
    correct_answer: bool
    explanation: Optional[str] = None

# Union of all content types
ExerciseContent = Union[
    MCQContent, 
    DragDropContent, 
    MatchLinesContent,
    ShortAnswerContent,
    LongAnswerContent,
    TrueFalseContent
]

# =============================================================================
# ADMIN STUDENT MANAGEMENT MODELS
# =============================================================================
class AdminStudentCreate(BaseModel):
    username: str
    email: str
    password: str
    role: RoleEnum = RoleEnum.STUDENT

class AdminStudentUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[RoleEnum] = None

class AdminPasswordReset(BaseModel):
    new_password: str
    new_password_confirm: str

class AdminStudentResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    total_exercises_completed: int = 0
    average_mastery: float = 0.0

# =============================================================================
# ADMIN EXERCISE MANAGEMENT MODELS
# =============================================================================
class AdminExerciseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    module_id: int
    sequence_id: int
    concept_id: int
    difficulty: str  # "easy", "medium", "challenging"
    exercise_type: ExerciseTypeEnum
    is_diagnostic: bool = False
    error_type_targeted: Optional[ErrorTypeEnum] = None
    content_json: Dict[str, Any]  # Flexible JSON structure
    explanation: Optional[str] = None
    is_active: bool = True

class AdminExerciseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    exercise_type: Optional[ExerciseTypeEnum] = None
    is_diagnostic: Optional[bool] = None
    error_type_targeted: Optional[ErrorTypeEnum] = None
    content_json: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    is_active: Optional[bool] = None

class AdminExerciseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    module_id: int
    sequence_id: int
    concept_id: int
    difficulty: str
    exercise_type: str
    is_diagnostic: bool
    error_type_targeted: Optional[str]
    is_active: bool
    created_by_admin_id: Optional[int]
    created_at: str
    attempt_count: int = 0
    success_rate: float = 0.0

# =============================================================================
# ADMIN LOG MODELS
# =============================================================================
class AdminLogResponse(BaseModel):
    id: int
    admin_id: int
    admin_username: str
    action_type: str
    entity: str
    entity_id: Optional[int]
    target_user_id: Optional[int]
    details: Optional[Dict] = None
    timestamp: str

class AdminLogCreate(BaseModel):
    action_type: AdminActionEnum
    entity: str
    entity_id: Optional[int] = None
    target_user_id: Optional[int] = None
    details: Optional[Dict] = None

# =============================================================================
# ADMIN ANALYTICS MODELS
# =============================================================================
class ConceptMasteryStats(BaseModel):
    concept_id: int
    concept_name: str
    average_mastery: float
    students_with_weakness: int
    students_with_strength: int
    total_attempts: int
    success_rate: float

class ErrorTypeStats(BaseModel):
    error_type: str
    frequency: int
    student_count: int
    concepts_affected: List[int]
    avg_difficulty: float

class AdminAnalyticsResponse(BaseModel):
    total_students: int
    total_exercises: int
    admin_created_exercises: int
    ai_generated_exercises: int
    average_student_mastery: float
    weakest_concepts: List[ConceptMasteryStats]
    most_common_errors: List[ErrorTypeStats]
    diagnostic_completion_rate: float
    timestamp: str

# =============================================================================
# DIAGNOSTIC MANAGEMENT MODELS
# =============================================================================
class AdminDiagnosticCreate(BaseModel):
    sequence_id: int
    question_ids: List[int]  # List of exercise IDs to use as diagnostic
    is_auto_generated: bool = False
    description: Optional[str] = None

class AdminDiagnosticResponse(BaseModel):
    id: int
    sequence_id: int
    total_questions: int
    created_by_admin_id: Optional[int]
    is_auto_generated: bool
    created_at: str

# =============================================================================
# EXERCISE TEMPLATE MODELS
# =============================================================================
class ExerciseTemplateCreate(BaseModel):
    name: str
    exercise_type: ExerciseTypeEnum
    content_json: Dict[str, Any]
    description: Optional[str] = None

class ExerciseTemplateResponse(BaseModel):
    id: int
    name: str
    exercise_type: str
    content_json: Dict[str, Any]
    description: Optional[str]
    created_by_admin_id: int
    created_at: str

# =============================================================================
# JWT & AUTH MODELS
# =============================================================================
class TokenPayload(BaseModel):
    sub: str  # username
    student_id: int
    role: str
    iat: int
    exp: int

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int

# =============================================================================
# DASHBOARD MODELS
# =============================================================================
class AdminDashboardResponse(BaseModel):
    total_students: int
    active_students: int
    total_exercises: int
    admin_exercises_count: int
    recent_logs: List[AdminLogResponse]
    student_mastery_distribution: Dict[str, int]  # "excellent", "good", "weak"
    most_practiced_concepts: List[Dict]
    timestamp: str
