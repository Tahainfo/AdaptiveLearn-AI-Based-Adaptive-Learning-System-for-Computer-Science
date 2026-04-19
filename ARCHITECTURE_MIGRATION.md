# FastAPI Adaptive Learning System - Curriculum Architecture Migration

**Status:** Ready for Implementation  
**Compatibility:** ✅ Zero Breaking Changes  
**Complexity:** Medium (Extending, not rebuilding)

---

## 🏗️ CURRENT STATE ANALYSIS

### What You Have (PROTECTED)
```
✅ students (with auth)
✅ concepts (foundational)
✅ mastery_state (per student + concept)
✅ exercise_attempts (with scoring)
✅ mistakes_log (error patterns)
✅ diagnostic_attempts (per concept)
✅ exercises (AI-generated)
✅ AI Engine (Claude Haiku integration)
✅ Recommendation Engine (concept-based)
✅ Student Model Service (mastery tracking)
```

### What Needs Extension (NON-BREAKING)
```
➕ modules table (new)
➕ sequences table (new)
🔄 concepts.sequence_id (FK - nullable for backward compatibility)
🔄 diagnostic_attempts.sequence_id (nullable - new column)
🔄 diagnostic_attempts.concept_breakdown (JSON - new column)
🔄 Recommendation logic (extend, don't replace)
🔄 Analytics endpoints (add aggregation queries)
```

---

## 📊 DATABASE MIGRATION STRATEGY

### Phase 1: Add New Tables (Non-Breaking)

```sql
-- NEW TABLE: Modules
CREATE TABLE modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE NOT NULL,
    description TEXT,
    order_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NEW TABLE: Sequences
CREATE TABLE sequences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    order_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(id),
    UNIQUE(module_id, title)
);

-- EXISTING TABLE: Concepts (MODIFY)
-- ADD COLUMN: sequence_id (nullable for backward compat)
ALTER TABLE concepts ADD COLUMN sequence_id INTEGER REFERENCES sequences(id);

-- EXISTING TABLE: diagnostic_attempts (MODIFY)
-- ADD COLUMNS: sequence_id and concept_breakdown
ALTER TABLE diagnostic_attempts ADD COLUMN sequence_id INTEGER REFERENCES sequences(id);
ALTER TABLE diagnostic_attempts ADD COLUMN concept_breakdown TEXT; -- JSON
```

### Phase 2: Insert Curriculum Data

```python
# backend/database/migrations.py
MOROCCAN_CURRICULUM = [
    {
        "module": "Généralités sur les systèmes informatiques",
        "sequences": [
            {
                "name": "Définitions et vocabulaire de base",
                "concepts": ["Définition de l'information", "Définition du traitement", 
                           "Définition de l'informatique", "Définition du système informatique"]
            },
            {
                "name": "Structure de base d'un ordinateur",
                "concepts": ["Schéma fonctionnel d'un ordinateur", "Périphériques", 
                           "Unité centrale de traitement"]
            },
            # ... etc
        ]
    },
    # ... 3 more modules
]
```

### Phase 3: Migrate Existing Data

**Key Rule:** Concepts without sequence_id still work (backward compatible).

```python
# Auto-map existing concepts to Algorithmique module if domain matches
cursor.execute("""
    UPDATE concepts 
    SET sequence_id = (
        SELECT s.id FROM sequences s 
        WHERE s.module_id = 3  -- Algorithmique module
        LIMIT 1
    )
    WHERE domain = 'Algorithmics' AND sequence_id IS NULL
""")
```

---

## 🎯 HIERARCHY STRUCTURE

```
Module (4 total)
├── Sequence (13 total)
│   ├── Concept (39 total) ← Existing mastery tracking continues
│   ├── Concept
│   └── Concept
├── Sequence
│   ├── Concept
│   └── Concept
└── [...]

🔗 Relationships:
- 1 Module → N Sequences
- 1 Sequence → N Concepts
- 1 Student → N Mastery States (per Concept)
- 1 Diagnostic → 1 Sequence OR 1 Concept (polymorphic)
```

---

## 🔄 UPDATED PYDANTIC MODELS

### Add to `backend/models/database_models.py`

