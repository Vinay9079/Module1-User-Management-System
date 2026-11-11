# Module 1 – User Management System

A role-based User Management System built using Python, Flask, and SQLite.

## Overview

This project implements user authentication, role-based access control (RBAC), team management, and audit logging.

## Technology Stack

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- Flask-Login
- Argon2 password hashing
- Flask-WTF (CSRF protection)
- Flask-Limiter (login rate limiting)

## Features

### Authentication
- User login using username or email
- Secure password hashing
- Session-based authentication
- Logout
- Profile update
- Password change
- Login rate limiting

### Role-Based Access Control
- Administrator
- Security Analyst
- Team Lead / Supervisor

### User Management
- Create and manage user accounts
- Assign roles
- Activate or deactivate accounts

### Team Management
- Create and view teams
- Add and remove team members
- Role-based team management permissions

### Audit Logging
- Record login successes and failures
- Track logout events
- Record user, role, and team changes
- Filter audit logs

### Security
- CSRF protection
- Password hashing using Argon2
- Protected routes
- Role-based authorization
- Environment-based secret configuration

## Project Structure

```text
Module1_UserManagement/
├── app/
│   ├── templates/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── auth.py
│   ├── teams.py
│   ├── audit.py
│   └── extensions.py
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

## Setup Instructions

1. Clone this repository.
2. Create a virtual environment.
3. Install the required dependencies.
4. Create a `.env` file containing a secure `SECRET_KEY`.
5. Initialize the application database.
6. Create an administrator account.
7. Run the Flask application.

## Installation

```bash
git clone YOUR_REPOSITORY_URL
cd Module1-User-Management-System

python -m venv venv
```

Activate the virtual environment on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
SECRET_KEY=replace_with_a_secure_random_secret
```

Create an administrator account:

```bash
flask --app run.py create-admin
```

Run the application:

```bash
python run.py
```

Open `http://127.0.0.1:5000` in your browser.

## Testing

The application was tested for authentication, role-based access, team management, audit logging, CSRF protection, and login rate limiting.

## Project Scope

This repository contains the User Management System implementation for Module 1.