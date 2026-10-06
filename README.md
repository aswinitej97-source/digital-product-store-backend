# Digital Product Store Backend
 
A backend application for a Digital Product Store built using FastAPI, Python, SQLAlchemy, SQLite, and JWT Authentication.
 
## Technologies Used
 
- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- JWT Authentication
- Uvicorn
 
## Features
 
- User Registration
- User Login
- JWT Authentication
- Protected User Profile API
- Product Management
- Database Integration
- API Validation and Error Handling
 
## Authentication APIs
 
- POST /auth/register
- POST /auth/login
- GET /profile
 
## Run the Project
 
Install dependencies:
 
pip install fastapi uvicorn sqlalchemy python-jose passlib email-validator
 
Start the server:
 
uvicorn main:app --reload
 
Open Swagger API documentation:
 
http://127.0.0.1:8000/docs
 
## Project Status
 
Backend development is in progress.
 
