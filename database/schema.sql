-- AI Interview Question Generator - Database Schema DDL
-- Member 4: Database Administrator & Security Engineer

CREATE DATABASE IF NOT EXISTS ai_interview_db;
USE ai_interview_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_username (username),
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Job Roles Table
CREATE TABLE IF NOT EXISTS job_roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_job_roles_name (role_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Skills Table
CREATE TABLE IF NOT EXISTS skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(50) NOT NULL UNIQUE,
    skill_type VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_skill_type CHECK (skill_type IN ('hard', 'soft')),
    INDEX idx_skills_name (skill_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Questions Table
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_role_id INT NULL,
    question_text TEXT NOT NULL,
    difficulty_level VARCHAR(15) NOT NULL,
    question_type VARCHAR(15) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_difficulty CHECK (difficulty_level IN ('Beginner', 'Intermediate', 'Expert')),
    CONSTRAINT chk_qtype CHECK (question_type IN ('technical', 'behavioral')),
    FOREIGN KEY (job_role_id) REFERENCES job_roles(id) ON DELETE SET NULL,
    INDEX idx_questions_difficulty (difficulty_level),
    INDEX idx_questions_type (question_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Question Skills Association Table (Many-to-Many)
CREATE TABLE IF NOT EXISTS question_skills (
    question_id INT NOT NULL,
    skill_id INT NOT NULL,
    PRIMARY KEY (question_id, skill_id),
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Interview Sessions Table
CREATE TABLE IF NOT EXISTS interview_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    job_role_id INT NOT NULL,
    difficulty_level VARCHAR(15) NOT NULL,
    status VARCHAR(15) NOT NULL DEFAULT 'ongoing',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    overall_score DECIMAL(4, 2) NULL,
    overall_feedback TEXT NULL,
    CONSTRAINT chk_session_difficulty CHECK (difficulty_level IN ('Beginner', 'Intermediate', 'Expert')),
    CONSTRAINT chk_session_status CHECK (status IN ('ongoing', 'completed')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (job_role_id) REFERENCES job_roles(id) ON DELETE CASCADE,
    INDEX idx_sessions_user (user_id),
    INDEX idx_sessions_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Responses Table
CREATE TABLE IF NOT EXISTS responses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    question_id INT NOT NULL,
    answer_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE RESTRICT,
    INDEX idx_responses_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Evaluations Table (One-to-One with Responses)
CREATE TABLE IF NOT EXISTS evaluations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    response_id INT NOT NULL UNIQUE,
    score INT NOT NULL,
    strengths JSON NULL,
    weaknesses JSON NULL,
    suggestions JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_eval_score CHECK (score BETWEEN 1 AND 10),
    FOREIGN KEY (response_id) REFERENCES responses(id) ON DELETE CASCADE,
    INDEX idx_evaluations_response (response_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
