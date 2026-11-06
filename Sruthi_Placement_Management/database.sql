CREATE DATABASE IF NOT EXISTS placement_management;
USE placement_management;

CREATE TABLE IF NOT EXISTS students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    roll_no VARCHAR(30) UNIQUE NOT NULL,
    branch VARCHAR(50),
    cgpa DECIMAL(3,2),
    email VARCHAR(100) UNIQUE
);

CREATE TABLE IF NOT EXISTS companies (
    company_id INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(150) NOT NULL,
    job_role VARCHAR(100) NOT NULL,
    package DECIMAL(10,2),
    eligibility_cgpa DECIMAL(3,2),
    drive_date DATE
);

CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin','student') NOT NULL,
    student_id INT UNIQUE,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE TABLE IF NOT EXISTS applications (
    application_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    company_id INT NOT NULL,
    applied_date DATE,
    round VARCHAR(50),
    status VARCHAR(30) DEFAULT 'Applied',
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE (student_id, company_id)
);
