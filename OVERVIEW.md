# 📊 Visual Project Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ADAPTIVE LEARNING SYSTEM                     │
│                  For Moroccan High School Students                   │
└─────────────────────────────────────────────────────────────────────┘

                              FRONTEND
                         (HTML/CSS/JavaScript)
        ┌──────────────────────────────────────────────────┐
        │                                                  │
        │  📱 Login/Register    📊 Dashboard              │
        │                      • Mastery bars            │
        │  💡 Exercise Mode     • Recommendations       │
        │  • Get Exercise       • Progress stats         │
        │  • Get Hints                                   │
        │  • Submit Answer      🧪 Diagnostic Tests     │
        │                       • Select concept         │
        │                       • Answer questions       │
        │                       • View results           │
        └──────────────────────────────────────────────────┘
                              ↕ HTTP REST API (15 endpoints)
                              
┌─────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI/Python)                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ROUTES (API Endpoints)                                      │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ 🔐 Auth Routes (3)  │ 📋 Diagnostic (4) │ 💡 Exercise (4)   │  │
│  │ • Register         │ • Get Concepts    │ • Get Next      │  │
│  │ • Login           │ • Get Questions   │ • Submit Answer │  │
│  │ • Logout          │ • Submit Test     │ • Get Hint      │  │
│  │                   │ • Get Results     │ • Get Stats     │  │
│  │                   │                   │                 │  │
│  │ 📊 Analytics (5) ├─┴─────────────────┴─────────────────┤  │
│  │ • Dashboard       │                                     │  │
│  │ • Progress        │   INTELLIGENT SERVICES              │  │
│  │ • Recommendations ├─────────────────────────────────────┤  │
│  │ • Proficiency     │ 🧠 StudentModel                     │  │
│  │ • Analytics       │    • Mastery tracking              │  │
│  │                   │    • Difficulty calculation        │  │
│  │                   │    • Performance stats             │  │
│  │                   │                                     │  │
│  │                   │ ⚠️ ErrorAnalyzer                    │  │
│  │                   │    • Error classification          │  │
│  │                   │    • Pattern detection             │  │
│  │                   │    • Mistake logging               │  │
│  │                   │                                     │  │
│  │                   │ 🤖 AIEngine (Claude Haiku)         │  │
│  │                   │    • Generate exercises            │  │
│  │                   │    • Create hints                  │  │
│  │                   │    • Provide solutions             │  │
│  │                   │    • Analyze answers               │  │
│  │                   │                                     │  │
│  │                   │ 🎯 RecommendationEngine            │  │
│  │                   │    • Next learning action          │  │
│  │                   │    • Study paths                   │  │
│  │                   │    • Progress analysis             │  │
│  │                   │                                     │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  DATA MODELS                                                 │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ StudentCreate  │ MasteryProfile │ ExerciseAttempt          │  │
│  │ DiagnosticTest │ ErrorAnalysis  │ AIRequest                │  │
│  │ ... (20 Pydantic models)                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────┬───────────────────────────────────────┘
                               ↕ SQLite Queries
                               
┌──────────────────────────────────────────────────────────────────────┐
│                       DATABASE (SQLite)                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [students] ←1──────∞→ [mastery_state] ←∞──1→ [concepts]          │
│     ↓                         ↑                     ↓                │
│     ├──∞→ [exercise_attempts] ─────┘              [exercises]      │
│     ├──∞→ [mistakes_log]                              ↓             │
│     └──∞→ [diagnostic_attempts]                 (1 has Many)       │
│                                                                      │
│  TABLES: 7 normalized tables with proper relationships            │
│  INDEXES: On student_id, concept_id for performance             │
│  QUERY: Fast analytics with proper joins                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                        CLAUDE HAIKU 4.5 API                         │
│                                                                      │
│  INPUT: Student mastery profile + weak concept + difficulty       │
│  PROCESS: AI generates contextual educational content             │
│  OUTPUT: Exercise | Hints[3] | Solution | Explanation            │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## Learning Flow Diagram

