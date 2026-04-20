"""
Extended Recommendation Service - With Error-Type Targeting
Added admin exercise prioritization and error classification routing
"""
from typing import Dict, List, Optional
import json

class RecommendationEngine:
    """Generates personalized learning recommendations with error awareness"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_next_recommendation(self, student_id: int, diagnostic_errors: Optional[List[str]] = None) -> Dict:
        """
        Determine the most beneficial next action for the student.
        Now considers error types from diagnostic tests.
        
        Args:
            student_id: Student ID
            diagnostic_errors: List of error types detected (conceptual, procedural, careless)
            
        Returns: {action, concept_id, priority, reason, exercise_source}
        """
        cursor = self.db.cursor()
        
        # Get student's mastery profile
        cursor.execute("""
            SELECT c.id, c.name, c.domain, m.mastery_level, m.attempts_count
            FROM mastery_state m
            JOIN concepts c ON m.concept_id = c.id
            WHERE m.student_id = ?
            ORDER BY m.mastery_level ASC, m.attempts_count ASC
        """, (student_id,))
        
        concepts = cursor.fetchall()
        
        if not concepts:
            return {
                "action": "diagnostic_test",
                "concept_id": None,
                "priority": "critical",
                "reason": "Student hasn't started yet. Begin with diagnostic test.",
                "exercise_source": "system"
            }
        
        # If diagnostic errors are provided, recommend error-type-specific exercises
        if diagnostic_errors:
            return self._recommend_for_error_types(student_id, concepts, diagnostic_errors)
        
        # Find best recommendation based on mastery
        for concept_id, concept_name, domain, mastery, attempts in concepts:
            
            # Priority 1: Concepts with very low mastery and multiple failures
            if mastery < 0.3 and attempts > 3:
                return {
                    "action": "remedial_exercise",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "priority": "critical",
                    "reason": f"Need to strengthen '{concept_name}' - only {mastery:.1%} mastery after {attempts} attempts",
                    "exercise_source": self._get_exercise_source(concept_id, None)
                }
            
            # Priority 2: Concepts not yet attempted
            if attempts == 0:
                return {
                    "action": "introductory_exercise",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "priority": "high",
                    "reason": f"Time to learn '{concept_name}' - foundational concept",
                    "exercise_source": self._get_exercise_source(concept_id, None)
                }
            
            # Priority 3: Consolidation needed (medium mastery)
            if 0.3 <= mastery < 0.6 and attempts >= 2:
                return {
                    "action": "practice_exercise",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "priority": "high",
                    "reason": f"Practice '{concept_name}' to improve from {mastery:.1%} to mastery",
                    "exercise_source": self._get_exercise_source(concept_id, None)
                }
        
        # Priority 4: Advanced challenges for strong concepts
        strong_concepts = [c for c in concepts if c[3] >= 0.7]
        if strong_concepts:
            concept = strong_concepts[-1]
            return {
                "action": "challenge_exercise",
                "concept_id": concept[0],
                "concept_name": concept[1],
                "priority": "medium",
                "reason": f"You've mastered '{concept[1]}'! Try a challenge.",
                "exercise_source": self._get_exercise_source(concept[0], None)
            }
        
        # Default: practice
        worst_concept = concepts[0]
        return {
            "action": "practice_exercise",
            "concept_id": worst_concept[0],
            "concept_name": worst_concept[1],
            "priority": "normal",
            "reason": f"Continue practicing '{worst_concept[1]}'",
            "exercise_source": self._get_exercise_source(worst_concept[0], None)
        }
    
    def _recommend_for_error_types(
        self, 
        student_id: int, 
        concepts: List, 
        error_types: List[str]
    ) -> Dict:
        """
        Recommend targeted exercises based on error types from diagnostic.
        
        Error type mapping:
        - conceptual -> Need fundamental explanation exercises
        - procedural -> Need step-by-step practice exercises
        - careless -> Need speed/accuracy drills
        """
        cursor = self.db.cursor()
        
        # Get concepts where student had specific errors
        weak_concepts = [c for c in concepts if c[3] < 0.5]
        
        if not weak_concepts:
            weak_concepts = concepts
        
        target_concept = weak_concepts[0]  # Focus on weakest
        concept_id = target_concept[0]
        concept_name = target_concept[1]
        
        # Determine primary error type to target
        primary_error = error_types[0] if error_types else "procedural"
        
        recommendation = {
            "action": "error_targeted_exercise",
            "concept_id": concept_id,
            "concept_name": concept_name,
            "target_error_type": primary_error,
            "priority": "high",
            "exercise_source": self._get_exercise_source(concept_id, primary_error)
        }
        
        if primary_error == "conceptual":
            recommendation["reason"] = (
                f"You showed conceptual misunderstandings in '{concept_name}'. "
                "Here are explanation-focused exercises."
            )
        elif primary_error == "procedural":
            recommendation["reason"] = (
                f"You need procedural practice in '{concept_name}'. "
                "These exercises guide you step-by-step."
            )
        elif primary_error == "careless":
            recommendation["reason"] = (
                f"You made careless mistakes in '{concept_name}'. "
                "Let's practice accuracy with these drills."
            )
        
        return recommendation
    
    def _get_exercise_source(self, concept_id: int, error_type: Optional[str]) -> str:
        """
        Determine if admin exercises exist, return 'admin' or 'ai'.
        Prioritizes admin exercises when available.
        """
        cursor = self.db.cursor()
        
        query = """
            SELECT id FROM exercises 
            WHERE concept_id = ? AND is_active = 1 AND created_by_admin_id IS NOT NULL
        """
        params = [concept_id]
        
        if error_type:
            query += " AND error_type_targeted = ?"
            params.append(error_type)
        
        cursor.execute(query, params)
        
        if cursor.fetchone():
            return "admin"  # Admin exercises have priority
        else:
            return "ai"  # Fall back to AI-generated
    
    def get_targeted_exercises(
        self, 
        student_id: int, 
        concept_id: int, 
        error_type: Optional[str] = None,
        limit: int = 3
    ) -> List[Dict]:
        """
        Get exercises targeted for specific error type.
        Prioritizes admin exercises.
        """
        cursor = self.db.cursor()
        
        # First try admin exercises with error type targeting
        query = """
            SELECT id, title, exercise_type, difficulty, error_type_targeted
            FROM exercises
            WHERE concept_id = ? AND is_active = 1 AND created_by_admin_id IS NOT NULL
        """
        params = [concept_id]
        
        if error_type:
            query += " AND error_type_targeted = ?"
            params.append(error_type)
        
        query += " LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        admin_exercises = cursor.fetchall()
        
        exercises = []
        for ex in admin_exercises:
            exercises.append({
                "id": ex[0],
                "title": ex[1],
                "exercise_type": ex[2],
                "difficulty": ex[3],
                "error_type_targeted": ex[4],
                "source": "admin"
            })
        
        # If not enough admin exercises, add AI-generated ones
        if len(exercises) < limit:
            query = """
                SELECT id, title, exercise_type, difficulty, error_type_targeted
                FROM exercises
                WHERE concept_id = ? AND is_active = 1 AND created_by_admin_id IS NULL
            """
            params = [concept_id]
            
            if error_type:
                query += " AND error_type_targeted = ?"
                params.append(error_type)
            
            remaining = limit - len(exercises)
            query += " LIMIT ?"
            params.append(remaining)
            
            cursor.execute(query, params)
            ai_exercises = cursor.fetchall()
            
            for ex in ai_exercises:
                exercises.append({
                    "id": ex[0],
                    "title": ex[1],
                    "exercise_type": ex[2],
                    "difficulty": ex[3],
                    "error_type_targeted": ex[4],
                    "source": "ai"
                })
        
        return exercises
    
    def recommend_study_path(self, student_id: int, domain: str = None) -> List[Dict]:
        """
        Recommend a structured learning path for a domain.
        domain: 'Algorithmics' or 'Networks'
        """
        cursor = self.db.cursor()
        
        if domain:
            cursor.execute("""
                SELECT c.id, c.name, m.mastery_level, m.attempts_count
                FROM concepts c
                LEFT JOIN mastery_state m ON c.id = m.concept_id AND m.student_id = ?
                WHERE c.domain = ?
                ORDER BY c.id
            """, (student_id, domain))
        else:
            cursor.execute("""
                SELECT c.id, c.name, m.mastery_level, m.attempts_count
                FROM concepts c
                LEFT JOIN mastery_state m ON c.id = m.concept_id AND m.student_id = ?
                ORDER BY c.id
            """, (student_id,))
        
        concepts = cursor.fetchall()
        recommendations = []
        
        for concept_id, concept_name, mastery, attempts in concepts:
            mastery = mastery or 0.0
            attempts = attempts or 0
            
            if attempts == 0:
                status = "not_started"
                action = "Begin"
            elif mastery < 0.4:
                status = "struggling"
                action = "Review & Practice"
            elif mastery < 0.7:
                status = "developing"
                action = "Consolidate"
            else:
                status = "mastered"
                action = "Challenge"
            
            recommendations.append({
                "concept_id": concept_id,
                "concept_name": concept_name,
                "mastery_level": round(mastery, 2),
                "attempts": attempts,
                "status": status,
                "recommended_action": action
            })
        
        return recommendations
    
    def should_move_to_next_topic(self, student_id: int, current_concept_id: int) -> bool:
        """
        Determine if student is ready to move to next topic.
        Returns True if mastery >= 0.7 and sufficient attempts.
        """
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT mastery_level, attempts_count
            FROM mastery_state
            WHERE student_id = ? AND concept_id = ?
        """, (student_id, current_concept_id))
        
        result = cursor.fetchone()
        
        if not result:
            return False
        
        mastery, attempts = result
        
        # Move on if mastery is good and they've practiced enough
        return mastery >= 0.7 and attempts >= 3
    
    def analyze_progress(self, student_id: int) -> Dict:
        """Analyze overall student progress"""
        cursor = self.db.cursor()
        
        # Overall stats
        cursor.execute("""
            SELECT COUNT(*), AVG(mastery_level), SUM(attempts_count)
            FROM mastery_state
            WHERE student_id = ?
        """, (student_id,))
        
        total_concepts, avg_mastery, total_attempts = cursor.fetchone()
        avg_mastery = avg_mastery or 0.0
        total_attempts = total_attempts or 0
        
        # Concepts by status
        cursor.execute("""
            SELECT
                SUM(CASE WHEN mastery_level >= 0.7 THEN 1 ELSE 0 END) as mastered,
                SUM(CASE WHEN mastery_level >= 0.4 AND mastery_level < 0.7 THEN 1 ELSE 0 END) as developing,
                SUM(CASE WHEN mastery_level < 0.4 THEN 1 ELSE 0 END) as struggling,
                SUM(CASE WHEN attempts_count = 0 THEN 1 ELSE 0 END) as not_started
            FROM mastery_state
            WHERE student_id = ?
        """, (student_id,))
        
        stats = cursor.fetchone()
        
        return {
            "total_concepts": total_concepts or 0,
            "average_mastery": round(avg_mastery, 2),
            "total_attempts": total_attempts,
            "concepts_mastered": stats[0] or 0,
            "concepts_developing": stats[1] or 0,
            "concepts_struggling": stats[2] or 0,
            "concepts_not_started": stats[3] or 0
        }
