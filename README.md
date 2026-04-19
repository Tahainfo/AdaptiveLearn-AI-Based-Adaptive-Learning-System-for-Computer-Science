<<<<<<< HEAD
# 🎓 Adaptive Learning System for Moroccan High School Students

An AI-powered intelligent learning platform that adapts to student mastery levels and provides personalized exercises for **Algorithmics** and **Networks** education.

## 🌟 Features

- **Diagnostic Tests**: Assess student knowledge across concepts
- **Adaptive Exercises**: AI-generated exercises that match student proficiency
- **Error Detection**: Classify mistakes (conceptual, procedural, careless)
- **Mastery Tracking**: Dynamic mastery profiles updated after each exercise
- **Smart Recommendations**: Suggests what students should learn next
- **Progress Dashboard**: Visualize learning progress across concepts
- **Multi-level Hints**: Progressive hints to guide without spoiling solutions
- **Claude Haiku Integration**: Uses Claude Haiku 4.5 API for intelligent content generation

## 🏗 Architecture

```
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── routes/
│   │   ├── auth.py            # Authentication routes
│   │   ├── diagnostic.py       # Diagnostic test routes
│   │   ├── exercise.py         # Exercise delivery routes
│   │   └── analytics.py        # Dashboard & analytics routes
│   ├── services/
│   │   ├── student_model.py    # Mastery tracking & student profiles
│   │   ├── error_analyzer.py   # Error classification system
│   │   ├── ai_engine.py        # Claude API integration
│   │   └── recommendation.py   # Learning path recommendations
│   ├── models/
│   │   └── database_models.py  # Pydantic models for API validation
│   ├── database/
│   │   └── db.py              # Database initialization & schema
│   └── utils/
│       ├── prompts.py         # AI prompts & diagnostic questions
│       └── auth.py            # Authentication utilities
│
├── frontend/
│   ├── index.html             # Main HTML page
│   ├── css/
│   │   └── style.css          # Styling
│   └── js/
│       ├── config.js          # Configuration
│       ├── api.js             # API communication
│       └── app.js             # Application logic
│
├── requirements.txt           # Python dependencies
├── .env.example              # Environment configuration template
└── README.md                 # This file
```

