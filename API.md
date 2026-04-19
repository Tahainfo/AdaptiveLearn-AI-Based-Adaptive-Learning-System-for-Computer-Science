# 🔌 API Reference Guide

Complete API endpoint documentation for the Adaptive Learning System.

## Base URL
```
http://localhost:8000
```

## Authentication

All endpoints (except `/auth/register` and `/auth/login`) require the `Authorization` header:

```
Authorization: Bearer {token}
```

Get token from `/auth/login` response.

---

## 🔐 Authentication Endpoints

### Register New Student
**POST** `/auth/register`

Create a new student account.

**Request:**
```json
{
  "username": "student_name",
  "email": "student@example.com",
  "password": "secure_password"
}
```

**Response (201):**
```json
{
  "id": 1,
  "username": "student_name",
  "email": "student@example.com",
  "created_at": "2024-01-15T10:30:00"
}
```

**Errors:**
- `400`: Student already exists

---

### Login Student
**POST** `/auth/login`

Authenticate and get access token.

**Request:**
```json
{
  "username": "student_name",
  "password": "secure_password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "student_id": 1
}
```

**Errors:**
- `401`: Invalid credentials

---

### Logout Student
**POST** `/auth/logout`

Invalidate user token.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

## 📋 Diagnostic Endpoints

### Get All Concepts
**GET** `/diagnostic/concepts`

