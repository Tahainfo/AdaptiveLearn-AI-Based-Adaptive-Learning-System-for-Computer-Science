# 🏗 System Architecture Overview

## Project Structure

```
📁 Projet personnel/
├── README.md                 # Main documentation
├── QUICKSTART.md            # 5-minute setup guide  
├── DATABASE.md              # Database schema & operations
├── API.md                   # Complete API reference
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
│
├── 📁 backend/
│   ├── main.py              # FastAPI application entry point
│   ├── __init__.py
│   │
│   ├── 📁 routes/           # API endpoint definitions
│   │   ├── __init__.py
│   │   ├── auth.py          # /auth endpoints
│   │   ├── diagnostic.py    # /diagnostic endpoints
│   │   ├── exercise.py      # /exercise endpoints
│   │   └── analytics.py     # /analytics endpoints
│   │
│   ├── 📁 services/         # Business logic layer
│   │   ├── __init__.py
│   │   ├── student_model.py    # Mastery tracking algorithm
│   │   ├── error_analyzer.py   # Error classification logic
│   │   ├── ai_engine.py        # Claude API integration
│   │   └── recommendation.py   # Smart recommendations engine
│   │
│   ├── 📁 models/           # Data validation models
│   │   ├── __init__.py
│   │   └── database_models.py  # Pydantic schemas
│   │
│   ├── 📁 database/         # Database management
│   │   ├── __init__.py
│   │   └── db.py            # SQLite setup & schema
│   │
│   └── 📁 utils/            # Utility modules
│       ├── __init__.py
│       ├── prompts.py       # AI prompts & diagnostic questions
│       └── auth.py          # Token management
│
└── 📁 frontend/             # User interface
    ├── index.html           # Main HTML page
    ├── 📁 css/
    │   └── style.css        # Complete styling
    └── 📁 js/
        ├── config.js        # Configuration & helpers
        ├── api.js           # API client layer
        └── app.js           # Application logic & UI handlers
```

## 🔄 Data Flow

### User Flow
```
Registration → Login → Diagnostic Test → Dashboard View
    ↓           ↓            ↓              ↓
  Register   Authenticate   Score      View Progress
   Student    Generate       Based      View Next Steps
            Access Token   Student     Take Exercise
                          Profile
```

### Exercise Flow
```
Get Next Exercise → Display Exercise → Get Hints (Optional)
        ↓                   ↓                  ↓
  AI Engine         Student Reads        Progressive
  Generates      Understands Problem      Hints
  Adaptive       Types Solution
  Exercise       
        ↓                   ↓
  Submit Answer → Error Analysis → Update Mastery
        ↓              ↓              ↓
   Check Answer   Classify Error   Update Level (0-1)
   is_correct?   Type & Pattern    Update Attempts
                                   Provide Feedback
```

### Mastery Update Algorithm
```
Student Submits Answer
        ↓
Error Analyzer
  ├─ Student vs Solution comparison
  ├─ Classify error type (conceptual/procedural/careless)
  └─ Store in mistakes_log
        ↓
Student Model
  ├─ Get current mastery level
  ├─ Calculate: new = 0.3 * old + 0.7 * (correct/total)
  ├─ Clamp to [0, 1]
  └─ Update mastery_state table
        ↓
Recommendation Engine
  ├─ Determine next concept
  ├─ Set difficulty level
  └─ Suggest learning path
        ↓
Provide Feedback to Student
```

## 🔗 Component Interactions

### Authentication System
```
frontend/js/api.js
    ↓ (POST /auth/register)
backend/routes/auth.py
    ↓
utils/auth.py (hash_password, TokenStore)
    ↓
database/db.py (students table)
```

### Exercise Generation
```
frontend/js/app.js (Get Next Exercise)
    ↓ (GET /exercise/next)
backend/routes/exercise.py
    ↓
services/student_model.py (get_student_mastery_profile)
services/error_analyzer.py (get_mistake_patterns)
    ↓
services/ai_engine.py (generate_adaptive_exercise)
    ├─ Create AIRequest with current mastery
    ├─ Send to Claude Haiku API
    └─ Parse & return exercise
    ↓
database/db.py (store exercise)
    ↓
Return exercise to frontend
```

### Error Analysis & Feedback
```
frontend/js/app.js (submitAnswer)
    ↓ (POST /exercise/submit)
backend/routes/exercise.py
    ↓
services/error_analyzer.py
  ├─ classify_error()
  ├─ Analyze patterns for concept
  └─ Determine error_type
    ↓
services/student_model.py
  ├─ update_mastery_level()
  ├─ Calculate new mastery
  └─ Update database
    ↓
database/db.py
  ├─ exercise_attempts table
  ├─ mistakes_log table
  └─ mastery_state table
    ↓
Return feedback to frontend
```

## 🤖 AI Integration Pattern

### Request to Claude
```python
# In services/ai_engine.py
prompt = _build_exercise_prompt(ai_request)
  ├─ Student mastery profile
  ├─ Common mistakes
  ├─ Target concept
  └─ Desired difficulty

response = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=1000,
    messages=[{"role": "user", "content": prompt}]
)
```

### Response Structure
```json
{
  "exercise": "Exercise description",
  "hints": ["Hint 1", "Hint 2", "Hint 3"],
  "solution": "Pseudocode solution",
  "explanation": "Why this solution works",
  "difficulty": "easy|medium|challenging"
}
```

