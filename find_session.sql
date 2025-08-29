-- SQL script to find session ID for quiz ID: 5a38de62-67e4-4a28-ac47-d5147cfc73c6
-- Run this against the quiz_db database

-- 1. Check if the quiz exists
SELECT 
    id,
    title,
    status,
    user_id,
    created_at
FROM quizzes 
WHERE id = '5a38de62-67e4-4a28-ac47-d5147cfc73c6';

-- 2. Find all quiz sessions for this quiz
SELECT 
    id as session_id,
    quiz_id,
    user_id,
    status,
    created_at,
    seed
FROM quiz_sessions 
WHERE quiz_id = '5a38de62-67e4-4a28-ac47-d5147cfc73c6'
ORDER BY created_at DESC;

-- 3. Find all quiz attempts for this quiz
SELECT 
    attempt_id,
    quiz_id,
    user_id,
    status,
    started_at,
    submitted_at,
    total_score,
    max_score
FROM quiz_attempts 
WHERE quiz_id = '5a38de62-67e4-4a28-ac47-d5147cfc73c6'
ORDER BY started_at DESC;

-- 4. Count related records
SELECT 
    'quiz_sessions' as table_name,
    COUNT(*) as count
FROM quiz_sessions 
WHERE quiz_id = '5a38de62-67e4-4a28-ac47-d5147cfc73c6'
UNION ALL
SELECT 
    'quiz_attempts' as table_name,
    COUNT(*) as count
FROM quiz_attempts 
WHERE quiz_id = '5a38de62-67e4-4a28-ac47-d5147cfc73c6'
UNION ALL
SELECT 
    'quiz_session_questions' as table_name,
    COUNT(*) as count
FROM quiz_session_questions qsq
JOIN quiz_sessions qs ON qsq.session_id = qs.id
WHERE qs.quiz_id = '5a38de62-67e4-4a28-ac47-d5147cfc73c6';

-- 5. Get session questions if sessions exist
SELECT 
    qsq.id as question_id,
    qsq.session_id,
    qsq.display_index,
    qsq.q_type,
    qsq.stem,
    qsq.options,
    qsq.blanks
FROM quiz_session_questions qsq
JOIN quiz_sessions qs ON qsq.session_id = qs.id
WHERE qs.quiz_id = '5a38de62-67e4-4a28-ac47-d5147cfc73c6'
ORDER BY qsq.session_id, qsq.display_index;
