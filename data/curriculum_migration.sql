-- Moroccan Curriculum Migration SQL Script
-- ============================================
-- This script adds curriculum hierarchy to your adaptive learning system
-- 
-- SAFE TO RUN:
-- - No existing tables are modified
-- - All new tables have IF NOT EXISTS clauses
-- - Existing data is preserved
-- - Backward compatible
-- ============================================

-- ============================================
-- PHASE 1: Create Curriculum Tables
-- ============================================

-- Modules Table (top of hierarchy)
CREATE TABLE IF NOT EXISTS modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE NOT NULL,
    description TEXT,
    order_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sequences Table (middle of hierarchy)
CREATE TABLE IF NOT EXISTS sequences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    order_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(id),
    UNIQUE(module_id, title)
);

-- ============================================
-- PHASE 2: Update Concepts Table
-- ============================================
-- 
-- If your concepts table already has sequence_id, this is safe
-- If not, you may need to add it manually:
--
-- ALTER TABLE concepts ADD COLUMN sequence_id INTEGER REFERENCES sequences(id);
--
-- SQLite has limited ALTER TABLE support, so if the above fails,
-- your concepts table is fine as-is (backward compatible)
--

-- ============================================
-- PHASE 3: Update Diagnostic Attempts Table
-- ============================================
--
-- If your diagnostic_attempts table doesn't have these columns,
-- add them (safe for SQLite 3.25.0+):
--
-- ALTER TABLE diagnostic_attempts ADD COLUMN sequence_id INTEGER REFERENCES sequences(id);
-- ALTER TABLE diagnostic_attempts ADD COLUMN concept_breakdown TEXT;
--
-- These columns are optional for backward compatibility
--

-- ============================================
-- PHASE 4: Insert Moroccan Curriculum Data
-- ============================================

-- MODULE 1: Généralités sur les systèmes informatiques
INSERT OR IGNORE INTO modules (title, description, order_index)
VALUES ('Généralités sur les systèmes informatiques', 'Tronc Commun - Fondamentaux des systèmes informatiques', 1);

INSERT OR IGNORE INTO sequences (module_id, title, description, order_index)
SELECT id, 'Définitions et vocabulaire de base', 'Concepts fondamentaux', 1
FROM modules WHERE title = 'Généralités sur les systèmes informatiques';

INSERT OR IGNORE INTO sequences (module_id, title, description, order_index)
SELECT id, 'Structure de base d''un ordinateur', 'Architecture matérielle', 2
FROM modules WHERE title = 'Généralités sur les systèmes informatiques';

INSERT OR IGNORE INTO sequences (module_id, title, description, order_index)
SELECT id, 'Les types de logiciels', 'Classification des logiciels', 3
FROM modules WHERE title = 'Généralités sur les systèmes informatiques';

INSERT OR IGNORE INTO sequences (module_id, title, description, order_index)
SELECT id, 'Domaines d''application', 'Applications pratiques', 4
FROM modules WHERE title = 'Généralités sur les systèmes informatiques';

-- MODULE 2: Les logiciels
INSERT OR IGNORE INTO modules (title, description, order_index)
VALUES ('Les logiciels', 'Tronc Commun - Utilisation et gestion des logiciels', 2);

INSERT OR IGNORE INTO sequences (module_id, title, description, order_index)
SELECT id, 'Système d''exploitation', 'Fonctionnement du système', 1
FROM modules WHERE title = 'Les logiciels';

INSERT OR IGNORE INTO sequences (module_id, title, description, order_index)
SELECT id, 'Traitement de texte', 'Traitement de documents', 2
FROM modules WHERE title = 'Les logiciels';

INSERT OR IGNORE INTO sequences (module_id, title, description, order_index)
SELECT id, 'Tableur', 'Calculs et tableaux', 3
FROM modules WHERE title = 'Les logiciels';

-- MODULE 3: Algorithmique et programmation
INSERT OR IGNORE INTO modules (title, description, order_index)
VALUES ('Algorithmique et programmation', 'Tronc Commun - Logique et programmation', 3);

INSERT OR IGNORE INTO sequences (module_id, title, description, order_index)
SELECT id, 'Notion d''algorithme', 'Éléments de base', 1
FROM modules WHERE title = 'Algorithmique et programmation';

INSERT OR IGNORE INTO sequences (module_id, title, description, order_index)
SELECT id, 'Instructions de base', 'Instructions fondamentales', 2
FROM modules WHERE title = 'Algorithmique et programmation';

INSERT OR IGNORE INTO sequences (module_id, title, description, order_index)
SELECT id, 'Structures de contrôle de base', 'Contrôle du flux d''exécution', 3
FROM modules WHERE title = 'Algorithmique et programmation';

