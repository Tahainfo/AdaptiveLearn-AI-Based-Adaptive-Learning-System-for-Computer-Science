"""
Recommendation Service - Determines next learning actions for students
"""
from typing import Dict, List, Optional

class RecommendationEngine:
    """Generates personalized learning recommendations"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_next_recommendation(self, student_id: int) -> Dict:
        """
        Determine the most beneficial next action for the student
        Returns: {action, concept_id, priority, reason}
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
                "reason": "Student hasn't started yet. Begin with diagnostic test."
            }
        
        # Find best recommendation
        for concept_id, concept_name, domain, mastery, attempts in concepts:
            
            # Priority 1: Concepts with very low mastery and multiple failures
            if mastery < 0.3 and attempts > 3:
                return {
                    "action": "remedial_exercise",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "priority": "critical",
                    "reason": f"Need to strengthen '{concept_name}' - only {mastery:.1%} mastery after {attempts} attempts"
                }
            
            # Priority 2: Concepts not yet attempted
            if attempts == 0:
                return {
                    "action": "introductory_exercise",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "priority": "high",
                    "reason": f"Time to learn '{concept_name}' - foundational concept"
                }
            
            # Priority 3: Consolidation needed (medium mastery)
            if 0.3 <= mastery < 0.6 and attempts >= 2:
                return {
                    "action": "practice_exercise",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "priority": "high",
                    "reason": f"Practice '{concept_name}' to improve from {mastery:.1%} to mastery"
                }
        
        # Priority 4: Advanced challenges for strong concepts
        strong_concepts = [c for c in concepts if c[3] >= 0.7]
        if strong_concepts:
            concept = strong_concepts[-1]  # Best performing
            return {
                "action": "challenge_exercise",
                "concept_id": concept[0],
                "concept_name": concept[1],
                "priority": "medium",
                "reason": f"You've mastered '{concept[1]}'! Try a challenge."
            }
        
        # Default: practice
        worst_concept = concepts[0]
        return {
            "action": "practice_exercise",
            "concept_id": worst_concept[0],
            "concept_name": worst_concept[1],
            "priority": "normal",
            "reason": f"Continue practicing '{worst_concept[1]}'"
        }
    
    def recommend_study_path(self, student_id: int, domain: str = None) -> List[Dict]:
        """
        Recommend a structured learning path for a domain
        domain: 'Algorithmics' or 'Networks'
        """
        cursor = self.db.cursor()
        
        # Get concepts in order of dependency
        algorithmics_order = [
            "Conditionals - If/Else",
            "Loops - For",
            "Loops - While",
            "Arrays/Lists",
            "Pseudocode"
        ]
        
        networks_order = [
            "OSI Model",
            "IP Addressing",
            "Subnetting",
            "Protocol Basics"
        ]
        
        if domain == "Algorithmics":
            concept_order = algorithmics_order
        elif domain == "Networks":
            concept_order = networks_order
        else:
            concept_order = algorithmics_order + networks_order
        
        recommendations = []
        
        cursor.execute("""
            SELECT c.id, c.name, m.mastery_level, m.attempts_count
            FROM concepts c
            LEFT JOIN mastery_state m ON c.id = m.concept_id AND m.student_id = ?
            WHERE c.name IN ({})
            ORDER BY c.name
        """.format(','.join('?' * len(concept_order))), 
        [student_id] + concept_order)
        
        concepts = cursor.fetchall()
        
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
                "mastery_level": mastery,
                "attempts": attempts,
                "status": status,
                "recommended_action": action
            })
        
        return recommendations
    
    def should_move_to_next_topic(self, student_id: int, current_concept_id: int) -> bool:
        """
        Determine if student is ready to move to next topic
        Returns True if mastery >= 0.7 and sufficient attempts
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
        
        # Concepts by status
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN mastery_level >= 0.7 THEN 1 ELSE 0 END) as mastered,
                SUM(CASE WHEN mastery_level >= 0.4 AND mastery_level < 0.7 THEN 1 ELSE 0 END) as developing,
                SUM(CASE WHEN mastery_level < 0.4 THEN 1 ELSE 0 END) as struggling
            FROM mastery_state
            WHERE student_id = ?
        """, (student_id,))
        
        mastered, developing, struggling = cursor.fetchone()
        
        # Improvement rate (recent vs older)
        cursor.execute("""
            SELECT mastery_level FROM mastery_state
            WHERE student_id = ?
            ORDER BY last_updated DESC
            LIMIT 3
        """, (student_id,))
        
        recent = [r[0] for r in cursor.fetchall()]
        recent_avg = sum(recent) / len(recent) if recent else 0
        
        return {
            "total_concepts": total_concepts or 0,
            "average_mastery": round(avg_mastery or 0, 3),
            "total_attempts": total_attempts or 0,
            "concepts_mastered": mastered or 0,
            "concepts_developing": developing or 0,
            "concepts_struggling": struggling or 0,
            "recent_performance": round(recent_avg, 3),
            "trend": "improving" if recent_avg > (avg_mastery or 0) else "stable"
        }
    
    # ===== SEQUENCE-AWARE RECOMMENDATIONS (NEW) =====
    # These methods extend the engine for curriculum hierarchy
    # Existing get_next_recommendation() remains unchanged for backward compatibility
    
    def get_sequence_aware_recommendation(self, student_id: int) -> Dict:
        """
        NEW: Curriculum-aware recommendation
        
        Algorithm:
        1. Find weakest sequence (lowest average mastery)
        2. Within that sequence, find weakest concept
        3. Return exercise targeting that concept
        4. Includes sequence context
        
        Returns: {
            action, concept_id, concept_name,
            sequence_id, sequence_name,
            priority, reason
        }
        """
        cursor = self.db.cursor()
        
        # Calculate average mastery per sequence
        cursor.execute("""
            SELECT 
                s.id,
                s.title,
                m.module_id,
                AVG(COALESCE(ms.mastery_level, 0)) as seq_mastery,
                COUNT(DISTINCT c.id) as concept_count
            FROM sequences s
            LEFT JOIN modules m ON m.id = s.module_id
            LEFT JOIN concepts c ON c.sequence_id = s.id
            LEFT JOIN mastery_state ms ON ms.concept_id = c.id 
                AND ms.student_id = ?
            GROUP BY s.id, s.title, m.module_id
            ORDER BY seq_mastery ASC, concept_count DESC
        """, (student_id,))
        
        sequences = cursor.fetchall()
        
        if not sequences:
            # No sequences (fallback to concept-based)
            return self.get_next_recommendation(student_id)
        
        # Find weakest sequence with concepts
        for seq_id, seq_name, module_id, seq_mastery, concept_count in sequences:
            if concept_count == 0:
                continue  # Skip empty sequences
            
            # Within this sequence, find weakest concept
            cursor.execute("""
                SELECT 
                    c.id, c.name,
                    COALESCE(ms.mastery_level, 0) as mastery,
                    COALESCE(ms.attempts_count, 0) as attempts
                FROM concepts c
                LEFT JOIN mastery_state ms ON ms.concept_id = c.id 
                    AND ms.student_id = ?
                WHERE c.sequence_id = ?
                ORDER BY mastery ASC, attempts ASC
            """, (student_id, seq_id))
            
            concept = cursor.fetchone()
            if not concept:
                continue
            
            concept_id, concept_name, mastery, attempts = concept
            
            # Determine action based on mastery
            if attempts == 0:
                action = "introductory_exercise"
                priority = "high"
            elif mastery < 0.3:
                action = "remedial_exercise"
                priority = "critical"
            elif mastery < 0.6:
                action = "practice_exercise"
                priority = "high"
            else:
                action = "consolidation_exercise"
                priority = "medium"
            
            return {
                "action": action,
                "concept_id": concept_id,
                "concept_name": concept_name,
                "sequence_id": seq_id,
                "sequence_name": seq_name,
                "sequence_mastery": round(seq_mastery, 3),
                "priority": priority,
                "reason": f"Focus on '{seq_name}' sequence → '{concept_name}' (mastery: {mastery:.1%})"
            }
        
        # Fallback to concept-based
        return self.get_next_recommendation(student_id)
    
    def get_sequence_mastery_profile(self, student_id: int) -> List[Dict]:
        """
        Get mastery breakdown by sequence and concept
        Useful for curriculum dashboard display
        
        Returns: [
            {
                sequence_id: int,
                sequence_name: str,
                average_mastery: float,
                concepts: [
                    {concept_id, concept_name, mastery, attempts},
                    ...
                ]
            }
        ]
        """
        cursor = self.db.cursor()
        
        # Get all sequences
        cursor.execute("""
            SELECT s.id, s.title
            FROM sequences s
            ORDER BY s.id
        """)
        
        sequences = cursor.fetchall()
        profile = []
        
        for seq_id, seq_name in sequences:
            # Get concepts in this sequence
            cursor.execute("""
                SELECT 
                    c.id, c.name,
                    COALESCE(ms.mastery_level, 0) as mastery,
                    COALESCE(ms.attempts_count, 0) as attempts
                FROM concepts c
                LEFT JOIN mastery_state ms ON ms.concept_id = c.id 
                    AND ms.student_id = ?
                WHERE c.sequence_id = ?
                ORDER BY c.id
            """, (student_id, seq_id))
            
            concepts_data = cursor.fetchall()
            if not concepts_data:
                continue
            
            concept_list = [
                {
                    "concept_id": c[0],
                    "concept_name": c[1],
                    "mastery": round(c[2], 3),
                    "attempts": c[3]
                }
                for c in concepts_data
            ]
            
            avg_mastery = sum(c[2] for c in concepts_data) / len(concepts_data) if concepts_data else 0
            
            profile.append({
                "sequence_id": seq_id,
                "sequence_name": seq_name,
                "average_mastery": round(avg_mastery, 3),
                "concept_count": len(concept_list),
                "concepts": concept_list
            })
        
        return profile
    
    def should_start_sequence_diagnostic(self, student_id: int, sequence_id: int) -> Dict:
        """
        Determine if student should take sequence diagnostic
        
        Returns: {
            should_take: bool,
            reason: str,
            suggested_action: str
        }
        """
        cursor = self.db.cursor()
        
        # Check if student has already done this sequence diagnostic
        cursor.execute("""
            SELECT COUNT(*) FROM diagnostic_attempts
            WHERE student_id = ? AND sequence_id = ?
        """, (student_id, sequence_id))
        
        diagnostic_count = cursor.fetchone()[0]
        
        # Check sequence mastery
        cursor.execute("""
            SELECT 
                AVG(COALESCE(ms.mastery_level, 0)) as seq_mastery,
                COUNT(DISTINCT c.id) as concept_count
            FROM concepts c
            LEFT JOIN mastery_state ms ON ms.concept_id = c.id 
                AND ms.student_id = ?
            WHERE c.sequence_id = ?
        """, (student_id, sequence_id))
        
        result = cursor.fetchone()
        seq_mastery, concept_count = result if result else (0, 0)
        
        if concept_count == 0:
            return {
                "should_take": False,
                "reason": "No concepts in this sequence",
                "suggested_action": "Select another sequence"
            }
        
        if diagnostic_count == 0:
            return {
                "should_take": True,
                "reason": "Initial diagnostic assessment",
                "suggested_action": "Take sequence diagnostic to establish baseline"
            }
        
        # Re-assessment if mastery changed significantly
        if seq_mastery > 0.7:
            return {
                "should_take": False,
                "reason": f"Strong mastery ({seq_mastery:.1%})",
                "suggested_action": "Move to next sequence or take challenge"
            }
        
        if seq_mastery < 0.4:
            return {
                "should_take": True,
                "reason": f"Low mastery ({seq_mastery:.1%})",
                "suggested_action": "Re-take diagnostic to track progress"
            }
        
        return {
            "should_take": True,
            "reason": f"Medium mastery ({seq_mastery:.1%}) - progress tracking",
            "suggested_action": "Optional: Re-take diagnostic or continue with exercises"
        }