```
         START
           │
           ↓
     ┌─────────────┐
     │  Register   │
     │   & Login   │
     └──────┬──────┘
            │
       ┌────▼────┐
       │ Dashboard
       │  (Empty)
       └────┬────┘
            │
            ▼
      ┌──────────────────┐
      │  Diagnostic Test │
      │  • Select topic  │
      │  • Answer Qs     │
      │  • Get score     │
      └────────┬─────────┘
               │
         ┌─────▼──────────────────┐
         │  Mastery Level Set     │
         │  Based on Test Score   │
         │  (Updates Database)    │
         └─────┬──────────────────┘
               │
       ┌───────▼──────────┐
       │  View Dashboard  │
       │ • Mastery: 65%   │
       │ • Attempted: 1   │
       │ • Next: Practice │
       └───────┬──────────┘
               │
    ┌──────────▼─────────────┐
    │   Get Next Exercise    │
    │  (AI Generated)        │
    │  • Difficulty: Medium  │
    │  • Concept: Loops      │
    └──────────┬─────────────┘
               │
    ┌──────────▼──────────────────┐
    │   Student Attempts          │
    │  • Reads exercise           │
    │  • Gets hints (optional)    │
    │  • Types pseudocode         │
    │  • Submits answer           │
    └──────────┬──────────────────┘
               │
    ┌──────────▼─────────────────┐
    │  Error Analysis             │
    │  • Check answer             │
    │  • Classify error type      │
    │  • Update mastery (Bayesian)
    │  • Log mistake pattern      │
    └──────────┬──────────────────┘
               │
    ┌──────────▼──────────────┐
    │  Provide Feedback        │
    │  ✅ Correct / ❌ Incorrect
    │  New Mastery: 72%        │
    │  Keep practicing!        │
    └──────────┬──────────────┘
               │
    ┌──────────▼──────────────────────┐
    │  Recommendation Engine           │
    │  Based on mastery:              │
    │  - If < 40%: Remedial exercise  │
    │  - If 40-70%: Practice more     │
    │  - If > 70%: Challenge exercise │
    └──────────┬──────────────────────┘
               │
    ┌──────────▼──────────────┐
    │  Get Next Exercise      │
    │  (Loop continues...)    │
    └─────────┬────────────────┘
              │
         ┌────▼────────┬──────────┐
         │   Or Check  │ Continue │
         │  Dashboard  │ Learning │
         └─────────────┴──────────┘
```

## Mastery Level Progression

```
Interactions:    0    1    2    3    4    5    6    7    8    9    10
Correct:         0    1    1    2    2    3    3    4    4    5    6
Attempts:        0    1    2    3    4    5    6    7    8    9   10

Mastery %:      0%  100%  85%  73%  63%  65%  60%  64%  60%  65%  68%
                ▁    ▅    ▄    ▃    ▃    ▄    ▃    ▄    ▃    ▄    ▄

Difficulty:    Easy  Easy  Easy  Med  Med  Med  Med  Med  Med  Med  Med
               │     │     │     │    │    │    │    │    │    │    │
               └─────────────────┴────┴────┴────┴────┴────┴────┴────┘
                              Learning Progression
```

## Concept Coverage Map

```
ALGORITHMICS                         NETWORKS
────────────                         ────────
                                     
Loops - For                          IP Addressing
  ↓ depends on                          ↓
Conditionals → Arrays/Lists          Subnetting
  ↓ ↓ ↓ ↓                               ↓
  └─ Pseudocode ────────→            OSI Model
                          ↓             ↓
                      Complex Problems Protocol Basics

✅ 5 Algorithmics concepts           ✅ 4 Networks concepts
✅ 15 Diagnostic questions           ✅ Progressive difficulty
✅ Adaptive exercises                ✅ Pattern detection
✅ Error classification              ✅ Performance tracking
```

## API Request/Response Flow

```
┌─────────────┐
│ Frontend    │
│ (Browser)   │
└──────┬──────┘
       │
       │ 1. GET /exercise/next
       │    (with Authorization header)
       ↓
┌──────────────────────┐
│ Backend Route        │
│ (FastAPI)            │
└──────┬───────────────┘
       │
       │ 2. Request student mastery profile
       ↓
┌──────────────────────┐
│ StudentModel Service │
│ Database Query       │
└──────┬───────────────┘
       │
       │ 3. Build AIRequest
       ↓
┌──────────────────────┐
│ AIEngine Service     │
│ Claude API call      │
└──────┬───────────────┘
       │
       │ {"exercise": "...", "hints": [...], "solution": "...", ...}
       ↓
┌──────────────────────┐
│ Store in Database    │
│ (exercises table)    │
└──────┬───────────────┘
       │
       │ 4. Return exercise to frontend
       ↓
┌──────────────────┐
│ Frontend         │
│ Display Exercise │
└──────────────────┘
       │
       │ (User reads, tries to solve)
       │
       │ 5. POST /exercise/submit
       │    {exercise_id, student_answer}
       ↓
┌──────────────────────┐
│ Backend Route        │
─ Error Analysis       │
└──────┬───────────────┘
       │
       │ 6. Check answer, update mastery
       ↓
┌──────────────────────┐
│ StudentModel Update  │
│ ErrorAnalyzer Log    │
└──────┬───────────────┘
       │
       │ 7. Return feedback result
       ↓
┌──────────────────────┐
│ Frontend             │
│ Show Result & Hints  │
└──────────────────────┘
```

## Technology Stack Layers