List available concepts for diagnostics.

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Loops - For",
    "domain": "Algorithmics",
    "description": "Understanding for loops and iteration"
  },
  {
    "id": 6,
    "name": "IP Addressing",
    "domain": "Networks",
    "description": "Understanding IPv4 address structure"
  }
]
```

---

### Get Diagnostic Questions
**GET** `/diagnostic/questions/{concept_id}`

Get diagnostic questions for a specific concept.

**Example:**
```
GET /diagnostic/questions/1
```

**Response (200):**
```json
[
  {
    "id": 0,
    "question": "What will this pseudocode output?\nFOR i = 1 TO 3\n    PRINT i\nEND FOR",
    "options": ["123", "012", "1234", "3"],
    "correct_index": 0,
    "explanation": "The for loop iterates from 1 to 3, printing each value."
  }
]
```

**Errors:**
- `404`: Concept not found

---

### Submit Diagnostic Answers
**POST** `/diagnostic/submit/{concept_id}`

Submit answers to diagnostic test and get mastery level.

**Example:**
```
POST /diagnostic/submit/1
```

**Request:**
```json
{
  "answers": [
    {
      "question_id": 0,
      "selected_index": 0
    },
    {
      "question_id": 1,
      "selected_index": 2
    }
  ]
}
```

**Response (200):**
```json
{
  "concept_id": 1,
  "concept_name": "Loops - For",
  "score": 66.67,
  "mastery_level": 0.667
}
```

---

### Get Diagnostic Results
**GET** `/diagnostic/results/{concept_id}`

Get previous diagnostic test results.

**Example:**
```
GET /diagnostic/results/1
```

**Response (200):**
```json
{
  "concept_name": "Loops - For",
  "score": 66.67,
  "taken_at": "2024-01-15T10:45:00",
  "mastery_level": 0.667
}
```

**Errors:**
- `404`: No diagnostic results found

---

## 📚 Exercise Endpoints

### Get Next Exercise
**GET** `/exercise/next`

Get the next recommended exercise based on student profile.

**Response (200):**
```json
{
  "type": "exercise",
  "exercise_id": 42,
  "concept_id": 1,
  "concept_name": "Loops - For",
  "difficulty": "medium",
  "exercise": "Write a pseudocode algorithm that...",
  "hints": [
    "Start by understanding the problem",
    "Use a for loop to iterate",
    "Check the loop bounds carefully"
  ],
  "recommendation": {
    "action": "practice_exercise",
    "priority": "high",
    "reason": "Practice 'Loops - For' to improve mastery"
  }
}
```

---

### Submit Exercise Answer
**POST** `/exercise/submit`

Submit student answer and get feedback.

**Request:**
```json
{
  "exercise_id": 42,
  "student_answer": "FOR i = 1 TO 5\n    PRINT i\nEND FOR"
}
```

**Response (200):**
```json
{
  "is_correct": true,
  "error_type": null,
  "feedback": "Excellent! Your loop correctly iterates 5 times.",
  "new_mastery": 0.75,
  "hint": "Great work! Your mastery improved to 75%"
}
```

**Error Response (when incorrect):**
```json
{
  "is_correct": false,
  "error_type": "procedural",
  "feedback": "Not quite right. Your loop logic has an issue.",
  "new_mastery": 0.55,
  "hint": "Check if your loop counter starts at the right value"
}
```

---

### Get Hint
**GET** `/exercise/hint/{exercise_id}`

Get a hint for an exercise at a specific level.

**Query Parameters:**
- `hint_level` (optional, 1-3): Hint difficulty level (default: 1)

**Example:**
```
GET /exercise/hint/42?hint_level=2
```

**Response (200):**
```json
{
  "hint": "You need a loop to repeat the action multiple times",
  "level": 2,
  "message": "Remember: the solution should follow the concept principles"
}
```

---

### Get Exercise Statistics
**GET** `/exercise/stats`

Get student's exercise performance statistics.

**Response (200):**
```json
{
  "total_attempts": 25,
  "total_correct": 18,
  "overall_accuracy": 72.0,
  "by_concept": [
    {
      "concept": "Loops - For",
      "attempts": 8,
      "correct": 6,
      "accuracy": 75.0
    },
    {
      "concept": "Conditionals - If/Else",
      "attempts": 7,
      "correct": 5,
      "accuracy": 71.43
    }
  ]
}
```

---

## 📊 Analytics Endpoints

### Get Dashboard
**GET** `/analytics/dashboard`

Get complete dashboard data with all statistics.

**Response (200):**
```json
{
  "student": {
    "id": 1,
    "username": "student_name",
    "email": "student@example.com",
    "created_at": "2024-01-15T10:30:00"
  },
  "mastery_states": [
    {
      "concept_id": 1,
      "concept_name": "Loops - For",
      "domain": "Algorithmics",
      "mastery_level": 0.75,
      "attempts": 8,
      "correct": 6
    }
  ],
  "recent_attempts": [
    {
      "concept": "Loops - For",
      "is_correct": true,
      "timestamp": "2024-01-15T11:20:00"
    }
  ],
  "statistics": {
    "average_mastery": 0.672,
    "total_attempts": 25,
    "total_correct": 18,
    "overall_accuracy": 0.72
  }
}
```

---

### Get Progress by Domain
**GET** `/analytics/progress`

Get learning progress organized by domain (Algorithmics/Networks).

**Response (200):**
```json
{
  "domains": [
    {
      "domain": "Algorithmics",
      "total_concepts": 5,
      "mastered": 2,
      "developing": 2,
      "struggling": 1,
      "average_mastery": 0.58,
      "progress_percentage": 40.0
    },
    {
      "domain": "Networks",
      "total_concepts": 4,
      "mastered": 0,
      "developing": 1,
      "struggling": 3,
      "average_mastery": 0.22,
      "progress_percentage": 0.0
    }
  ]
}
```

---

### Get Learning Recommendations
**GET** `/analytics/recommendations`

Get personalized learning recommendations and study paths.

**Response (200):**
```json
{
  "algorithmics_path": [
    {
      "concept_id": 3,
      "concept_name": "Conditionals - If/Else",
      "mastery_level": 0.35,
      "attempts": 4,
      "status": "struggling",
      "recommended_action": "Review & Practice"
    }
  ],
  "networks_path": [
    {
      "concept_id": 6,
      "concept_name": "IP Addressing",
      "mastery_level": 0.0,
      "attempts": 0,
      "status": "not_started",
      "recommended_action": "Begin"
    }
  ],
  "next_action": {
    "action": "remedial_exercise",
    "concept_id": 3,
    "concept_name": "Conditionals - If/Else",
    "priority": "critical",
    "reason": "Need to strengthen 'Conditionals - If/Else' - only 35% mastery"
  }
}
```

---

### Get Proficiency by Concept
**GET** `/analytics/proficiency-by-concept`

Get mastery levels for all concepts.

**Response (200):**
```json
{
  "concepts": [
    {
      "concept": "Loops - For",
      "domain": "Algorithmics",
      "mastery_level": 0.75,
      "attempts": 8,
      "level": "Mastered"
    },
    {
      "concept": "Conditionals - If/Else",
      "domain": "Algorithmics",
      "mastery_level": 0.35,
      "attempts": 4,
      "level": "Struggling"
    }
  ]
}
```

---

### Get Learning Analytics
**GET** `/analytics/learning-analytics`

Get detailed learning analytics (activity, errors, etc).

**Response (200):**
```json
{
  "daily_activity": [
    {
      "date": "2024-01-15",
      "exercises_completed": 5,
      "correct_answers": 4,
      "accuracy": 80.0
    }
  ],
  "error_distribution": [
    {
      "error_type": "procedural",
      "count": 3
    },
    {
      "error_type": "careless",
      "count": 2
    }
  ]
}
```

---

## ❌ Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes:
- `200`: Success
- `201`: Created
- `400`: Bad request (invalid data)
- `401`: Unauthorized (missing/invalid token)
- `404`: Not found (resource doesn't exist)
- `500`: Server error

---

## 📝 Common Usage Patterns

### Complete Flow Example

#### 1. Register
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student1",
    "email": "student1@example.com",
    "password": "password123"
  }'
```

#### 2. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student1",
    "password": "password123"
  }'
# Get token from response
```

#### 3. Take Diagnostic
```bash
# Get concepts
curl -X GET "http://localhost:8000/diagnostic/concepts" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get questions for concept 1
curl -X GET "http://localhost:8000/diagnostic/questions/1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Submit answers
curl -X POST "http://localhost:8000/diagnostic/submit/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {"question_id": 0, "selected_index": 0},
      {"question_id": 1, "selected_index": 2}
    ]
  }'
```

#### 4. Get Exercise
```bash
curl -X GET "http://localhost:8000/exercise/next" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 5. Submit Answer
```bash
curl -X POST "http://localhost:8000/exercise/submit" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_id": 42,
    "student_answer": "FOR i = 1 TO 5\n    PRINT i\nEND FOR"
  }'
```

#### 6. View Dashboard
```bash
curl -X GET "http://localhost:8000/analytics/dashboard" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔗 Interactive Documentation

While the server is running, visit:
```
http://localhost:8000/docs
```

This provides an interactive Swagger UI where you can:
- Browse all endpoints
- View request/response schemas
- Test endpoints directly

---

**Last Updated:** 2024-01-15
**API Version:** 1.0.0