## 🗄 Database Relationships

```
students (1)
    ├───────(many)──→ mastery_state (concept_id)
    ├───────(many)──→ exercise_attempts (exercise_id → exercises.id)
    ├───────(many)──→ mistakes_log (concept_id)
    └───────(many)──→ diagnostic_attempts (concept_id)

concepts (1)
    ├───────(many)──→ mastery_state
    ├───────(many)──→ exercises
    ├───────(many)──→ mistakes_log
    └───(many)──→ diagnostic_attempts

exercises (1)
    └───────(many)──→ exercise_attempts
```

## 🔐 Security Layers

1. **Authentication**
   - SHA-256 password hashing
   - JWT-style token system
   - 24-hour token expiration

2. **Authorization**
   - Token required for all protected endpoints
   - Student can only see their own data
   - Server validates token before processing

3. **Data Validation**
   - Pydantic models validate all inputs
   - Type checking on request/response
   - SQL injection prevention (parameterized queries)

4. **CORS**
   - Currently open for development
   - Should restrict to specific origins in production

## 📊 Difficulty Adaptation Algorithm

```
if mastery < 0.4:
    difficulty = "easy"
    # Focus on foundational concepts
    # Simple, clear problems
    # More hand-holding
    
elif 0.4 ≤ mastery < 0.7:
    difficulty = "medium"
    # Balanced challenge level
    # Apply concepts in new contexts
    # Moderate hints needed
    
else (mastery ≥ 0.7):
    difficulty = "challenging"
    # Complex multi-step problems
    # Combine multiple concepts
    # Minimal hints
```

## 📈 Mastery Level Interpretation

```
0.0 - 0.2: Just starting (Need remedial help)
0.2 - 0.4: Early learning (Still struggling)
0.4 - 0.6: Developing skill (Making progress)
0.6 - 0.7: Solidifying (Near competent)
0.7 - 0.9: Proficient (Strong understanding)
0.9 - 1.0: Mastered (Expert level)
```

## 🔄 API Call Sequence

### Creating an Exercise (Detailed)
```
1. Frontend: GET /exercise/next (with token)
   ↓
2. Backend route handler checks authorization
   ↓
3. StudentModel.get_student_mastery_profile(student_id)
   ↓
4. ErrorAnalyzer.get_mistake_patterns(student_id)
   ↓
5. StudentModel.get_difficulty_level(student_id, concept_id)
   ↓
6. AIEngine.generate_adaptive_exercise(AIRequest)
   ├─ Build prompt with all context
   ├─ Call Claude API
   ├─ Parse JSON response
   └─ Return exercise
   ↓
7. Store exercise in database
   ↓
8. Return to frontend with full exercise data
   ↓
9. Frontend displays exercise prompt, hints button
```

## 📱 Frontend Architecture

### State Management
```javascript
// Current state in memory
let currentExercise = null;
let currentDiagnosticConcept = null;
let diagnosticQuestions = [];
let hintLevel = 0;

// Stored in localStorage
{
  token: "...",
  studentId: 1
}
```

### Page Components
```
index.html (Single Page App)
├── #login - Authentication page
├── #dashboard - Progress & recommendations
├── #exercise - Learning interface
└── #diagnostic - Testing interface
```

### Rendering Flow
```
API Response → Process Data → Build HTML → Insert into DOM → Display
```

## 🔑 Key Algorithms

### Mastery Calculation
```python
# Weighted recency bias
historical_weight = 0.3
recent_weight = 0.7

historical_mastery = current_average
recent_mastery = correct_answers / total_attempts

new_mastery = (historical_weight * historical_mastery + 
              recent_weight * recent_mastery)

# Clamp between 0 and 1
new_mastery = max(0.0, min(1.0, new_mastery))
```

### Error Classification
```python
# Pattern-based decision tree
if concept == "Loop":
    if off_by_one_detected:
        error_type = "procedural"
    elif loop_variable_missing:
        error_type = "conceptual"
else if concept == "Conditional":
    if logic_operator_wrong:
        error_type = "conceptual"
    elif assignment_instead_of_comparison:
        error_type = "careless"
else:
    # Similarity-based fallback
    similarity = string_similarity(student, correct)
    error_type = "careless" if similarity > 0.8 else
                 "procedural" if similarity > 0.5 else
                 "conceptual"
```

## 🎯 Performance Considerations

### Database Optimization
- Indexes on student_id, concept_id for fast queries
- One row per student-concept pair (no duplicates)
- Timestamps for historical analysis

### API Optimization
- Lazy loading (fetch data only when needed)
- Batch queries where possible
- Cache concepts in frontend

### Frontend Optimization
- Single Page App (no full page reloads)
- Minimal CSS/JS files
- Responsive design for all devices

---

## 🔄 Extension Points

The system is designed to be extended:

1. **New Concepts**: Add to `utils/prompts.py` diagnostic questions
2. **New Error Types**: Extend `error_analyzer.py` with pattern detection
3. **New AI Models**: Switch Claude model in `ai_engine.py`
4. **New Metrics**: Add analytics queries in `routes/analytics.py`
5. **Frontend Features**: Add pages to `frontend/index.html`

---

**Architecture Version:** 1.0
**Last Updated:** 2024-01-15
