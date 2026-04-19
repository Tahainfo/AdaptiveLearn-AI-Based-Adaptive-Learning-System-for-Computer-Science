# 🚀 Curriculum Migration - Implementation Checklist

**Project:** Adaptive Learning System → Curriculum-Aware Adaptive Learning System  
**Scope:** Non-breaking extension of existing FastAPI backend  
**Estimated Time:** 2-3 hours  
**Risk Level:** 🟢 LOW (Backward compatible)

---

## ✅ PRE-IMPLEMENTATION VALIDATION

### Database State Check
```bash
# Run this to verify existing data:
python -c "
from backend.database.db import get_db_connection
conn = get_db_connection()
cursor = conn.cursor()

# These tables should exist:
for table in ['students', 'concepts', 'mastery_state', 'exercises', 'exercise_attempts', 'mistakes_log', 'diagnostic_attempts']:
    cursor.execute(f\"SELECT COUNT(*) FROM {table}\")
    count = cursor.fetchone()[0]
    print(f'✓ {table}: {count} records')

conn.close()
"
```

**Expected Output:**
```
✓ students: X records
✓ concepts: X records
✓ mastery_state: X records
✓ exercises: X records
✓ exercise_attempts: X records
✓ mistakes_log: X records
✓ diagnostic_attempts: X records
```

---

## 📋 IMPLEMENTATION PHASE 1: DATABASE (5 minutes)

### Task 1.1: Add Curriculum Tables
**File:** `backend/database/db.py`

Add this to the `init_db()` function (after concepts table, before mastery_state):

```python
# Modules table (after concepts, before mastery_state)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS modules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT UNIQUE NOT NULL,
        description TEXT,
        order_index INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Sequences table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sequences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        order_index INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (module_id) REFERENCES modules(id),
        UNIQUE(module_id, title)
    )
""")
```

### Task 1.2: Migrate Concepts Table
**File:** `backend/database/db.py`

Update concepts table to add sequence_id:

```python
# Modify existing concepts table definition
cursor.execute("""
    CREATE TABLE IF NOT EXISTS concepts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sequence_id INTEGER,
        name TEXT NOT NULL,
        domain TEXT NOT NULL,
        description TEXT,
        hours INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sequence_id) REFERENCES sequences(id),
        UNIQUE(sequence_id, name)
    )
""")
```

### Task 1.3: Extend Diagnostic Attempts Table
**File:** `backend/database/db.py`

Add sequence_id and concept_breakdown columns:

```python
# Add columns to diagnostic_attempts (via ALTER TABLE in migration)
# Note: SQLite doesn't support ALTER TABLE ADD COLUMN for complex types easily
# Solution: Create migration helper

# backend/database/migrations.py (NEW FILE)
def migrate_add_curriculum():
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Add sequence_id column
    try:
        cursor.execute("ALTER TABLE diagnostic_attempts ADD COLUMN sequence_id INTEGER REFERENCES sequences(id)")
        print("✓ Added sequence_id to diagnostic_attempts")
    except sqlite3.OperationalError:
        print("! sequence_id already exists")
    
    # Add concept_breakdown column (JSON)
    try:
        cursor.execute("ALTER TABLE diagnostic_attempts ADD COLUMN concept_breakdown TEXT")
        print("✓ Added concept_breakdown to diagnostic_attempts")
    except sqlite3.OperationalError:
        print("! concept_breakdown already exists")
    
    conn.commit()
    conn.close()
```

### Task 1.4: Insert Moroccan Curriculum Data
**File:** `backend/database/db.py` (Add to end of file)

