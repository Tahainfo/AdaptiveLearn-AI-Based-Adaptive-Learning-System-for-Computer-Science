# 📊 Database Schema & Operations

## Database Overview

The system uses SQLite database for simplicity. Default location: `data/adaptive_learning.db`

## 📋 Tables

### 1. **students**
Stores user account information.

```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `id`: Unique student identifier
- `username`: Login username (unique)
- `email`: Student email (unique)
- `password_hash`: SHA-256 hashed password
- `created_at`: Account creation timestamp
- `updated_at`: Last profile update

### 2. **concepts**
Learning concepts available in the system.

```sql
CREATE TABLE concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    domain TEXT NOT NULL,
    description TEXT
);
```

**Sample Data:**
- ✅ Loops - For (Domain: Algorithmics)
- ✅ Conditionals - If/Else (Domain: Algorithmics)
- ✅ Arrays/Lists (Domain: Algorithmics)
- ✅ IP Addressing (Domain: Networks)
- ✅ Subnetting (Domain: Networks)

### 3. **mastery_state** ⭐ Core Table
Tracks each student's progress on each concept.

```sql
CREATE TABLE mastery_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    concept_id INTEGER NOT NULL,
    mastery_level REAL DEFAULT 0.0,
    attempts_count INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (concept_id) REFERENCES concepts(id),
    UNIQUE(student_id, concept_id)
);
```

**Fields:**
- `mastery_level`: 0.0 to 1.0 (0% to 100%)
- `attempts_count`: Total exercises attempted
- `correct_count`: Correct answers
- **One row per student per concept**

### 4. **exercises**
Library of learning exercises.

```sql
CREATE TABLE exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    difficulty TEXT,  -- 'easy', 'medium', 'challenging'
    exercise_prompt TEXT,
    solution TEXT,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (concept_id) REFERENCES concepts(id)
);
```

**Fields:**
- `difficulty`: Matches student mastery level
- `exercise_prompt`: The actual exercise question
- `solution`: Correct pseudocode solution
- `explanation`: Why this solution is correct

### 5. **exercise_attempts**
Student answer history.

```sql
CREATE TABLE exercise_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    student_answer TEXT,
    is_correct INTEGER,  -- 0 or 1
    error_type TEXT,     -- 'conceptual', 'procedural', 'careless'
    time_spent_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);
```

**Fields:**
- `is_correct`: Boolean (0=incorrect, 1=correct)
- `error_type`: Classification of mistake
- `time_spent_seconds`: How long to solve

### 6. **mistakes_log**
Detailed error pattern tracking.

```sql
CREATE TABLE mistakes_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    concept_id INTEGER NOT NULL,
    mistake_type TEXT,
    description TEXT,
    context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (concept_id) REFERENCES concepts(id)
);
```

**Used for:**
- Identifying patterns in wrong answers
- Personalizing feedback and hints
- Recommending specific practice areas

### 7. **diagnostic_attempts**
Diagnostic test history.

```sql
CREATE TABLE diagnostic_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    concept_id INTEGER NOT NULL,
    score REAL,  -- 0-100
    answers TEXT, -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (concept_id) REFERENCES concepts(id)
);
```

## 🔄 Key Relationships

```
students (1) ──┬── (Many) mastery_state ──(1) concepts
               ├── (Many) exercise_attempts ──(1) exercises ──(1) concepts
               ├── (Many) mistakes_log ──(1) concepts
               └── (Many) diagnostic_attempts ──(1) concepts
```

## 📊 Query Examples

### Get Student Mastery Profile
```sql
SELECT c.name, m.mastery_level, m.attempts_count, m.correct_count
FROM mastery_state m
JOIN concepts c ON m.concept_id = c.id
WHERE m.student_id = 1
ORDER BY c.name;
```

### Find Weakest Concept
```sql
SELECT c.name, m.mastery_level
FROM mastery_state m
JOIN concepts c ON m.concept_id = c.id
WHERE m.student_id = 1
ORDER BY m.mastery_level ASC
LIMIT 1;
```

### Get Recent Attempts
```sql
SELECT e.title, ea.student_answer, ea.is_correct, ea.created_at
FROM exercise_attempts ea
JOIN exercises e ON ea.exercise_id = e.id
WHERE ea.student_id = 1
ORDER BY ea.created_at DESC
LIMIT 10;
```

### Analyze Error Patterns
```sql
SELECT mistake_type, COUNT(*) as frequency
FROM mistakes_log
WHERE student_id = 1 AND concept_id = 1
GROUP BY mistake_type
ORDER BY frequency DESC;
```

### Get Concepts by Mastery Status
```sql
SELECT c.name,
  SUM(CASE WHEN m.mastery_level >= 0.7 THEN 1 ELSE 0 END) as mastered,
  SUM(CASE WHEN m.mastery_level >= 0.4 AND m.mastery_level < 0.7 THEN 1 ELSE 0 END) as developing,
  SUM(CASE WHEN m.mastery_level < 0.4 THEN 1 ELSE 0 END) as struggling
FROM concepts c
LEFT JOIN mastery_state m ON c.id = m.concept_id
GROUP BY c.id;
```

## 🔧 Database Operations

### View Database in SQLite
```bash
# Install sqlite3 if needed
pip install sqlite3

# Open database
sqlite3 data/adaptive_learning.db

# View tables
.tables

# View schema
.schema mastery_state

# Run a query
SELECT * FROM students;

# Exit
.quit
```

### Reset Database
```bash
# Delete current database
rm data/adaptive_learning.db  # macOS/Linux
del data\adaptive_learning.db # Windows

# Reinitialize
python backend/database/db.py
```

### Backup Database
```bash
# Copy database file
cp data/adaptive_learning.db data/adaptive_learning.backup.db

# Or export to SQL
sqlite3 data/adaptive_learning.db .dump > backup.sql
```

## 📈 Mastery Level Calculation

The system uses a weighted average approach:

```
new_mastery = 0.3 * historical_mastery + 0.7 * recent_mastery

where:
  recent_mastery = correct_answers / total_attempts
  historical_mastery = previous_mastery_level
```

This emphasizes recent performance while maintaining historical progress.

### Examples:
- Student gets first 3 correct: mastery = 1.0
- Next 3 incorrect: mastery = 0.3 * 1.0 + 0.7 * (3/6) = 0.65
- Improves over time: mastery increases gradually

## 🎯 Difficulty Assignment

Based on mastery level:

```python
if mastery < 0.4:
    difficulty = "easy"
elif mastery < 0.7:
    difficulty = "medium"
else:
    difficulty = "challenging"
```

## 📊 Analytics Queries

### Student Progress Report
```sql
SELECT 
  s.username,
  COUNT(DISTINCT m.concept_id) as concepts_attempted,
  AVG(m.mastery_level) as avg_mastery,
  SUM(ea.is_correct) as total_correct,
  COUNT(*) as total_attempts
FROM students s
LEFT JOIN mastery_state m ON s.id = m.student_id
LEFT JOIN exercise_attempts ea ON s.id = ea.student_id
WHERE s.id = 1
GROUP BY s.id;
```

### Class Statistics
```sql
SELECT 
  AVG(mastery_level) as avg_class_mastery,
  MIN(mastery_level) as min_mastery,
  MAX(mastery_level) as max_mastery
FROM mastery_state;
```

---

**Note:** The database structure is automatically created when you run `python backend/database/db.py`