## 📦 Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python) |
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| Database | SQLite |
| AI | Claude Haiku 4.5 API |
| Server | Uvicorn |

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Claude API key (free tier available at https://console.anthropic.com)

### Installation Steps

#### 1. Clone/Extract the Project
```bash
cd "c:\Users\ISMAILI TAHA\Desktop\CRMEF\SEMESTRE 2\Projet personnel"
```

#### 2. Create Python Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment
```bash
# Copy the example env file
copy .env.example .env

# Edit .env and add your Claude API key
# (Open .env with your text editor and fill in ANTHROPIC_API_KEY)
```

#### 5. Initialize Database
```bash
python backend/database/db.py
```

This creates the SQLite database and inserts default concepts for Algorithmics and Networks.

#### 6. Start the Backend Server
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: **http://localhost:8000**

#### 7. Open Frontend in Browser
```
http://localhost:8000
```

Or if you prefer to serve the frontend separately, open `frontend/index.html` in a web browser.

## 📚 How It Works

### 1. Student Registration & Login
- Students register with username, email, password
- Login generates JWT token for subsequent requests

### 2. Diagnostic Test
- Student takes a diagnostic test for selected concept
- System evaluates understanding (0-100%)
- Initial mastery level is set based on score

### 3. Exercise Generation
- System determines student's weakest concept
- Based on mastery profile and mistake patterns
- Claude API generates targeted exercise for difficulty level
- Student receives: exercise prompt, 3-level hints, solution, explanation

### 4. Answer Submission & Feedback
- Student submits pseudocode or solution
- Error analyzer classifies mistake type:
  - **Conceptual**: Misunderstands the concept
  - **Procedural**: Wrong steps but knows concept
  - **Careless**: Simple arithmetic/syntax error
- Mastery is updated using Bayesian approach
- Student receives targeted feedback

### 5. Progress Tracking
- Mastery profile continuously updated
- Performance analytics show:
  - Overall mastery percentage
  - Progress by domain (Algorithmics/Networks)
  - Error pattern analysis
  - Daily activity statistics

### 6. Smart Recommendations
- Recommends next learning action based on:
  - Weakest areas (mastery < 40%)
  - Concepts not yet attempted
  - Domain-specific learning paths
  - Student readiness to advance

## 🎯 Concepts Covered

### Algorithmics
- **Loops - For**: Iteration with fixed count
- **Loops - While**: Iteration with condition
- **Conditionals - If/Else**: Decision making
- **Arrays/Lists**: Data structure manipulation
- **Pseudocode**: Algorithm description language

### Networks
- **IP Addressing**: IPv4 address structure (192.168.1.1)
- **Subnetting**: Network segmentation (CIDR notation)
- **OSI Model**: 7-layer network model
- **Protocol Basics**: TCP, UDP, packet structure

## 🔌 API Endpoints

### Authentication
- `POST /auth/register` - Register new student
- `POST /auth/login` - Login and get token
- `POST /auth/logout` - Logout

### Diagnostic
- `GET /diagnostic/concepts` - List all concepts
- `GET /diagnostic/questions/{concept_id}` - Get questions for concept
- `POST /diagnostic/submit/{concept_id}` - Submit test answers
- `GET /diagnostic/results/{concept_id}` - Get previous results

### Exercise
- `GET /exercise/next` - Get next recommended exercise
- `POST /exercise/submit` - Submit answer to exercise
- `GET /exercise/hint/{exercise_id}` - Get hint for exercise
- `GET /exercise/stats` - Get exercise statistics

### Analytics
- `GET /analytics/dashboard` - Full dashboard data
- `GET /analytics/progress` - Progress by domain
- `GET /analytics/recommendations` - Learning recommendations
- `GET /analytics/proficiency-by-concept` - Mastery distribution
- `GET /analytics/learning-analytics` - Detailed analytics

## 🧠 Core Intelligence Components

### Student Model (`services/student_model.py`)
- Tracks mastery level (0.0 to 1.0) for each concept
- Calculates difficulty level based on mastery:
  - Easy: mastery < 0.4
  - Medium: 0.4 ≤ mastery < 0.7
  - Challenging: mastery ≥ 0.7
- Updates mastery using weighted average approach

### Error Analyzer (`services/error_analyzer.py`)
- Classifies student errors into 3 categories
- Pattern-specific analysis for each concept:
  - Loops: checks for off-by-one, missing variables
  - Conditionals: detects logic operator confusion
  - Arrays: identifies indexing errors
  - IP: validates format and subnet calculations
- Maintains mistake log for pattern tracking

### AI Engine (`services/ai_engine.py`)
- Interfaces with Claude Haiku 4.5 API
- Generates contextual exercises based on student profile
- Creates hints at 3 difficulty levels
- Analyzes student answers and provides feedback
- Falls back to mock responses if API unavailable

### Recommendation Engine (`services/recommendation.py`)
- Determines optimal next learning action
- Recommends study paths by domain
- Decides when student is ready to advance
- Analyzes overall progress and trends

## 📊 Database Schema

### students
- id, username, email, password_hash, created_at, updated_at

### concepts
- id, name (e.g., "Loops - For"), domain, description

### mastery_state
- id, student_id, concept_id, mastery_level, attempts_count, correct_count, last_updated

### exercise_attempts
- id, student_id, exercise_id, student_answer, is_correct, error_type, time_spent_seconds, created_at

### mistakes_log
- id, student_id, concept_id, mistake_type, description, context, created_at

### diagnostic_attempts
- id, student_id, concept_id, score, answers, created_at

### exercises
- id, concept_id, title, description, difficulty, exercise_prompt, solution, explanation, created_at

## 🤖 Claude API Integration

### Request Format
```json
{
  "concept_mastery": [
    {"concept_name": "Loops - For", "mastery_level": 0.6, "attempts": 5, "correct": 3}
  ],
  "mistake_patterns": [
    {"concept": "Loops - For", "mistake_type": "off-by-one", "frequency": 2}
  ],
  "weak_concept": "Loops - For",
  "difficulty_level": "medium",
  "goal": "generate targeted exercise"
}
```

### Response Format
```json
{
  "exercise": "Exercise description here...",
  "hints": ["Basic hint", "Specific hint", "Almost answer hint"],
  "solution": "Complete solution in pseudocode format",
  "explanation": "Why this solution is correct and key concepts",
  "difficulty": "medium"
}
```

## 🔐 Security Notes

- Passwords are hashed using SHA-256
- Tokens expire after 24 hours
- All API endpoints require authentication (except login/register)
- Frontend validates user input before sending to backend
- CORS configured to accept all origins (development only - restrict in production)

## 🛠 Development

### Running Tests
```bash
# Currently, manual testing recommended
# API docs available at: http://localhost:8000/docs
```

### Database Management
```bash
# Reinitialize database
python backend/database/db.py

# View data (using sqlite3)
sqlite3 data/adaptive_learning.db
.tables
SELECT * FROM students;
```

### Without Claude API
The system will use mock responses if API key is not set. This allows full functionality for testing.

## 📝 Example Request/Response

### Register Student
**Request:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student1",
    "email": "student1@example.com",
    "password": "password123"
  }'
