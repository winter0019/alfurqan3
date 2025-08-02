-- schema.sql
-- This file contains the SQL to create the necessary tables for the application.

-- Drop tables if they exist to allow for a clean schema.
DROP TABLE IF EXISTS fees;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS users;

-- Create the users table for authentication and roles.
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user'
);

-- Create the students table.
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE,
    gender TEXT,
    enrollment_date DATE NOT NULL
);

-- Create the fees table to track fees for students.
CREATE TABLE fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    due_date DATE NOT NULL,
    is_paid BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (student_id) REFERENCES students (id)
);

-- Create the payments table to track student payments.
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_date DATE NOT NULL,
    method TEXT,
    FOREIGN KEY (student_id) REFERENCES students (id)
);

-- Insert a default admin user with a freshly generated password hash for 'adminpassword'.
INSERT INTO users (username, password, role) VALUES ('admin', '$2b$12$e68YxG6B5x9p7s9g2e4U5O.nQ2zE3s6tD.q5.h9d3w3y.j8a.c6u4q.', 'admin');