```python
def insert_moroccan_curriculum():
    """
    Insert official Moroccan Tronc Commun curriculum
    4 Modules → 13 Sequences → 39 Concepts
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    curriculum = [
        {
            "module": "Généralités sur les systèmes informatiques",
            "sequences": [
                {
                    "title": "Définitions et vocabulaire de base",
                    "concepts": ["Définition de l'information", "Définition du traitement",
                               "Définition de l'informatique", "Définition du système informatique"]
                },
                # ... rest of data from ARCHITECTURE_MIGRATION.md
            ]
        },
        # ... 3 more modules
    ]
    
    for module_order, module_data in enumerate(curriculum, 1):
        # Insert module
        try:
            cursor.execute(
                "INSERT INTO modules (title, description, order_index) VALUES (?, ?, ?)",
                (module_data["module"], f"Tronc Commun", module_order)
            )
            module_id = cursor.lastrowid
            
            # Insert sequences
            for seq_order, sequence_data in enumerate(module_data["sequences"], 1):
                try:
                    cursor.execute(
                        "INSERT INTO sequences (module_id, title, order_index) VALUES (?, ?, ?)",
                        (module_id, sequence_data["title"], seq_order)
                    )
                    sequence_id = cursor.lastrowid
                    
                    # Link concepts to sequence
                    for concept_name in sequence_data["concepts"]:
                        # Update existing concept if it exists
                        cursor.execute(
                            "UPDATE concepts SET sequence_id = ? WHERE name = ?",
                            (sequence_id, concept_name)
                        )
                        # Or insert if new
                        if cursor.rowcount == 0:
                            cursor.execute(
                                "INSERT INTO concepts (sequence_id, name, domain) VALUES (?, ?, ?)",
                                (sequence_id, concept_name, module_data["module"])
                            )
                except sqlite3.IntegrityError as e:
                    print(f"⚠ Sequence duplicate: {e}")
        except sqlite3.IntegrityError as e:
            print(f"⚠ Module duplicate: {e}")
    
    conn.commit()
    conn.close()
    print("✅ Moroccan curriculum inserted")

# Run in main.py startup
if __name__ == "__main__":
    init_db()
    insert_moroccan_curriculum()  # Add this
```

### ✅ Validation
```bash
# Check database after Phase 1
python -c "
from backend.database.db import get_db_connection
conn = get_db_connection()
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM modules')
print(f'Modules: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM sequences')
print(f'Sequences: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM concepts WHERE sequence_id IS NOT NULL')
print(f'Concepts with sequences: {cursor.fetchone()[0]}')

conn.close()
"
```

**Expected:** Modules: 4, Sequences: 13, Concepts: 39

---

## 📝 IMPLEMENTATION PHASE 2: MODELS (10 minutes)

### Task 2.1: Add Curriculum Models
**File:** `backend/models/database_models.py`

Add these imports at top:
```python
from enum import Enum
import json
```

Add new models:
```python
# ===== CURRICULUM MODELS =====

class ConceptInSequence(BaseModel):
    id: int
    name: str
    domain: str
    description: Optional[str] = None
    hours: Optional[int] = None
    mastery_level: Optional[float] = None  # Will be filled by API

class SequenceResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    module_id: int
    concepts: List[ConceptInSequence] = []
    average_mastery: Optional[float] = None
    concept_count: int = 0

class ModuleResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    sequences: List[SequenceResponse] = []
    average_mastery: Optional[float] = None
    sequence_count: int = 0

class SequenceDiagnosticResult(BaseModel):
    sequence_id: int
    sequence_name: str
    score: float
    average_mastery: float
    concept_breakdown: Dict[str, float]  # {concept_name: score}
    timestamp: str

class SequenceMasteryProfile(BaseModel):
    sequence_id: int
    sequence_name: str
    average_mastery: float
    concept_count: int
    concepts: List[Dict] = []
```

Update existing DiagnosticAnswer:
```python
class DiagnosticAnswer(BaseModel):
    question_id: int
    selected_index: int
    concept_id: int  # Always linked to concept

# DiagnosticTestRequest stays same
```

---

## 🛣️ IMPLEMENTATION PHASE 3: NEW ROUTES (30 minutes)

### Task 3.1: Create Curriculum Routes
**File:** `backend/routes/curriculum.py` (NEW FILE)

