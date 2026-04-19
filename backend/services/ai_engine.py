"""
AI Engine Service - Integration with Claude API for adaptive learning
"""
import os
import json
import sqlite3
from typing import Dict, List, Optional
from backend.models.database_models import AIRequest, AIResponse, MasteryProfile, MistakePattern


class AIEngine:
    """Handles AI integration with Claude Haiku API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI Engine with Claude API
        Uses ANTHROPIC_API_KEY environment variable if not provided
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        # Import here to avoid dependency issues if not installed
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            print("Warning: anthropic library not installed. Install with: pip install anthropic")
            self.client = None
    
    def generate_adaptive_exercise(self, ai_request: AIRequest) -> Dict:
        """
        Generate a targeted exercise based on student's mastery profile and mistakes
        """
        if not self.client:
            return self._mock_exercise_response()
        
        prompt = self._build_exercise_prompt(ai_request)
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = response.content[0].text
            
            # Parse JSON response
            try:
                # Try to extract JSON from code blocks or find JSON object
                json_str = response_text
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                
                exercise_data = json.loads(json_str.strip())
                return exercise_data
            except json.JSONDecodeError:
                # If parsing fails, structure the response
                return self._structure_response(response_text)
        
        except Exception as e:
            print(f"Claude API error: {e}")
            return self._mock_exercise_response()
    
    def _build_exercise_prompt(self, ai_request: AIRequest) -> str:
        """Build the prompt to send to Claude"""
        
        mastery_summary = "\n".join([
            f"- {m.concept_name}: {m.mastery_level:.1%} mastery ({m.correct}/{m.attempts} correct)"
            for m in ai_request.concept_mastery
        ])
        
        mistakes_summary = ""
        if ai_request.mistake_patterns:
            mistakes_summary = "\n".join([
                f"- {m.concept}: {m.mistake_type} error ({m.frequency} times)"
                for m in ai_request.mistake_patterns[:3]
            ])
        
        prompt = f"""You are an expert tutor for Moroccan high school students learning algorithmics and networks.

STUDENT PROFILE:
Current Mastery Levels:
{mastery_summary}

Common Mistakes:
{mistakes_summary if mistakes_summary else "None recorded yet"}

TASK:
Generate a {ai_request.difficulty_level} exercise for the concept: {ai_request.weak_concept}

The exercise should:
1. Target the student's weak area
2. Help them overcome their typical mistakes
3. Match their difficulty level ({ai_request.difficulty_level})
4. Be clear and actionable

RESPONSE FORMAT (MUST BE VALID JSON):
{{
    "exercise": "Your exercise question here with context",
    "hints": ["Hint 1: Basic hint", "Hint 2: More specific", "Hint 3: Nearly the answer"],
    "solution": "Complete solution in pseudocode format",
    "explanation": "Why this solution is correct and how it relates to the concept",
    "difficulty": "{ai_request.difficulty_level}"
}}

Respond ONLY with the JSON object above, no additional text."""

        return prompt
    
    def _mock_exercise_response(self) -> Dict:
        """Return a mock exercise for testing without API"""
        return {
            "exercise": "Write a pseudocode algorithm to find the maximum value in an array",
            "hints": [
                "Start by assuming the first element is the maximum",
                "You'll need a loop to compare each element with your current maximum",
                "Update the maximum whenever you find a larger value"
            ],
            "solution": """ALGORITHM FindMax(array A)
    max = A[0]
    FOR i = 1 TO length(A) - 1 DO
        IF A[i] > max THEN
            max = A[i]
        END IF
    END FOR
    RETURN max
END ALGORITHM""",
            "explanation": "This algorithm uses a simple approach: start with the first element as maximum, then iterate through the array comparing each element. When a larger element is found, update the maximum. This demonstrates loop usage and conditional logic.",
            "difficulty": "easy"
        }
    
    def _structure_response(self, text: str) -> Dict:
        """Structure free-text response into exercise format"""
        return {
            "exercise": text[:200],
            "hints": ["Work through the problem step by step", "Check your logic carefully", "Review the concept fundamentals"],
            "solution": text[200:400] if len(text) > 200 else "See explanation",
            "explanation": text,
            "difficulty": "medium"
        }
    
    def analyze_student_answer(self, student_answer: str, exercise: str, 
                              concept: str) -> Dict:
        """Use Claude to analyze a student's answer"""
        if not self.client:
            return self._mock_analysis_response()
        
        prompt = f"""You are a tutor analyzing a student's answer.

EXERCISE: {exercise}
CONCEPT: {concept}

STUDENT'S ANSWER:
{student_answer}

Analyze this answer and provide:
1. Is it correct? (yes/no/partially)
2. What conceptual errors exist?
3. What procedural mistakes are present?
4. Helpful feedback

RESPONSE FORMAT:
{{
    "is_correct": true/false,
    "error_type": "none|conceptual|procedural|careless",
    "feedback": "Your feedback here",
    "next_step": "What to do next"
}}

Respond ONLY with the JSON object above."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            try:
                json_str = response_text
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                return json.loads(json_str.strip())
            except json.JSONDecodeError:
                return self._mock_analysis_response()
        
        except Exception as e:
            print(f"Claude API error during analysis: {e}")
            return self._mock_analysis_response()
    
    def _mock_analysis_response(self) -> Dict:
        """Mock analysis response"""
        return {
            "is_correct": False,
            "error_type": "procedural",
            "feedback": "There's a logical error in your approach. Check the loop bounds.",
            "next_step": "Review loop indexing and try again"
        }
    
    def generate_diagnostic_questions(self, concept: str) -> List[Dict]:
        """
        Generate diagnostic questions for a concept
        Returns list of questions with answers
        """
        if not self.client:
            return self._mock_diagnostic_questions()
        
        prompt = f"""Generate 3 multiple-choice diagnostic questions for: {concept}

These are for Moroccan high school students.

RESPONSE FORMAT:
[
    {{
        "question": "Question text?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_index": 0,
        "explanation": "Why this is correct..."
    }},
    ...
]

Respond ONLY with the JSON array above."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            try:
                json_str = response_text
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                return json.loads(json_str.strip())
            except json.JSONDecodeError:
                return self._mock_diagnostic_questions()
        
        except Exception as e:
            print(f"Claude API error: {e}")
            return self._mock_diagnostic_questions()
    
    def _mock_diagnostic_questions(self) -> List[Dict]:
        """Mock diagnostic questions"""
        return [
            {
                "question": "What is the purpose of a loop in programming?",
                "options": [
                    "To repeat a block of code multiple times",
                    "To store data in memory",
                    "To define a function",
                    "To create a variable"
                ],
                "correct_index": 0,
                "explanation": "Loops allow us to repeat code without writing it multiple times."
            }
        ]
