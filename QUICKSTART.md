# 🚀 Quick Start Guide

Get the Adaptive Learning System running in 5 minutes!

## Step 1: Setup Environment (2 minutes)

### Windows
```bash
# Open Command Prompt or PowerShell in the project directory
cd "c:\Users\ISMAILI TAHA\Desktop\CRMEF\SEMESTRE 2\Projet personnel"

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies  
pip install -r requirements.txt
```

### macOS/Linux
```bash
cd ~/Desktop/CRMEF/SEMESTRE\ 2/Projet\ personnel

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

## Step 2: Get Claude API Key (1 minute)

1. Go to https://console.anthropic.com
2. Sign up or login
3. Create API key
4. Copy the key (starts with `sk-ant-`)

## Step 3: Configure Your Key (1 minute)

### Windows
```bash
# Create .env file
copy .env.example .env

# Open .env in Notepad
notepad .env
```

### macOS/Linux
```bash
cp .env.example .env
nano .env
```

Edit `.env` and replace the XXX with your actual Claude API key:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

Save the file.

## Step 4: Start the Backend (1 minute)

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Database initialized
```

## Step 5: Open in Browser (1 minute)

Open your browser and go to:
```
http://localhost:8000
```

You'll see the login page!

## First Time Usage

### 1. Create Account
- Click "Register here" link
- Fill in username, email, password
- Click "Register"

### 2. Login
- Enter your credentials
- You'll see the dashboard

### 3. Take Diagnostic Test
- Click "Diagnostic" in menu
- Select a concept (e.g., "Loops - For")
- Answer 3 questions
- See your mastery score!

### 4. Start Learning
- Click "Exercise" in menu
- System generates a targeted exercise
- Click "Get Hint" to see progressive hints
- Enter your pseudocode answer
- Get instant feedback on your mastery!

### 5. View Progress
- Click "Dashboard"
- See all your mastery levels
- See recommended next steps
- View your statistics

## 🎯 Quick Test Data

To test without needing the Claude API, the system has built-in fallbacks. But for full features:

### Example Login
```
Username: testuser
Email: test@example.com
Password: password123
```

## Common Issues

### "Module not found" error
```bash
# Make sure virtual environment is activated
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Reinstall packages
pip install -r requirements.txt
```

### "Port 8000 already in use"
The port might be in use by another application. Use a different port:
```bash
python -m uvicorn backend.main:app --reload --port 8001
```
Then access at `http://localhost:8001`

### API key not working
- Double-check it starts with `sk-ant-`
- Make sure it's in the `.env` file (not `.env.example`)
- Restart the server after changing `.env`

### Database errors
```bash
# Reinitialize the database
python backend/database/db.py
```

## 📚 Next Steps

Once you have it running:

1. **Explore Concepts**: Try different topics in Diagnostics
2. **Complete Exercises**: Build your mastery scores
3. **Check Analytics**: View your detailed progress
4. **Try Different Difficulties**: System adapts to your level

## 🔗 Useful Links

- **API Documentation**: http://localhost:8000/docs
- **Database**: `data/adaptive_learning.db` (SQLite)
- **Frontend Code**: `frontend/index.html`
- **Backend Code**: `backend/main.py`

## 💡 Tips

- Hints progressively help without giving answers
- System tracks all your mistakes and learns your patterns
- Mastery updates after each exercise
- Dashboard shows what you should learn next
- Use different usernames to test multiple student profiles

**You're all set! Happy learning! 🎓**