```python
from typing import Dict, List, Optional
from pydantic import BaseModel

# ===== CURRICULUM MODELS =====

class ConceptInSequence(BaseModel):
    id: int
    name: str
    domain: str
    description: Optional[str]
    mastery_level: Optional[float] = None
    hours: Optional[int] = None

class SequenceResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    module_id: int
    concepts: List[ConceptInSequence] = []
    average_mastery: Optional[float] = None
    diagnostic_completed: Optional[bool] = None

class ModuleResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    sequences: List[SequenceResponse] = []
    average_mastery: Optional[float] = None

class SequenceDiagnosticResult(BaseModel):
    sequence_id: int
    sequence_name: str
    score: float
    concept_breakdown: Dict[str, float]  # {concept_name: score}
    average_mastery: float
    timestamp: str

class DiagnosticAnswer(BaseModel):
    """Support both concept and sequence diagnostics"""
    question_id: int
    selected_index: int
    concept_id: int  # Always map to concept, even for sequence tests

class DiagnosticTestRequest(BaseModel):
    answers: List[DiagnosticAnswer]
    sequence_id: Optional[int] = None  # If sequence-based diagnostic
```

---

## 🛣️ NEW API ENDPOINTS

### Curriculum Discovery Routes

```python
# backend/routes/curriculum.py (NEW FILE)

router = APIRouter(prefix="/curriculum", tags=["curriculum"])

@router.get("/modules", tags=["discovery"])
async def get_all_modules(authorization: Optional[str] = Header(None)):
    """
    GET /curriculum/modules
    Returns: List[ModuleResponse] with sequences and mastery
    """
    student_id = get_current_student(authorization)
    # Query modules + sequences + calculate avg mastery per sequence
    
@router.get("/modules/{module_id}")
async def get_module_detail(
    module_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    GET /curriculum/modules/3
    Returns: ModuleResponse with full sequence tree + student mastery
    """
    student_id = get_current_student(authorization)

@router.get("/sequences/{sequence_id}")
async def get_sequence_detail(
    sequence_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    GET /curriculum/sequences/5
    Returns: SequenceResponse with concepts + mastery per concept
    """
    student_id = get_current_student(authorization)

@router.get("/sequences/{sequence_id}/mastery")
async def get_sequence_mastery(
    sequence_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    GET /curriculum/sequences/5/mastery
    Returns: {
        sequence_name: str,
        average_mastery: float,
        concept_mastery: Dict[str, float],
        diagnostic_status: "not_started" | "in_progress" | "completed"
    }
    """
    student_id = get_current_student(authorization)
```

### Sequence-Based Diagnostic Routes

```python
# backend/routes/diagnostic.py (EXTEND EXISTING FILE)

@router.get("/sequence/{sequence_id}/questions")
async def get_sequence_diagnostic_questions(
    sequence_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    GET /diagnostic/sequence/5/questions
    Returns: List of questions covering ALL concepts in sequence
    
    Response: [
        {
            "id": 1,
            "concept_id": 10,
            "concept_name": "Loops",
            "question": "...",
            "options": [...],
            "correct_index": 2
        },
        ...
    ]
    """
    student_id = get_current_student(authorization)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all concepts in sequence
    cursor.execute("""
        SELECT id, name FROM concepts WHERE sequence_id = ? ORDER BY id
    """, (sequence_id,))
    concepts = cursor.fetchall()
    
    all_questions = []
    for concept_id, concept_name in concepts:
        questions = get_diagnostic_questions(concept_name)
        for q in questions:
            q['concept_id'] = concept_id
            q['concept_name'] = concept_name
            all_questions.append(q)
    
    return all_questions

@router.post("/sequence/submit")
async def submit_sequence_diagnostic(
    test_data: DiagnosticTestRequest,
    authorization: Optional[str] = Header(None)
):
    """
    POST /diagnostic/sequence/submit
    
    Request: {
        "sequence_id": 5,
        "answers": [
            {"question_id": 0, "selected_index": 2, "concept_id": 10},
            ...
        ]
    }
    
    Returns: SequenceDiagnosticResult with:
    - Overall sequence score
    - Per-concept breakdown
    - Updates mastery_state for each concept
    - Creates diagnostic_attempts record with concept_breakdown JSON
    """
    student_id = get_current_student(authorization)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Group answers by concept
    concept_scores = {}
    for answer in test_data.answers:
        if answer.concept_id not in concept_scores:
            concept_scores[answer.concept_id] = {'correct': 0, 'total': 0}
        
        concept_scores[answer.concept_id]['total'] += 1
        # Check if correct (compare with question bank)
        if is_answer_correct(answer):
            concept_scores[answer.concept_id]['correct'] += 1
    
    # Calculate scores and update mastery per concept
    concept_breakdown = {}
    for concept_id, scores in concept_scores.items():
        score = (scores['correct'] / scores['total']) * 100 if scores['total'] > 0 else 0
        concept_breakdown[concept_id] = score
        
        # Update mastery_state for this concept
        cursor.execute("""
            INSERT OR REPLACE INTO mastery_state
            (student_id, concept_id, mastery_level, ...)
            VALUES (?, ?, ?, ...)
        """, (student_id, concept_id, score / 100.0, ...))
    
    # Store diagnostic attempt with breakdown
    avg_score = sum(concept_breakdown.values()) / len(concept_breakdown)
    cursor.execute("""
        INSERT INTO diagnostic_attempts
        (student_id, sequence_id, score, concept_breakdown, answers)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, test_data.sequence_id, avg_score, 
          json.dumps(concept_breakdown), json.dumps([...])))
    
    conn.commit()
    
    return SequenceDiagnosticResult(...)
```

