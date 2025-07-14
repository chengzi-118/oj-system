import sqlite3
import bcrypt
from datetime import datetime

async def create_table():
    """
    create table for initialize system.
    """
    conn = sqlite3.connect('./app/oj_system.db')
    
    # Create table of users
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            join_time TEXT NOT NULL,
            submit_count INTEGER NOT NULL,
            resolve_count INTEGER NOT NULL
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
            difficulty TEXT,
            public_cases INTEGER
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
            score INTEGER,
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
    
    # Create table of view_logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS view_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            problem_id TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    conn.commit()
    
    # Check admin
    cursor.execute("SELECT * FROM users WHERE name = ?", ("admin",))
    result = cursor.fetchone()
    if not result:
        # Admin user does not exist, create it
        cursor.execute(
            """INSERT INTO users (
                    name, password, role, join_time, submit_count, resolve_count
                    ) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                "admin", 
                bcrypt.hashpw(
                    "admintestpassword".encode('utf-8'),
                    bcrypt.gensalt(rounds=12)
                ).decode('utf-8'), 
                "admin",
                datetime.now().strftime("%Y-%m-%d"),
                0,
                0,
            )
        )
        conn.commit()
        
    conn.close()