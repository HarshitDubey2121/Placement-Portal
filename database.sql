CREATE DATABASE IF NOT EXISTS placement_portal;
USE placement_portal;

-- =========================
-- STUDENTS TABLE
-- =========================
CREATE TABLE students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    course VARCHAR(100),
    mobile VARCHAR(20),
    resume VARCHAR(255),
    penalty_points INT DEFAULT 0,
    warning_count INT DEFAULT 0,
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- COMPANIES TABLE
-- =========================
CREATE TABLE companies (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(150),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    website VARCHAR(150),
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- JOBS TABLE
-- =========================
CREATE TABLE jobs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT,
    title VARCHAR(150),
    description TEXT,
    salary VARCHAR(50),
    location VARCHAR(100),
    deadline DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- =========================
-- APPLICATIONS TABLE
-- =========================
CREATE TABLE applications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    job_id INT,
    status VARCHAR(50) DEFAULT 'Applied',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- =========================
-- INTERVIEWS TABLE
-- =========================
CREATE TABLE interviews (
    id INT PRIMARY KEY AUTO_INCREMENT,
    application_id INT,
    interview_date DATETIME,
    mode VARCHAR(50),
    meeting_link VARCHAR(255),
    attendance VARCHAR(20) DEFAULT 'Pending',
    result VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

-- =========================
-- ADMIN TABLE
-- =========================
CREATE TABLE admin (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50),
    password VARCHAR(255)
);

INSERT INTO admin(username,password)
VALUES('admin','admin123');

-- =========================
-- NOTIFICATIONS TABLE
-- =========================
CREATE TABLE notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_email VARCHAR(100),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);