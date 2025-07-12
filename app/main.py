from fastapi import FastAPI
import uvicorn
from app.api.api_problems import problems
from app.api.api_submissions import submissions
from app.api.api_auth import auth
from app.api.api_users import users
from app.api.api_languages import languages
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import sqlite3
import bcrypt

# Call the function before the app starts listening for requests
@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = sqlite3.connect('./app/oj_system.db')
    
    # Create table of users
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
    
    # Create table of problems
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS problems (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            input_description TEXT NOT NULL,
            output_description TEXT NOT NULL,
            samples TEXT NOT NULL,
            constraints TEXT NOT NULL,
            testcases TEXT NOT NULL,
            hint TEXT,
            source TEXT,
            tags TEXT,
            time_limit REAL,
            memory_limit INTEGER,
            author TEXT,
            difficulty TEXT
        )
    ''')
    conn.commit()
    
    # Create table of submissions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            problem_id TEXT NOT NULL,
            code TEXT NOT NULL,
            language TEXT NOT NULL,
            status TEXT NOT NULL,
            counts INTEGER,
            log TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (problem_id) REFERENCES problems (id)
        )
    ''')
    conn.commit()
    
    # Create table of languages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS languages (
            name TEXT PRIMARY KEY,
            file_ext TEXT NOT NULL,
            compile_cmd TEXT,
            run_cmd TEXT NOT NULL,
            source_template TEXT,
            time_limit REAL,
            memory_limit INTEGER
        )
    ''')
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
                    "admintestpassword".encode('utf-8'),
                    bcrypt.gensalt(rounds=12)
                ).decode('utf-8'), 
                "admin"
            )
        )
        conn.commit()
        
    cursor.execute("SELECT * FROM languages WHERE name = ?", ("cpp",))
    result = cursor.fetchone()
    if not result:
        # C++ does not exist, create it
        cursor.execute(
            """INSERT INTO languages (
                name, file_ext, compile_cmd, run_cmd,
                source_template, time_limit, memory_limit
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                "cpp", ".cpp", "g++ {src} -o {exe} -O2 -std=c++17",
                "{file_name}.exe", "{code}", 1.0, 128
            )
        )
        conn.commit()
        
    cursor.execute("SELECT * FROM languages WHERE name = ?", ("python",))
    result = cursor.fetchone()
    if not result:
        # python does not exist, create it
        cursor.execute(
            """INSERT INTO languages (
                name, file_ext, run_cmd,
                source_template, time_limit, memory_limit
            ) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                "python", ".py", "python3 {file_name}.py",
                "{code}", 1.0, 128
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
app.include_router(languages, prefix = '/api/languages')

@app.get("/")
async def welcome():
    return "Welcome!"

if __name__ == '__main__':
    uvicorn.run(app)
