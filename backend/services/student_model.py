"""
Student Model Service - Manages student mastery tracking and profiles
"""
import sqlite3
from typing import List, Dict, Optional, Tuple

class StudentModel:
    """Manages student learning profiles and mastery tracking"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_student_mastery_profile(self, student_id: int) -> Dict:
        """
        Get complete mastery profile for a student
        Returns: {concept_name: mastery_level, ...}
        """
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT c.id, c.name, m.mastery_level, m.attempts_count, m.correct_count
            FROM mastery_state m
            JOIN concepts c ON m.concept_id = c.id
            WHERE m.student_id = ?
            ORDER BY c.name
        """, (student_id,))
        
        results = cursor.fetchall()
        profile = {}
        for row in results:
            profile[row[1]] = {
                'concept_id': row[0],
                'mastery_level': row[2],
                'attempts': row[3],
                'correct': row[4]
            }
        
        return profile
    
    def update_mastery_level(self, student_id: int, concept_id: int, is_correct: bool):
        """
        Update mastery level based on exercise attempt
        Uses simple Bayesian update approach
        """
        cursor = self.db.cursor()
        
        # Get current mastery state
        cursor.execute("""
            SELECT mastery_level, attempts_count, correct_count
            FROM mastery_state
            WHERE student_id = ? AND concept_id = ?
        """, (student_id, concept_id))
        
        result = cursor.fetchone()
        
        if result:
            current_mastery, attempts, correct = result
            new_attempts = attempts + 1
            new_correct = correct + (1 if is_correct else 0)
        else:
            # First attempt - initialize
            current_mastery = 0.0
            new_attempts = 1
            new_correct = 1 if is_correct else 0
        
        # Calculate new mastery level using weighted average
        # More weight to recent performance
        if new_attempts > 0:
            # Simple moving average with recent attempts weighted more
            recent_weight = 0.7
            historical_weight = 0.3
            
            if new_attempts == 1:
                new_mastery = 1.0 if is_correct else 0.0
            else:
                historical_mastery = current_mastery
                recent_mastery = new_correct / new_attempts
                new_mastery = (historical_weight * historical_mastery + 
                              recent_weight * recent_mastery)
        else:
            new_mastery = 0.0
        
        # Clamp between 0 and 1
        new_mastery = max(0.0, min(1.0, new_mastery))
        
        # Update or insert
        cursor.execute("""
            INSERT OR REPLACE INTO mastery_state
            (student_id, concept_id, mastery_level, attempts_count, correct_count, last_updated)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (student_id, concept_id, new_mastery, new_attempts, new_correct))
        
        self.db.commit()
        return new_mastery
    
    def get_weak_concepts(self, student_id: int, threshold: float = 0.5) -> List[Dict]:
        """Get concepts where student's mastery is below threshold"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT c.id, c.name, c.domain, m.mastery_level
            FROM mastery_state m
            JOIN concepts c ON m.concept_id = c.id
            WHERE m.student_id = ? AND m.mastery_level < ?
            ORDER BY m.mastery_level ASC
        """, (student_id, threshold))
        
        results = cursor.fetchall()
        return [
            {
                'concept_id': row[0],
                'name': row[1],
                'domain': row[2],
                'mastery_level': row[3]
            }
            for row in results
        ]
    
    def get_strengths(self, student_id: int, threshold: float = 0.7) -> List[Dict]:
        """Get concepts where student shows strong mastery"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT c.id, c.name, c.domain, m.mastery_level
            FROM mastery_state m
            JOIN concepts c ON m.concept_id = c.id
            WHERE m.student_id = ? AND m.mastery_level >= ?
            ORDER BY m.mastery_level DESC
        """, (student_id, threshold))
        
        results = cursor.fetchall()
        return [
            {
                'concept_id': row[0],
                'name': row[1],
                'domain': row[2],
                'mastery_level': row[3]
            }
            for row in results
        ]
    
    def get_difficulty_level(self, student_id: int, concept_id: int) -> str:
        """
        Determine appropriate difficulty level based on mastery
        easy: < 0.4
        medium: 0.4-0.7
        challenging: > 0.7
        """
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT mastery_level
            FROM mastery_state
            WHERE student_id = ? AND concept_id = ?
        """, (student_id, concept_id))
        
        result = cursor.fetchone()
        if not result:
            return "easy"  # First time - start easy
        
        mastery = result[0]
        if mastery < 0.4:
            return "easy"
        elif mastery < 0.7:
            return "medium"
        else:
            return "challenging"
    
    def initialize_student_mastery(self, student_id: int):
        """Initialize mastery tracking for all concepts"""
        cursor = self.db.cursor()
        
        # Get all concepts
        cursor.execute("SELECT id FROM concepts")
        concepts = cursor.fetchall()
        
        for concept in concepts:
            concept_id = concept[0]
            try:
                cursor.execute("""
                    INSERT INTO mastery_state
                    (student_id, concept_id, mastery_level, attempts_count, correct_count)
                    VALUES (?, ?, 0.0, 0, 0)
                """, (student_id, concept_id))
            except sqlite3.IntegrityError:
                pass  # Already initialized
        
        self.db.commit()
    
    def get_performance_stats(self, student_id: int) -> Dict:
        """Get overall performance statistics"""
        cursor = self.db.cursor()
        
        # Average mastery
        cursor.execute("""
            SELECT AVG(mastery_level), SUM(attempts_count), SUM(correct_count)
            FROM mastery_state
            WHERE student_id = ?
        """, (student_id,))
        
        avg_mastery, total_attempts, total_correct = cursor.fetchone()
        
        return {
            'average_mastery': avg_mastery or 0.0,
            'total_attempts': total_attempts or 0,
            'total_correct': total_correct or 0,
            'overall_accuracy': (total_correct / total_attempts) if total_attempts else 0.0
        }
