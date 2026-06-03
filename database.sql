-- ============================================================
-- AI Interview Question Generator - MySQL Database Schema
-- College Project: PRG 200 Final Project
-- ============================================================

-- Create and use the database
CREATE DATABASE IF NOT EXISTS ai_interview_db;
USE ai_interview_db;

-- ============================================================
-- 1. Candidates Table
--    Stores candidate profile information extracted from resume
-- ============================================================
CREATE TABLE Candidates (
    candidate_id    INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(100)  NOT NULL,
    email           VARCHAR(100)  UNIQUE,
    phone           VARCHAR(20),
    education       VARCHAR(255),
    experience_years INT DEFAULT 0
);

-- ============================================================
-- 2. Skills Table
--    Stores skills extracted from the candidate's resume
-- ============================================================
CREATE TABLE Skills (
    skill_id      INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id  INT NOT NULL,
    skill_name    VARCHAR(100) NOT NULL,
    skill_type    ENUM('Hard Skill', 'Soft Skill') NOT NULL,
    FOREIGN KEY (candidate_id) REFERENCES Candidates(candidate_id)
        ON DELETE CASCADE
);

-- ============================================================
-- 3. InterviewSessions Table
--    Tracks each interview session for a candidate
-- ============================================================
CREATE TABLE InterviewSessions (
    session_id      INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id    INT NOT NULL,
    job_role        VARCHAR(100) NOT NULL,
    difficulty      ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    interview_date  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES Candidates(candidate_id)
        ON DELETE CASCADE
);

-- ============================================================
-- 4. Questions Table
--    Stores AI-generated interview questions
-- ============================================================
CREATE TABLE Questions (
    question_id     INT AUTO_INCREMENT PRIMARY KEY,
    question_text   TEXT NOT NULL,
    difficulty      ENUM('Easy', 'Medium', 'Hard') NOT NULL
);

-- ============================================================
-- 5. Responses Table
--    Stores candidate answers linked to a session and question
-- ============================================================
CREATE TABLE Responses (
    response_id   INT AUTO_INCREMENT PRIMARY KEY,
    session_id    INT NOT NULL,
    question_id   INT NOT NULL,
    answer_text   TEXT NOT NULL,
    FOREIGN KEY (session_id)  REFERENCES InterviewSessions(session_id)
        ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES Questions(question_id)
        ON DELETE CASCADE
);

-- ============================================================
-- 6. InterviewSummary Table
--    Stores AI-generated evaluation summary for each session
-- ============================================================
CREATE TABLE InterviewSummary (
    summary_id      INT AUTO_INCREMENT PRIMARY KEY,
    session_id      INT NOT NULL UNIQUE,
    overall_score   DECIMAL(5,2),
    strengths       TEXT,
    weaknesses      TEXT,
    final_feedback  TEXT,
    FOREIGN KEY (session_id) REFERENCES InterviewSessions(session_id)
        ON DELETE CASCADE
);