---

## 🧠 UPDATED RECOMMENDATION ENGINE

### Extend `backend/services/recommendation.py`

**Key Change:** Detect weakest *sequence* first, then weakest *concept* within that sequence.

```python
class RecommendationEngine:
    def get_next_recommendation(self, student_id: int) -> Dict:
        """
        UPDATED: Now sequence-aware
        
        Algorithm:
        1. Calculate average mastery per sequence
        2. Find weakest sequence
        3. Within that sequence, find weakest concept
        4. Return exercise for that concept
        """
        cursor = self.db.cursor()
        
        # NEW: Calculate sequence mastery first
        cursor.execute("""
            SELECT 
                s.id,
                s.title,
                AVG(m.mastery_level) as seq_mastery
            FROM sequences s
            LEFT JOIN concepts c ON c.sequence_id = s.id
            LEFT JOIN mastery_state m ON m.concept_id = c.id 
                AND m.student_id = ?
            GROUP BY s.id
            ORDER BY seq_mastery ASC
        """, (student_id,))
        
        sequences = cursor.fetchall()
        
        # Find weakest sequence
        weakest_sequence = sequences[0] if sequences else None
        
        if weakest_sequence:
            sequence_id, sequence_name, seq_mastery = weakest_sequence
            
            # Within this sequence, find weakest concept
            cursor.execute("""
                SELECT c.id, c.name, m.mastery_level, m.attempts_count
                FROM concepts c
                LEFT JOIN mastery_state m ON m.concept_id = c.id 
                    AND m.student_id = ?
                WHERE c.sequence_id = ?
                ORDER BY COALESCE(m.mastery_level, 0) ASC
            """, (student_id, sequence_id))
            
            weakest_concept = cursor.fetchone()
            
            return {
                "action": "practice_exercise",
                "concept_id": weakest_concept[0],
                "concept_name": weakest_concept[1],
                "sequence_id": sequence_id,
                "sequence_name": sequence_name,
                "priority": "high",
                "reason": f"Focus on sequence '{sequence_name}' - concept '{weakest_concept[1]}' needs work"
            }
        
        # Fallback to existing concept-based logic
        return self._get_concept_based_recommendation(student_id)
    
    def _get_concept_based_recommendation(self, student_id: int) -> Dict:
        """Existing logic - unchanged"""
        # ... original code ...
        pass
```

---

## 📈 UPDATED ANALYTICS

### Add to `backend/routes/analytics.py`

```python
@router.get("/dashboard/curriculum")
async def get_curriculum_analytics(authorization: Optional[str] = Header(None)):
    """
    GET /analytics/dashboard/curriculum
    
    NEW Endpoint: Curriculum-scoped analytics
    
    Returns: {
        "modules": [
            {
                "module_name": "Algorithmique et programmation",
                "mastery": 0.65,
                "sequences": [
                    {
                        "sequence_name": "Loops",
                        "mastery": 0.70,
                        "concepts": [
                            {"name": "For Loop", "mastery": 0.80},
                            {"name": "While Loop", "mastery": 0.60}
                        ]
                    }
                ]
            }
        ],
        "overall_mastery": 0.58,
        "diagnostic_completion": {
            "total_sequences": 13,
            "completed": 3,
            "in_progress": 1
        }
    }
    """
    student_id = get_current_student(authorization)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query: Mastery aggregation per module/sequence/concept
    cursor.execute("""
        SELECT 
            m.id,
            m.title,
            AVG(COALESCE(ms.mastery_level, 0)) as module_mastery,
            COUNT(DISTINCT s.id) as sequence_count,
            COUNT(DISTINCT c.id) as concept_count
        FROM modules m
        LEFT JOIN sequences s ON s.module_id = m.id
        LEFT JOIN concepts c ON c.sequence_id = s.id
        LEFT JOIN mastery_state ms ON ms.concept_id = c.id 
            AND ms.student_id = ?
        GROUP BY m.id
    """, (student_id,))
    
    # Build hierarchy...
    return analytics_structure
```

---

## 🔌 INTEGRATION CHECKLIST

### ✅ DO NOT TOUCH
- `exercise_attempts` logic
- `mistakes_log` error classification
- `AI Engine` generation (keep as-is)
- `StudentModel` mastery calculations
- Existing diagnostic routes (keep `/diagnostic/submit/{concept_id}`)

