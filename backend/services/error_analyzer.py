"""
Error Analysis Service - Detects and classifies student mistakes
"""
from typing import Dict, List, Optional
import sqlite3

class ErrorAnalyzer:
    """Analyzes student errors and detects patterns"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def classify_error(self, student_answer: str, correct_answer: str, 
                      concept: str, context: str = "") -> Dict:
        """
        Classify student error into categories:
        - conceptual: misunderstands the concept
        - procedural: knows concept but wrong steps
        - careless: arithmetic/syntax mistake
        """
        
        # Normalize answers for comparison
        student_answer_clean = student_answer.strip().lower()
        correct_answer_clean = correct_answer.strip().lower()
        
        # Exact match
        if student_answer_clean == correct_answer_clean:
            return {
                'is_correct': True,
                'error_type': None,
                'confidence': 1.0
            }
        
        # Check for common mistake patterns
        error_analysis = self._analyze_patterns(
            student_answer_clean, 
            correct_answer_clean, 
            concept
        )
        
        return error_analysis
    
    def _analyze_patterns(self, student_ans: str, correct_ans: str, 
                         concept: str) -> Dict:
        """Analyze specific patterns based on concept"""
        
        # Algorithmics-specific patterns
        if "loop" in concept.lower() or "for" in concept.lower():
            return self._analyze_loop_errors(student_ans, correct_ans)
        elif "conditional" in concept.lower() or "if" in concept.lower():
            return self._analyze_conditional_errors(student_ans, correct_ans)
        elif "array" in concept.lower() or "list" in concept.lower():
            return self._analyze_array_errors(student_ans, correct_ans)
        elif "pseudocode" in concept.lower():
            return self._analyze_pseudocode_errors(student_ans, correct_ans)
        
        # Networks-specific patterns
        elif "ip" in concept.lower() or "addressing" in concept.lower():
            return self._analyze_ip_errors(student_ans, correct_ans)
        elif "subnet" in concept.lower():
            return self._analyze_subnet_errors(student_ans, correct_ans)
        elif "osi" in concept.lower():
            return self._analyze_osi_errors(student_ans, correct_ans)
        
        # Default pattern analysis
        return self._generic_analysis(student_ans, correct_ans)
    
    def _analyze_loop_errors(self, student: str, correct: str) -> Dict:
        """Analyze loop-related errors"""
        issues = []
        
        # Check for off-by-one errors
        if any(x in student for x in ["i=0", "i < n+1", "i <= n"]):
            if "i=1" in correct or "i < n" in correct:
                issues.append("off-by-one")
        
        # Check for wrong loop counter
        if any(x in correct for x in ["for i", "for j", "for k"]):
            if not any(x in student for x in ["for i", "for j", "for k"]):
                issues.append("missing_loop_variable")
        
        # Check for missing loop body
        if "{" in correct and "{" not in student:
            issues.append("missing_loop_body")
        
        if "off-by-one" in issues:
            return {
                'is_correct': False,
                'error_type': 'procedural',
                'confidence': 0.8,
                'details': 'Off-by-one error in loop bounds'
            }
        elif "missing_loop_variable" in issues:
            return {
                'is_correct': False,
                'error_type': 'conceptual',
                'confidence': 0.7,
                'details': 'Loop variable not properly defined'
            }
        
        return {
            'is_correct': False,
            'error_type': 'procedural',
            'confidence': 0.5,
            'details': 'Error in loop logic'
        }
    
    def _analyze_conditional_errors(self, student: str, correct: str) -> Dict:
        """Analyze conditional statement errors"""
        issues = []
        
        # Check for logic operator confusion (AND vs OR)
        if "&&" in correct and "||" in student:
            issues.append("logic_operator")
        elif "and" in correct and "or" in student:
            issues.append("logic_operator")
        
        # Check for comparison operator confusion
        if "==" in correct and "=" in student and "==" not in student:
            issues.append("assignment_vs_comparison")
        
        # Check for missing else clause when needed
        if "else" in correct and "else" not in student:
            issues.append("incomplete_condition")
        
        if "logic_operator" in issues:
            return {
                'is_correct': False,
                'error_type': 'conceptual',
                'confidence': 0.85,
                'details': 'Incorrect logical operator (AND vs OR)'
            }
        elif "assignment_vs_comparison" in issues:
            return {
                'is_correct': False,
                'error_type': 'careless',
                'confidence': 0.9,
                'details': 'Using = instead of == for comparison'
            }
        
        return {
            'is_correct': False,
            'error_type': 'procedural',
            'confidence': 0.6,
            'details': 'Error in conditional logic'
        }
    
    def _analyze_array_errors(self, student: str, correct: str) -> Dict:
        """Analyze array/list related errors"""
        issues = []
        
        # Check for indexing errors (0-based vs 1-based)
        if "[0]" in correct and "[1]" in student:
            issues.append("array_index_base")
        
        # Check for out of bounds
        if any(x in student for x in ["[n]", "[size]", "[length]"]):
            if any(x in correct for x in ["[n-1]", "[size-1]", "[length-1]"]):
                issues.append("array_bounds")
        
        if "array_index_base" in issues:
            return {
                'is_correct': False,
                'error_type': 'conceptual',
                'confidence': 0.85,
                'details': 'Array indexing error (off-by-one in base)'
            }
        elif "array_bounds" in issues:
            return {
                'is_correct': False,
                'error_type': 'conceptual',
                'confidence': 0.8,
                'details': 'Array boundary error (accessing out of bounds)'
            }
        
        return {
            'is_correct': False,
            'error_type': 'procedural',
            'confidence': 0.5,
            'details': 'Error in array handling'
        }
    
    def _analyze_pseudocode_errors(self, student: str, correct: str) -> Dict:
        """Analyze pseudocode errors"""
        # In pseudocode, any significant difference is likely conceptual
        similarity = self._string_similarity(student, correct)
        
        if similarity > 0.7:
            return {
                'is_correct': False,
                'error_type': 'careless',
                'confidence': 0.6,
                'details': 'Minor syntax/formatting error'
            }
        else:
            return {
                'is_correct': False,
                'error_type': 'conceptual',
                'confidence': 0.7,
                'details': 'Logical structure error in pseudocode'
            }
    
    def _analyze_ip_errors(self, student: str, correct: str) -> Dict:
        """Analyze IP addressing errors"""
        issues = []
        
        # Check for valid IP format
        if not self._is_valid_ip(student):
            issues.append("invalid_format")
        
        # Check for subnet calculation errors
        if "/" in correct and "/" not in student:
            issues.append("missing_subnet_mask")
        
        if "invalid_format" in issues:
            return {
                'is_correct': False,
                'error_type': 'careless',
                'confidence': 0.85,
                'details': 'Invalid IP address format'
            }
        
        return {
            'is_correct': False,
            'error_type': 'procedural',
            'confidence': 0.7,
            'details': 'Incorrect IP address or subnet calculation'
        }
    
    def _analyze_subnet_errors(self, student: str, correct: str) -> Dict:
        """Analyze subnetting errors"""
        return {
            'is_correct': False,
            'error_type': 'procedural',
            'confidence': 0.75,
            'details': 'Error in subnet mask calculation'
        }
    
    def _analyze_osi_errors(self, student: str, correct: str) -> Dict:
        """Analyze OSI model errors"""
        return {
            'is_correct': False,
            'error_type': 'conceptual',
            'confidence': 0.7,
            'details': 'Incorrect understanding of OSI layers'
        }
    
    def _generic_analysis(self, student: str, correct: str) -> Dict:
        """Generic error classification"""
        similarity = self._string_similarity(student, correct)
        
        if similarity > 0.8:
            error_type = 'careless'
        elif similarity > 0.5:
            error_type = 'procedural'
        else:
            error_type = 'conceptual'
        
        return {
            'is_correct': False,
            'error_type': error_type,
            'confidence': min(0.9, similarity + 0.2),
            'details': f'Student answer differs from correct solution'
        }
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate simple string similarity"""
        if len(s1) == 0 and len(s2) == 0:
            return 1.0
        if len(s1) == 0 or len(s2) == 0:
            return 0.0
        
        # Simple matching
        matches = sum(1 for a, b in zip(s1, s2) if a == b)
        return matches / max(len(s1), len(s2))
    
    def _is_valid_ip(self, ip_str: str) -> bool:
        """Check if string is valid IP format"""
        parts = ip_str.split(".")
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    def log_mistake(self, student_id: int, concept_id: int, 
                   mistake_type: str, description: str):
        """Log a student mistake for pattern tracking"""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO mistakes_log
            (student_id, concept_id, mistake_type, description)
            VALUES (?, ?, ?, ?)
        """, (student_id, concept_id, mistake_type, description))
        self.db.commit()
    
    def get_mistake_patterns(self, student_id: int) -> List[Dict]:
        """Get student's mistake patterns"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT c.name, mistake_type, COUNT(*) as frequency
            FROM mistakes_log ml
            JOIN concepts c ON ml.concept_id = c.id
            WHERE ml.student_id = ?
            GROUP BY concept_id, mistake_type
            ORDER BY frequency DESC
            LIMIT 10
        """, (student_id,))
        
        results = cursor.fetchall()
        return [
            {
                'concept': row[0],
                'mistake_type': row[1],
                'frequency': row[2]
            }
            for row in results
        ]
