from fastapi import FastAPI
import uvicorn
from api.api_problems import problems
from api.api_submissions import submissions
from api.api_auth import auth
from api.api_users import users
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import sqlite3
import bcrypt

# Call the function before the app starts listening for requests
@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = sqlite3.connect('./users.db')
    
    # Create table
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    '''
    )
    conn.commit()
    
    # Check admin
    cursor.execute("SELECT * FROM users WHERE name = ?", ("admin",))
    result = cursor.fetchone()
    if not result:
        # Admin user does not exist, create it
        cursor.execute(
            "INSERT INTO users (name, password, role) VALUES (?, ?, ?)",
            (
                "admin", 
                bcrypt.hashpw(
                    "admin".encode('utf-8'),
                    bcrypt.gensalt(rounds=12)
                ).decode('utf-8'), 
                "admin"
            )
        )
        conn.commit()
    
    yield
    conn.close()
        
app = FastAPI(
    title="Simple OJ System - Student Template",
    description="A simple online judge system for programming assignments",
    version="1.0.0",
    lifespan = lifespan
)

app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

app.include_router(problems, prefix = '/api/problems')
app.include_router(submissions, prefix = '/api/submissions')
app.include_router(auth, prefix = '/api/auth')
app.include_router(users, prefix = '/api/users')

@app.get("/")
async def welcome():
    return "Welcome!"

if __name__ == '__main__':
    uvicorn.run(app)
