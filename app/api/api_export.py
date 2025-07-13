from fastapi import APIRouter, Request, Response
import sqlite3
import json

export_data = APIRouter()

@export_data.get('/')
async def exporting(request: Request, response: Response):
    """
    Export data.

    Returns:
        200: success.
        401: not logged in.
        403: insufficient permissions.
    """
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    # Check permission
    if request.session["role"] != "admin":
        response.status_code = 403
        return {"code": 403, "msg": "insufficient permissions", "data": None}

    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        users = []
        for row in rows:
            users.append({
                "user_id": row[0],
                "username": row[1],
                "password": row[2],
                "role": row[3],
                "join_time": row[4],
                "submit_count": row[5],
                "resolve_count": row[6]
            })

        # Get all problems
        cursor.execute("SELECT * FROM problems")
        rows = cursor.fetchall()
        problems = []
        for row in rows:
            problems.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "input_description": row[3],
                "output_description": row[4],
                "samples": json.loads(row[5]),
                "constraints": row[6],
                "testcases": json.loads(row[7]),
                "hint": row[8],
                "source": row[9],
                "tags": json.loads(row[10]) if row[10] else [],
                "time_limit": row[11],
                "memory_limit": row[12],
                "author": row[13],
                "difficulty": row[14],
                "public_cases": True if row[15] else False
            })

        # Get all submissions
        cursor.execute("SELECT * FROM submissions")
        rows = cursor.fetchall()
        submissions = []
        for row in rows:
            submissions.append({
                "submission_id": str(row[0]),
                "user_id": str(row[1]),
                "problem_id": row[2],
                "language": row[4],
                "code": row[3],
                "details": json.loads(str(row[7])),
                "score": 10,
                "counts": row[6],
            })

    response.status_code = 200
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "users": users,
            "problems": problems,
            "submissions": submissions
        }
    }