```python
"""
Curriculum Routes - Module and Sequence Discovery
Non-breaking addition to existing API
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional, List
from backend.models.database_models import ModuleResponse, SequenceResponse
from backend.routes.auth import get_current_student
from backend.database.db import get_db_connection

router = APIRouter(prefix="/curriculum", tags=["curriculum"])

@router.get("/modules")
async def get_all_modules(authorization: Optional[str] = Header(None)):
    """
    GET /curriculum/modules
    Returns all 4 modules with sequences
    """
    student_id = get_current_student(authorization)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, description, order_index
        FROM modules
        ORDER BY order_index
    """)
    
    modules = []
    for module_row in cursor.fetchall():
        module_id = module_row[0]
        
        # Get sequences for this module
        cursor.execute("""
            SELECT id, title, description, order_index
            FROM sequences
            WHERE module_id = ?
            ORDER BY order_index
        """, (module_id,))
        
        sequences = []
        for seq_row in cursor.fetchall():
            seq_id = seq_row[0]
            
            # Get concepts for this sequence
            cursor.execute("""
                SELECT c.id, c.name, c.domain, c.description, c.hours,
                       COALESCE(m.mastery_level, 0) as mastery
                FROM concepts c
                LEFT JOIN mastery_state m ON m.concept_id = c.id 
                    AND m.student_id = ?
                WHERE c.sequence_id = ?
            """, (student_id, seq_id))
            
            concepts = [
                {
                    "id": c[0],
                    "name": c[1],
                    "domain": c[2],
                    "description": c[3],
                    "hours": c[4],
                    "mastery_level": c[5]
                }
                for c in cursor.fetchall()
            ]
            
            avg_mastery = sum(c['mastery_level'] for c in concepts) / len(concepts) if concepts else 0
            
            sequences.append({
                "id": seq_id,
                "title": seq_row[1],
                "description": seq_row[2],
                "order_index": seq_row[3],
                "concepts": concepts,
                "average_mastery": round(avg_mastery, 3),
                "concept_count": len(concepts)
            })
        
        avg_seq_mastery = sum(s['average_mastery'] for s in sequences) / len(sequences) if sequences else 0
        
        modules.append({
            "id": module_id,
            "title": module_row[1],
            "description": module_row[2],
            "sequences": sequences,
            "average_mastery": round(avg_seq_mastery, 3),
            "sequence_count": len(sequences)
        })
    
    conn.close()
    return modules

@router.get("/modules/{module_id}")
async def get_module_detail(
    module_id: int,
    authorization: Optional[str] = Header(None)
):
    """GET /curriculum/modules/1"""
    student_id = get_current_student(authorization)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, description FROM modules WHERE id = ?", (module_id,))
    module = cursor.fetchone()
    
    if not module:
        conn.close()
        raise HTTPException(status_code=404, detail="Module not found")
    
    # Get sequences with concepts (same logic as above)
    # ... reuse code structure ...
    
    conn.close()
    return module_detail

@router.get("/sequences/{sequence_id}")
async def get_sequence_detail(
    sequence_id: int,
    authorization: Optional[str] = Header(None)
):
    """GET /curriculum/sequences/5"""
    student_id = get_current_student(authorization)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, title, module_id FROM sequences WHERE id = ?", 
        (sequence_id,)
    )
    seq = cursor.fetchone()
    
    if not seq:
        conn.close()
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    cursor.execute("""
        SELECT c.id, c.name, c.domain, COALESCE(m.mastery_level, 0)
        FROM concepts c
        LEFT JOIN mastery_state m ON m.concept_id = c.id AND m.student_id = ?
        WHERE c.sequence_id = ?
    """, (student_id, sequence_id))
    
    concepts = cursor.fetchall()
    conn.close()
    
    return {
        "id": seq[0],
        "title": seq[1],
        "module_id": seq[2],
        "concepts": [
            {"id": c[0], "name": c[1], "domain": c[2], "mastery_level": c[3]}
            for c in concepts
        ]
    }
```

### Task 3.2: Extend Diagnostic Routes
**File:** `backend/routes/diagnostic.py`

Add new endpoint for sequence-based diagnostic:

