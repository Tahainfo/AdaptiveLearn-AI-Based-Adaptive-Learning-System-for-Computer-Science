-- =============================================================================
-- ADMIN INTERFACE MIGRATION FOR ADAPTIVELEARN
-- =============================================================================
-- This migration extends the existing system with RBAC and admin capabilities
-- It maintains backward compatibility with existing tables

-- =============================================================================
-- 1. ADD ROLE-BASED ACCESS CONTROL TO STUDENTS
-- =============================================================================
-- Adds role and is_active fields to students table
ALTER TABLE students ADD COLUMN role TEXT DEFAULT 'student' CHECK(role IN ('student', 'admin'));
ALTER TABLE students ADD COLUMN is_active INTEGER DEFAULT 1;

-- Create index for role-based queries
CREATE INDEX IF NOT EXISTS idx_students_role ON students(role);

-- =============================================================================
-- 2. EXTEND EXERCISES TABLE WITH ADMIN FEATURES
-- =============================================================================
-- Adds exercise type, diagnostic flag, error type targeting, and JSON content
ALTER TABLE exercises ADD COLUMN exercise_type TEXT DEFAULT 'short_answer' 
    CHECK(exercise_type IN ('mcq', 'drag_drop', 'match_lines', 'short_answer', 'long_answer', 'true_false'));
ALTER TABLE exercises ADD COLUMN is_diagnostic INTEGER DEFAULT 0;
ALTER TABLE exercises ADD COLUMN error_type_targeted TEXT 
    CHECK(error_type_targeted IN ('conceptual', 'procedural', 'careless', NULL));
ALTER TABLE exercises ADD COLUMN content_json TEXT; -- Stores type-specific structure
ALTER TABLE exercises ADD COLUMN created_by_admin_id INTEGER REFERENCES students(id);
ALTER TABLE exercises ADD COLUMN is_active INTEGER DEFAULT 1;

-- Create indexes for queries
CREATE INDEX IF NOT EXISTS idx_exercises_type ON exercises(exercise_type);
CREATE INDEX IF NOT EXISTS idx_exercises_diagnostic ON exercises(is_diagnostic);
CREATE INDEX IF NOT EXISTS idx_exercises_error_type ON exercises(error_type_targeted);
CREATE INDEX IF NOT EXISTS idx_exercises_active ON exercises(is_active);

-- =============================================================================
-- 3. CREATE ADMIN LOGS TABLE
-- =============================================================================
-- Tracks all admin actions for accountability and auditing
CREATE TABLE IF NOT EXISTS admin_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    action_type TEXT NOT NULL CHECK(action_type IN (
        'create_student', 'update_student', 'delete_student', 'reset_password',
        'create_exercise', 'update_exercise', 'delete_exercise', 'activate_exercise', 'deactivate_exercise',
        'view_student_progress', 'view_analytics', 'create_diagnostic', 'update_diagnostic'
    )),
    entity TEXT NOT NULL, -- 'student', 'exercise', 'diagnostic', 'concept'
    entity_id INTEGER,
    target_user_id INTEGER, -- If action affects another user
    details TEXT, -- JSON string for additional context
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES students(id),
    FOREIGN KEY (target_user_id) REFERENCES students(id)
);

CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_id ON admin_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_timestamp ON admin_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_admin_logs_action ON admin_logs(action_type);

-- =============================================================================
-- 4. CREATE EXERCISE TEMPLATE TABLE (for reusable diagnostic questions)
-- =============================================================================
CREATE TABLE IF NOT EXISTS exercise_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    exercise_type TEXT NOT NULL,
    content_json TEXT NOT NULL, -- The template structure
    description TEXT,
    created_by_admin_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by_admin_id) REFERENCES students(id)
);

-- =============================================================================
-- 5. ADD DIAGNOSTIC RESPONSE TRACKING
-- =============================================================================
-- Extended diagnostic tracking with error classification
ALTER TABLE diagnostic_attempts ADD COLUMN error_types_detected TEXT; -- JSON array of error types
ALTER TABLE diagnostic_attempts ADD COLUMN classification TEXT; -- Overall classification

-- =============================================================================
-- 6. CREATE ADMIN SETTINGS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS admin_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    updated_by_admin_id INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by_admin_id) REFERENCES students(id)
);

-- Insert default settings
INSERT OR IGNORE INTO admin_settings (setting_key, setting_value, description) VALUES
    ('enable_ai_generation', 'true', 'Allow AI-generated exercises'),
    ('prioritize_admin_exercises', 'true', 'Use admin exercises before AI-generated'),
    ('max_diagnostic_questions', '10', 'Maximum questions per diagnostic test'),
    ('mastery_threshold', '0.7', 'Mastery level threshold (0-1)'),
    ('weak_concept_threshold', '0.4', 'Weakness threshold (0-1)');

-- =============================================================================
-- SUMMARY OF CHANGES
-- =============================================================================
-- Added to students: role, is_active
-- Added to exercises: exercise_type, is_diagnostic, error_type_targeted, content_json, created_by_admin_id, is_active
-- New tables: admin_logs, exercise_templates, admin_settings
-- Extended: diagnostic_attempts with error_types_detected, classification