### 🔄 EXTEND (Non-Breaking)
- Add `POST /diagnostic/sequence/submit`
- Add `/curriculum/*` routes
- Extend `RecommendationEngine` (add method, don't replace)
- Add new analytics aggregation queries

### ⚠️ BACKWARD COMPATIBILITY
```python
# Existing routes still work:
POST /diagnostic/submit/{concept_id}  ← Still functional
GET /diagnostic/concepts              ← Still functional

# New routes added:
POST /diagnostic/sequence/submit      ← New sequence support
GET /curriculum/modules               ← New curriculum navigation
GET /curriculum/modules/{id}          ← New module details
```

---

## 🚀 MIGRATION EXECUTION PLAN

### Step 1: Database (5 minutes)
```python
# backend/database/migrations.py
def migrate_to_curriculum():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Run Phase 1 & 2 SQL
    # Insert curriculum data
    # Auto-migrate existing concepts
    
    conn.commit()
```

### Step 2: Models (10 minutes)
- Add new Pydantic models to `database_models.py`
- Keep existing models unchanged

### Step 3: Routes (20 minutes)
- Create `backend/routes/curriculum.py` (new)
- Extend `backend/routes/diagnostic.py` (add new endpoint)
- Extend `backend/routes/analytics.py` (add aggregations)

### Step 4: Services (15 minutes)
- Extend `RecommendationEngine.get_next_recommendation()`
- Add helper method for sequence-based logic

### Step 5: Frontend (30 minutes)
- Add `/curriculum/modules` API call
- Add module/sequence cards to dashboard
- Add sequence diagnostic modal
- Keep existing diagnostic UI (don't remove)

### Step 6: Testing (20 minutes)
- Test existing diagnostic still works
- Test new sequence diagnostic
- Test recommendation engine picks weakest sequence
- Verify mastery calculations unchanged

---

## 📐 CODE ORGANIZATION

```
backend/
├── routes/
│   ├── curriculum.py          ← NEW (module/sequence discovery)
│   ├── diagnostic.py          ← EXTEND (add sequence diagnostic)
│   └── analytics.py           ← EXTEND (add curriculum aggregations)
├── services/
│   ├── recommendation.py      ← EXTEND (sequence-aware logic)
│   └── ai_engine.py           ← NO CHANGE
├── models/
│   └── database_models.py     ← ADD models (keep existing)
└── database/
    ├── db.py                  ← EXTEND schema
    └── migrations.py          ← NEW (curriculum data)
```

---

## 🎯 VALIDATION RULES

### Database Integrity
```sql
-- Verify no orphaned concepts
SELECT c.* FROM concepts c 
WHERE c.sequence_id IS NOT NULL 
AND c.sequence_id NOT IN (SELECT id FROM sequences);

-- Verify mastery tracking still works
SELECT COUNT(*) FROM mastery_state; -- Should have data
```

### Logic Verification
```python
# Recommendation picks sequence correctly
rec = engine.get_next_recommendation(student_id)
assert 'sequence_id' in rec or rec['reason'].contains('concept-based')

# Sequence diagnostic updates mastery
submit_sequence_diagnostic(...)
assert mastery_state updated for each concept
assert diagnostic_attempts has concept_breakdown JSON
```

---

## ⏱️ TOTAL IMPLEMENTATION TIME
- **Database:** 5 min
- **Models:** 10 min
- **API Routes:** 35 min
- **Services:** 15 min
- **Frontend:** 30 min
- **Testing:** 20 min

**Total: ~2 hours for solo developer**

---

## 🎓 KEY PRINCIPLES

✅ **Layered Addition:** New code sits beside old, no replacements  
✅ **Backward Compatible:** Existing routes untouched  
✅ **AI Preserved:** No changes to Claude integration  
✅ **Mastery Logic:** Untouched, only extended  
✅ **Zero Data Loss:** Migration preserves all existing records  
✅ **Atomic Operations:** Each transaction self-contained  

---

## 📞 TROUBLESHOOTING

**Issue:** "Concepts without sequence_id"
**Solution:** They still work! Backward compatible. Set default sequence or add to migration.

**Issue:** "Old diagnostic routes return wrong data"
**Solution:** They don't! Concept-based diagnostics unaffected. New sequence diagnostics run in parallel.

**Issue:** "Recommendation engine slow"
**Solution:** Add indexes on `sequences(module_id)`, `concepts(sequence_id)`, `mastery_state(student_id, concept_id)`.

---

**Status:** ✅ Ready to implement  
**Risk Level:** 🟢 LOW (Extending, not refactoring)  
**Data Safety:** 🟢 FULL (Backward compatible)