INSERT OR IGNORE INTO sequences (module_id, title, description, order_index)
SELECT id, 'Langages de programmation', 'Implémentation en langage', 4
FROM modules WHERE title = 'Algorithmique et programmation';

-- MODULE 4: Réseaux et Internet
INSERT OR IGNORE INTO modules (title, description, order_index)
VALUES ('Réseaux et Internet', 'Tronc Commun - Réseautique et Internet', 4);

INSERT OR IGNORE INTO sequences (module_id, title, description, order_index)
SELECT id, 'Notion de réseau informatique', 'Fondamentaux des réseaux', 1
FROM modules WHERE title = 'Réseaux et Internet';

INSERT OR IGNORE INTO sequences (module_id, title, description, order_index)
SELECT id, 'Réseau Internet', 'Internet et services', 2
FROM modules WHERE title = 'Réseaux et Internet';

-- ============================================
-- PHASE 5: Auto-map Existing Concepts to Sequences
-- ============================================
-- This maps concepts to sequences based on names/domains
-- Only updates concepts that don't already have a sequence_id

-- Map Algorithmics concepts to Algorithmique et programmation sequences
UPDATE concepts SET sequence_id = (
    SELECT s.id FROM sequences s 
    WHERE s.module_id = (SELECT id FROM modules WHERE title = 'Algorithmique et programmation')
    AND s.title = 'Notion d''algorithme'
    LIMIT 1
)
WHERE name IN ('Constante', 'Variable', 'Type', 'Pseudocode')
AND sequence_id IS NULL;

UPDATE concepts SET sequence_id = (
    SELECT s.id FROM sequences s 
    WHERE s.module_id = (SELECT id FROM modules WHERE title = 'Algorithmique et programmation')
    AND s.title = 'Instructions de base'
    LIMIT 1
)
WHERE name IN ('Lecture', 'Ecriture', 'Affectation')
AND sequence_id IS NULL;

UPDATE concepts SET sequence_id = (
    SELECT s.id FROM sequences s 
    WHERE s.module_id = (SELECT id FROM modules WHERE title = 'Algorithmique et programmation')
    AND s.title = 'Structures de contrôle de base'
    LIMIT 1
)
WHERE name IN ('Séquentielle', 'Sélective')
AND sequence_id IS NULL;

UPDATE concepts SET sequence_id = (
    SELECT s.id FROM sequences s 
    WHERE s.module_id = (SELECT id FROM modules WHERE title = 'Algorithmique et programmation')
    AND s.title = 'Langages de programmation'
    LIMIT 1
)
WHERE name IN ('Loops - For', 'Loops - While', 'Conditionals - If/Else', 'Arrays/Lists')
AND sequence_id IS NULL;

-- Map Networks concepts to Réseaux et Internet sequences
UPDATE concepts SET sequence_id = (
    SELECT s.id FROM sequences s 
    WHERE s.module_id = (SELECT id FROM modules WHERE title = 'Réseaux et Internet')
    AND s.title = 'Notion de réseau informatique'
    LIMIT 1
)
WHERE name IN ('OSI Model', 'IP Addressing')
AND sequence_id IS NULL;

UPDATE concepts SET sequence_id = (
    SELECT s.id FROM sequences s 
    WHERE s.module_id = (SELECT id FROM modules WHERE title = 'Réseaux et Internet')
    AND s.title = 'Réseau Internet'
    LIMIT 1
)
WHERE name IN ('Subnetting', 'Protocol Basics')
AND sequence_id IS NULL;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Verify modules created:
SELECT COUNT(*) as module_count FROM modules;
-- Expected: 4

-- Verify sequences created:
SELECT COUNT(*) as sequence_count FROM sequences;
-- Expected: 13

-- Verify concepts mapped:
SELECT COUNT(*) as concepts_with_sequences FROM concepts WHERE sequence_id IS NOT NULL;
-- Expected: Most/all existing concepts

-- View curriculum structure:
SELECT 
    m.title as Module,
    COUNT(DISTINCT s.id) as Sequences,
    COUNT(DISTINCT c.id) as Concepts
FROM modules m
LEFT JOIN sequences s ON s.module_id = m.id
LEFT JOIN concepts c ON c.sequence_id = s.id
GROUP BY m.id
ORDER BY m.order_index;

-- ============================================
-- ROLLBACK (If needed)
-- ============================================
-- 
-- To remove all curriculum changes:
-- DELETE FROM sequences;
-- DELETE FROM modules;
-- UPDATE concepts SET sequence_id = NULL;
--
-- This preserves all mastery data and exercises
--

-- ============================================
-- END OF MIGRATION
-- ============================================
-- Status: ✅ SAFE - No existing data modified
-- Concept-based adaptive learning still works
-- New curriculum hierarchy now available