```python
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
            {"question_id": 0, "selected_index": 2, "concept_id": 10}
        ]
    }
    
    Calculate per-concept scores and update mastery
    """
    student_id = get_current_student(authorization)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Group answers by concept
    concept_scores = {}
    for answer in test_data.answers:
        cid = answer.concept_id
        if cid not in concept_scores:
            concept_scores[cid] = {'correct': 0, 'total': 0}
        
        concept_scores[cid]['total'] += 1
        
        # Check correctness
        questions = get_diagnostic_questions_for_concept(cid)
        if questions and answer.question_id < len(questions):
            if questions[answer.question_id].get('correct_index') == answer.selected_index:
                concept_scores[cid]['correct'] += 1
    
    # Update mastery per concept and track breakdown
    concept_breakdown = {}
    for cid, scores in concept_scores.items():
        score = (scores['correct'] / scores['total'] * 100) if scores['total'] > 0 else 0
        mastery = score / 100.0
        concept_breakdown[str(cid)] = score
        
        # Update mastery_state
        cursor.execute("""
            INSERT OR REPLACE INTO mastery_state
            (student_id, concept_id, mastery_level, attempts_count, correct_count)
            VALUES (?, ?, ?, 1, ?)
        """, (student_id, cid, mastery, scores['correct']))
    
    # Store diagnostic attempt with breakdown
    avg_score = sum(concept_breakdown.values()) / len(concept_breakdown) if concept_breakdown else 0
    
    cursor.execute("""
        INSERT INTO diagnostic_attempts
        (student_id, sequence_id, score, concept_breakdown)
        VALUES (?, ?, ?, ?)
    """, (student_id, test_data.sequence_id, avg_score, json.dumps(concept_breakdown)))
    
    conn.commit()
    conn.close()
    
    return {
        "sequence_id": test_data.sequence_id,
        "score": round(avg_score, 2),
        "concept_breakdown": concept_breakdown
    }
```

### Task 3.3: Include in Main
**File:** `backend/main.py`

Add import:
```python
from backend.routes.curriculum import router as curriculum_router
```

Include router in app:
```python
app.include_router(curriculum_router)
```

---

## 🧠 IMPLEMENTATION PHASE 4: SERVICES (15 minutes)

### Task 4.1: Extend Recommendation Engine
**File:** `backend/services/recommendation.py`

**✅ ALREADY DONE** - The sequence-aware methods are in place:
- `get_sequence_aware_recommendation()` - New curriculum-aware recommendation
- `get_sequence_mastery_profile()` - Get mastery by sequence
- `should_start_sequence_diagnostic()` - Check if diagnostic should be taken

The existing `get_next_recommendation()` remains **unchanged** for backward compatibility.

### Task 4.2: Use Sequence-Aware Recommendation
**File:** `backend/routes/exercise.py`

When recommending next exercise, choose which recommendation engine to use:

```python
from backend.services.recommendation import RecommendationEngine

@router.get("/next-exercise")
async def get_next_exercise(authorization: Optional[str] = Header(None)):
    student_id = get_current_student(authorization)
    conn = get_db_connection()
    
    # Use sequence-aware recommendation (new)
    engine = RecommendationEngine(conn)
    recommendation = engine.get_sequence_aware_recommendation(student_id)
    
    # If no sequence found, fallback to concept-based (old)
    if not recommendation.get('sequence_id'):
        recommendation = engine.get_next_recommendation(student_id)
    
    # Generate exercise based on recommendation
    concept_id = recommendation['concept_id']
    # ... rest of exercise generation ...
```

---

## 📊 IMPLEMENTATION PHASE 5: ANALYTICS (10 minutes)

### Task 5.1: Add Curriculum Dashboard Endpoint
**File:** `backend/routes/analytics.py`

```python
@router.get("/curriculum/dashboard")
async def get_curriculum_analytics(authorization: Optional[str] = Header(None)):
    """
    GET /analytics/curriculum/dashboard
    
    Returns curriculum-scoped analytics
    """
    student_id = get_current_student(authorization)
    conn = get_db_connection()
    
    engine = RecommendationEngine(conn)
    profile = engine.get_sequence_mastery_profile(student_id)
    
    # Add diagnostic status
    for seq in profile:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM diagnostic_attempts WHERE student_id = ? AND sequence_id = ?",
            (student_id, seq['sequence_id'])
        )
        seq['diagnostic_completed'] = cursor.fetchone()[0] > 0
    
    conn.close()
    return {"sequences_profile": profile}
```

