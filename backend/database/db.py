"""
Database configuration and initialization
"""
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Database path
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "adaptive_learning.db"

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database with schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Modules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            description TEXT,
            order_index INTEGER
        )
    """)
    
    # Sequences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sequences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            order_index INTEGER,
            FOREIGN KEY (module_id) REFERENCES modules(id),
            UNIQUE(module_id, title)
        )
    """)
    
    # Concepts table (renamed to notions conceptually, but keeping the table name)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sequence_id INTEGER,
            name TEXT NOT NULL,
            domain TEXT NOT NULL,
            description TEXT,
            hours INTEGER DEFAULT 0,
            FOREIGN KEY (sequence_id) REFERENCES sequences(id),
            UNIQUE(sequence_id, name)
        )
    """)
    
    # Mastery state - tracks student progress per concept
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mastery_state (
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
        )
    """)
    
    # Exercises table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            difficulty TEXT,
            exercise_prompt TEXT,
            solution TEXT,
            explanation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (concept_id) REFERENCES concepts(id)
        )
    """)
    
    # Exercise attempts - track student answers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            student_answer TEXT,
            is_correct INTEGER,
            error_type TEXT,
            time_spent_seconds INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        )
    """)
    
    # Mistakes log - detailed error tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mistakes_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            concept_id INTEGER NOT NULL,
            mistake_type TEXT,
            description TEXT,
            context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (concept_id) REFERENCES concepts(id)
        )
    """)
    
    # Diagnostic tests
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diagnostic_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            concept_id INTEGER NOT NULL,
            score REAL,
            answers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (concept_id) REFERENCES concepts(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def insert_default_modules_and_sequences():
    """Insert default modules, sequences and concepts"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Modules data
    modules_data = [
        {
            "title": "Généralités sur les systèmes informatiques",
            "description": "Tronc commun - Fondamentaux des systèmes informatiques",
            "sequences": [
                {
                    "title": "Définitions et vocabulaire de base",
                    "concepts": [
                        ("Définition de l'information", 2),
                        ("Définition du traitement", 2),
                        ("Définition de l'informatique", 2),
                        ("Définition du système informatique", 2),
                    ]
                },
                {
                    "title": "Structure de base d'un ordinateur",
                    "concepts": [
                        ("Schéma fonctionnel d'un ordinateur", 2),
                        ("Périphériques", 2),
                        ("Unité centrale de traitement", 2),
                    ]
                },
                {
                    "title": "Les types de logiciels",
                    "concepts": [
                        ("Les logiciels de base", 2),
                        ("Les logiciels d'application", 2),
                    ]
                },
                {
                    "title": "Domaines d'application",
                    "concepts": [
                        ("Applications de l'informatique", 2),
                    ]
                },
            ]
        },
        {
            "title": "Les logiciels",
            "description": "Tronc commun - Utilisation des logiciels",
            "sequences": [
                {
                    "title": "Système d'exploitation",
                    "concepts": [
                        ("Fonctionnalités de base d'un système d'exploitation", 2),
                        ("Environnement d'un système d'exploitation", 2),
                        ("Gestion des fichiers/dossiers", 2),
                    ]
                },
                {
                    "title": "Traitement de texte",
                    "concepts": [
                        ("Fonctionnalités d'un texteur", 3),
                        ("L'environnement de travail", 3),
                        ("Saisie et mise en forme", 3),
                        ("Insertion d'objets et mise en page", 3),
                    ]
                },
                {
                    "title": "Tableur",
                    "concepts": [
                        ("Fonctionnalités d'un tableur", 2),
                        ("L'environnement de travail", 2),
                        ("Formules et Adressage", 2),
                        ("Fonctions et Graphiques", 2),
                    ]
                },
            ]
        },
        {
            "title": "Algorithmique et programmation",
            "description": "Tronc commun - Concepts de base de la programmation",
            "sequences": [
                {
                    "title": "Notion d'algorithme",
                    "concepts": [
                        ("Constante", 2),
                        ("Variable", 2),
                        ("Type", 2),
                    ]
                },
                {
                    "title": "Instructions de base",
                    "concepts": [
                        ("Lecture", 2),
                        ("Ecriture", 2),
                        ("Affectation", 2),
                    ]
                },
                {
                    "title": "Structures de contrôle de base",
                    "concepts": [
                        ("Séquentielle", 2),
                        ("Sélective", 2),
                    ]
                },
                {
                    "title": "Langages de programmation",
                    "concepts": [
                        ("Notion de programme", 1),
                        ("Langages de programmation", 1),
                        ("Transcription d'algorithme", 1),
                    ]
                },
            ]
        },
        {
            "title": "Réseaux et Internet",
            "description": "Tronc commun - Fondamentaux des réseaux",
            "sequences": [
                {
                    "title": "Notion de réseau informatique",
                    "concepts": [
                        ("Notion de réseau informatique", 1),
                        ("Topologie de réseaux", 1),
                        ("Avantages d'un réseau", 2),
                    ]
                },
                {
                    "title": "Réseau Internet",
                    "concepts": [
                        ("Définition d'Internet", 2),
                        ("Connexion à Internet", 2),
                        ("Services Internet (Web, e-mail, chat)", 2),
                        ("Avantages et inconvénients", 2),
                    ]
                },
            ]
        },
    ]
    
    # Insert modules and sequences
    for module_idx, module in enumerate(modules_data):
        try:
            cursor.execute(
                "INSERT INTO modules (title, description, order_index) VALUES (?, ?, ?)",
                (module["title"], module["description"], module_idx + 1)
            )
            module_id = cursor.lastrowid
            
            # Insert sequences
            for seq_idx, sequence in enumerate(module["sequences"]):
                try:
                    cursor.execute(
                        "INSERT INTO sequences (module_id, title, order_index) VALUES (?, ?, ?)",
                        (module_id, sequence["title"], seq_idx + 1)
                    )
                    sequence_id = cursor.lastrowid
                    
                    # Insert concepts for each sequence
                    for concept_name, hours in sequence["concepts"]:
                        try:
                            cursor.execute(
                                "INSERT INTO concepts (sequence_id, name, domain, hours) VALUES (?, ?, ?, ?)",
                                (sequence_id, concept_name, module["title"], hours)
                            )
                        except sqlite3.IntegrityError:
                            pass
                except sqlite3.IntegrityError:
                    pass
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()
    print("✅ Default modules and sequences inserted")

def insert_default_concepts():
    """Insert default concepts into database (kept for backward compatibility)"""
    insert_default_modules_and_sequences()

if __name__ == "__main__":
    init_db()
    insert_default_concepts()