```

**Response:**
```json
{
  "id": 1,
  "username": "student1",
  "email": "student1@example.com",
  "created_at": "2024-01-15T10:30:00"
}
```

### Get Next Exercise
**Request:**
```bash
curl -X GET "http://localhost:8000/exercise/next" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "exercise_id": 42,
  "concept_id": 1,
  "concept_name": "Loops - For",
  "difficulty": "medium",
  "exercise": "Write a pseudocode loop that iterates 5 times...",
  "hints": ["Think about how to count", "Use a counter variable", "Counter goes 1 to 5"],
  "recommendation": {
    "action": "practice_exercise",
    "priority": "high"
  }
}
```

### Submit Exercise Answer
**Request:**
```bash
curl -X POST "http://localhost:8000/exercise/submit" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_id": 42,
    "student_answer": "FOR i = 1 TO 5\n    PRINT i\nEND FOR"
  }'
```

**Response:**
```json
{
  "is_correct": true,
  "error_type": null,
  "feedback": "Perfect! Your loop correctly iterates 5 times.",
  "new_mastery": 0.65,
  "hint": "Great work!"
}
```

## 🎨 Frontend Features

- **Responsive Design**: Works on desktop and mobile
- **Real-time Feedback**: Instant exercise evaluation
- **Progress Visualization**: Mastery bars and statistics
- **Hint System**: Progressive hints without spoilers
- **Dashboard**: Complete learning overview
- **Diagnostic Interface**: Easy concept selection and testing

## 🚧 Future Enhancements

- [ ] Dark mode support
- [ ] Export progress reports (PDF)
- [ ] Leaderboards and competitions
- [ ] Collaborative exercises
- [ ] More concepts and languages
- [ ] Video tutorials
- [ ] Mobile native app
- [ ] Real-time collaborative features
- [ ] Teacher dashboard
- [ ] Advanced analytics and insights

## 📄 License

This project is developed for educational purposes.

## 👥 Contributors

- Developed as an adaptive learning system for Moroccan high school students

## 📞 Support

For issues, questions, or improvements:
1. Check the API documentation at `/docs`
2. Review error messages in browser console
3. Check server logs for backend errors

## 🙏 Acknowledgments

- Built with Claude Haiku 4.5 API
- FastAPI framework
- Moroccan educational curriculum

---

**Happy Learning! 🚀**
=======
# AdaptiveLearn-AI-Based-Adaptive-Learning-System-for-Computer-Science
AdaptiveLearn is an intelligent educational platform designed to personalize learning in computer science for high school students.  The system combines diagnostic assessment, mistake analysis, and AI-generated exercises to adapt learning paths based on each student’s level and weaknesses.