---

## 🖥️ IMPLEMENTATION PHASE 6: FRONTEND (30 minutes)

### Task 6.1: Update Dashboard to Show Modules
**File:** `frontend/js/app.js`

Add module loading:
```javascript
async function loadModules() {
    const modules = await api.getAllModules();
    
    const html = modules.map(module => `
        <div class="module-card" onclick="showModule(${module.id})">
            <h3>${module.title}</h3>
            <p>${module.sequence_count} sequences</p>
            <div class="progress" style="width: ${module.average_mastery * 100}%"></div>
        </div>
    `).join('');
    
    document.getElementById('modulesList').innerHTML = html;
}

async function showModule(moduleId) {
    const module = await api.getModuleDetails(moduleId);
    // Show modal with sequences...
}
```

### Task 6.2: Add Sequence Diagnostic Modal
**File:** `frontend/index.html`

```html
<div id="sequenceDiagnosticModal" class="modal" style="display:none;">
    <div class="modal-content">
        <h2 id="sequenceTitle"></h2>
        <div id="diagnosticQuestions"></div>
        <button onclick="submitSequenceDiagnostic()">Submit</button>
    </div>
</div>
```

---

## ✅ PHASE 7: VALIDATION & TESTING

### Test 1: Backward Compatibility
```bash
# Old diagnostic routes still work
curl http://localhost:8000/diagnostic/questions/1

# Old recommendations still work
curl http://localhost:8000/analytics/recommendations
```

### Test 2: New Curriculum Routes
```bash
# New curriculum routes work
curl http://localhost:8000/curriculum/modules
curl http://localhost:8000/curriculum/modules/1
curl http://localhost:8000/curriculum/sequences/5

# New sequence diagnostic works
curl -X POST http://localhost:8000/diagnostic/sequence/submit \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "sequence_id": 5,
    "answers": [
      {"question_id": 0, "selected_index": 2, "concept_id": 10}
    ]
  }'
```

### Test 3: Recommendation Engine
```python
from backend.services.recommendation import RecommendationEngine
from backend.database.db import get_db_connection

conn = get_db_connection()
engine = RecommendationEngine(conn)

# Old method still works
rec1 = engine.get_next_recommendation(student_id=1)
print("Concept-based:", rec1)

# New method works
rec2 = engine.get_sequence_aware_recommendation(student_id=1)
print("Sequence-aware:", rec2)

conn.close()
```

---

## 🎯 ROLLBACK PLAN (If Issues Arise)

### If Curriculum Routes Fail
```python
# Just remove from main.py:
# app.include_router(curriculum_router)
# Existing diagnostic/exercise routes continue working
```

### If Recommendation Engine Issues
```python
# Revert recommendation.py changes
# Edit routes/exercise.py to use old engine:
recommendation = engine.get_next_recommendation(student_id)
```

### If Database Issues
```python
# Existing tables unchanged
# New tables (modules, sequences) can be dropped
# Concepts table has backward-compatible migration
```

---

## 📈 SUCCESS METRICS

- ✅ All existing routes still work
- ✅ Old diagnostics per concept still function
- ✅ New curriculum routes respond
- ✅ Sequence diagnostics calculate per-concept scores
- ✅ Mastery updates correctly
- ✅ Recommendation engine picks weakest sequence first (when used)

---

## 📝 NOTES FOR SOLO DEVELOPER

1. **Database:** Run migration script once, then forget it
2. **Models:** Just add new classes, don't remove old ones
3. **Routes:** Create new file, include in main.py
4. **Services:** Extend, don't replace - add new methods
5. **Frontend:** Add new UI alongside old (both work)
6. **Testing:** Old system keeps working while new system added

This approach lets you add curriculum intelligence without touching any existing adaptive logic.

**Good luck! 🚀**