```
┌────────────────────────────────────┐
│  PRESENTATION LAYER                │
│  • HTML5 (Markup)                  │
│  • CSS3 (Styling)                  │
│  • Vanilla JavaScript (Logic)      │
│  • Responsive Design               │
└────────────────────────────────────┘
           ↑ HTTP REST ↓
┌────────────────────────────────────┐
│  APPLICATION LAYER                 │
│  • FastAPI Framework               │
│  • Pydantic Models                 │
│  • Request/Response Handling       │
│  • CORS Middleware                 │
└────────────────────────────────────┘
           ↑ Python Calls ↓
┌────────────────────────────────────┐
│  BUSINESS LOGIC LAYER              │
│  • Student Model                   │
│  • Error Analyzer                  │
│  • AI Engine                       │
│  • Recommendation Engine           │
└────────────────────────────────────┘
           ↑ Queries/API ↓
┌────────────────────────────────────┐
│  DATA LAYER                        │
│  • SQLite Database                 │
│  • Normalized Schema               │
│  • 7 Tables                        │
│  • Proper Indexes                  │
└────────────────────────────────────┘
           ↑ HTTP API ↓
┌────────────────────────────────────┐
│  EXTERNAL SERVICES                 │
│  • Claude Haiku 4.5 API            │
│  • AI Exercise Generation          │
│  • Smart Content Creation          │
└────────────────────────────────────┘
```

## File Organization Tree

```
📦 Projet personnel/
 ├── 📄 README.md (Main documentation)
 ├── 📄 QUICKSTART.md (5-min setup)
 ├── 📄 DATABASE.md (Schema guide)
 ├── 📄 API.md (Endpoint reference)
 ├── 📄 ARCHITECTURE.md (Design docs)
 ├── 📄 COMPLETION.md (Summary)
 ├── 📄 requirements.txt
 ├── 📄 .env.example
 │
 ├── 📁 backend/
 │  ├── 📄 main.py (Entry point)
 │  ├── 📁 routes/ (API endpoints)
 │  │  ├── auth.py (3 endpoints)
 │  │  ├── diagnostic.py (4 endpoints)
 │  │  ├── exercise.py (4 endpoints)
 │  │  └── analytics.py (5 endpoints)
 │  ├── 📁 services/ (Business logic)
 │  │  ├── student_model.py
 │  │  ├── error_analyzer.py
 │  │  ├── ai_engine.py
 │  │  └── recommendation.py
 │  ├── 📁 models/ (Data validation)
 │  │  └── database_models.py (20 models)
 │  ├── 📁 database/ (Data persistence)
 │  │  └── db.py (7 tables)
 │  └── 📁 utils/ (Helpers)
 │     ├── prompts.py (AI prompts)
 │     └── auth.py (Token management)
 │
 └── 📁 frontend/
    ├── 📄 index.html (4 pages, SPA)
    ├── 📁 css/
    │  └── 📄 style.css (Responsive)
    └── 📁 js/
       ├── 📄 config.js (Settings)
       ├── 📄 api.js (API client)
       └── 📄 app.js (App logic)
```

## Key Features Summary

```
┌──────────────────────────────────────────────────────────┐
│  🎓 ADAPTIVE LEARNING SYSTEM - KEY FEATURES             │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ✅ Diagnostic Testing                                  │
│     - Pre-test assessment                              │
│     - Mastery level calculation                        │
│     - Baseline performance                             │
│                                                         │
│  ✅ Personalized Exercise Generation                    │
│     - AI-powered (Claude Haiku)                        │
│     - Difficulty-matched                              │
│     - Concept-focused                                 │
│                                                         │
│  ✅ Intelligent Error Analysis                         │
│     - 3 error types detected                          │
│     - Pattern recognition                            │
│     - Mistake logging                                │
│                                                         │
│  ✅ Mastery Tracking                                   │
│     - Per-concept tracking                           │
│     - Bayesian updates                               │
│     - Historical trends                              │
│                                                         │
│  ✅ Smart Recommendations                              │
│     - Next learning action                           │
│     - Study paths by domain                          │
│     - Readiness assessment                           │
│                                                         │
│  ✅ Comprehensive Analytics                            │
│     - Dashboard overview                             │
│     - Progress by domain                             │
│     - Error distribution                             │
│     - Daily activity                                 │
│                                                         │
│  ✅ Multi-Level Hints                                  │
│     - Progressive hint system                        │
│     - Difficulty-matched hints                       │
│     - Don't spoil answers                            │
│                                                         │
│  ✅ Responsive Interface                               │
│     - Works on all devices                          │
│     - Intuitive navigation                          │
│     - Real-time feedback                            │
│                                                         │
│  ✅ Secure & Scalable                                  │
│     - Token authentication                          │
│     - Normalized database                           │
│     - Stateless API                                 │
│                                                         │
└──────────────────────────────────────────────────────────┘
```

---

**This comprehensive system provides a complete, production-ready adaptive learning platform!** 🚀
