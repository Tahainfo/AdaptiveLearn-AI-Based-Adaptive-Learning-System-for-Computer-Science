"""
Prompt templates for AI interactions
"""

DIAGNOSTIC_PROMPT_TEMPLATE = """You are a diagnostic assessor for Moroccan high school students.

CONCEPT: {concept}

Generate 3 diagnostic questions to assess the students's understanding of this concept.

The questions should:
1. Test foundational understanding
2. Be clear and unambiguous
3. Have 4 multiple choice options

RESPONSE FORMAT:
[
    {{
        "question": "Question text?",
        "options": ["A", "B", "C", "D"],
        "correct_index": 0,
        "explanation": "Why A is correct"
    }},
    ...
]

CONCEPT BACKGROUND:
- For Algorithmics: Focus on logic, control flow, data structures
- For Networks: Focus on protocols, addressing, layers
- Use real-world examples relevant to Morocco

Respond with ONLY the JSON array."""

EXERCISE_GENERATION_TEMPLATE = """You are an expert tutor for Moroccan high school students.

STUDENT STATUS:
- Concept: {concept}
- Current Mastery: {mastery_percent}%
- Difficulty Level: {difficulty}
- Common Mistakes: {mistakes}

Generate a {difficulty} exercise that:
1. Targets {concept}
2. Addresses their common mistakes
3. Builds their mastery progressively
4. Includes pseudocode when relevant

RESPONSE FORMAT:
{{
    "exercise": "Exercise description and question",
    "hints": ["Hint 1", "Hint 2", "Hint 3"],
    "solution": "Complete solution in pseudocode or step-by-step",
    "explanation": "Why this solution works and key concepts",
    "difficulty": "{difficulty}"
}}

Respond with ONLY the JSON object."""

ERROR_ANALYSIS_TEMPLATE = """Analyze this student's error:

CONCEPT: {concept}
CORRECT ANSWER: {correct_answer}
STUDENT ANSWER: {student_answer}

Identify:
1. Is the answer correct?
2. What type of error? (conceptual/procedural/careless)
3. Root cause
4. Helpful feedback

RESPONSE FORMAT:
{{
    "is_correct": true/false,
    "error_type": "none|conceptual|procedural|careless",
    "root_cause": "Explanation of why the error occurred",
    "feedback": "Encouraging and specific feedback",
    "hint": "What to try next"
}}

Respond with ONLY the JSON object."""

HINT_TEMPLATE = """Generate {hint_level} hint for this exercise:

EXERCISE: {exercise}
CONCEPT: {concept}
HINT_LEVEL: {hint_level} (1=basic, 2=intermediate, 3=almost answer)

The hint should:
- Not give away the answer directly
- Guide thinking towards the solution
- Be encouraging and concise

Respond with ONLY the hint text."""

DIAGNOSTIC_QUESTIONS = {
    "Loops - For": [
        {
            "question": "What will this pseudocode output?\nFOR i = 1 TO 3\n    PRINT i\nEND FOR",
            "options": ["123", "012", "1234", "3"],
            "correct_index": 0,
            "explanation": "The for loop iterates from 1 to 3, printing each value."
        },
        {
            "question": "How many times does this loop execute?\nFOR i = 1 TO 5\n    // loop body\nEND FOR",
            "options": ["4 times", "5 times", "6 times", "Infinite times"],
            "correct_index": 1,
            "explanation": "From 1 to 5 inclusive means 5 iterations total."
        },
        {
            "question": "What is the correct syntax for a for loop?",
            "options": [
                "FOR i = 1 TO n",
                "FOR i FROM 1 UNTIL n",
                "LOOP i = 1 TO n",
                "REPEAT i = 1 TO n"
            ],
            "correct_index": 0,
            "explanation": "Standard pseudocode uses 'FOR i = start TO end' syntax."
        }
    ],
    "Loops - While": [
        {
            "question": "What does a while loop require?",
            "options": [
                "A counter variable",
                "A condition that becomes false",
                "A fixed iteration count",
                "An array"
            ],
            "correct_index": 1,
            "explanation": "While loops continue until the condition becomes false."
        },
        {
            "question": "What happens if the condition is always true?",
            "options": [
                "Loop executes once",
                "Infinite loop",
                "Loop doesn't execute",
                "Syntax error"
            ],
            "correct_index": 1,
            "explanation": "If the condition never becomes false, the loop continues forever."
        },
        {
            "question": "Which loop is best when you don't know how many iterations needed?",
            "options": [
                "FOR loop",
                "WHILE loop",
                "REPEAT loop",
                "None"
            ],
            "correct_index": 1,
            "explanation": "WHILE loops are used when iteration count is unknown but condition is clear."
        }
    ],
    "IP Addressing": [
        {
            "question": "Which is a valid IPv4 address?",
            "options": [
                "256.0.0.1",
                "192.168.1.1",
                "999.999.999.999",
                "-1.0.0.1"
            ],
            "correct_index": 1,
            "explanation": "Each octet in IPv4 must be between 0-255. 192.168.1.1 is valid."
        },
        {
            "question": "What does the subnet mask 255.255.255.0 represent?",
            "options": [
                "256 hosts",
                "255 hosts",
                "254 usable hosts",
                "1024 hosts"
            ],
            "correct_index": 2,
            "explanation": "255.255.255.0 allows 256 total addresses, minus network and broadcast = 254 usable."
        },
        {
            "question": "What is the network address for 192.168.1.100/24?",
            "options": [
                "192.168.1.0",
                "192.168.1.100",
                "192.168.1.255",
                "192.168.0.0"
            ],
            "correct_index": 0,
            "explanation": "/24 means the last octet is for hosts. Network address is 192.168.1.0."
        }
    ],
    "Conditionals - If/Else": [
        {
            "question": "What output for this code?\nIF x > 5 THEN\n    PRINT 'big'\nELSE\n    PRINT 'small'\nEND IF\n(assume x = 3)",
            "options": ["big", "small", "big small", "Error"],
            "correct_index": 1,
            "explanation": "Since 3 is not > 5, the ELSE branch executes, printing 'small'."
        },
        {
            "question": "What is the correct syntax for checking equality?",
            "options": ["x = 5", "x == 5", "x EQUALS 5", "x IS 5"],
            "correct_index": 1,
            "explanation": "In most languages and pseudocode, == is used for comparison, = for assignment."
        }
    ]
}

def get_diagnostic_questions(concept: str) -> list:
    """Get pre-built diagnostic questions for a concept"""
    return DIAGNOSTIC_QUESTIONS.get(concept, [])
