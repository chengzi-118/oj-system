from fastapi import APIRouter, Request, Response, UploadFile, File, HTTPException
import sqlite3
import json

import_data = APIRouter()

@import_data.post('/')
async def importing(request: Request, response: Response, file: UploadFile = File(None)):
    """
    Import data.

    Returns:
        200: success.
        400: format error.
        401: not logged in.
        403: insufficient permissions.
        500: server error.
    """
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    # Check permission
    if request.session["role"] != "admin":
        response.status_code = 403
        return {"code": 403, "msg": "insufficient permissions", "data": None}
    
    # Check file
    if not file:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    if not file.filename:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files supported")
    
    # Read file
    content = await file.read()
    if not content:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    try:
        data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    if not validate(data):
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        
        for user in data["users"]:
            cursor.execute(
                """INSERT OR REPLACE INTO users 
                (id, name, password, role, join_time, submit_count, resolve_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    user["user_id"], user["username"], user["password"], user["role"],
                    user["join_time"], user["submit_count"], user["resolve_count"]
                )
            )
        
        for problem_data in data["problems"]:
            cursor.execute(
                """INSERT OR REPLACE INTO problems (
                    id, title, description, input_description, output_description, 
                    samples, constraints, testcases, hint, source, tags, 
                    time_limit, memory_limit, author, difficulty, public_cases
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    problem_data['id'], problem_data['title'],
                    problem_data['description'], problem_data['input_description'],
                    problem_data['output_description'],
                    json.dumps(problem_data['samples']),
                    problem_data['constraints'], 
                    json.dumps(problem_data['testcases']),
                    problem_data['hint'], problem_data['source'],
                    json.dumps(problem_data['tags']),
                    problem_data['time_limit'], problem_data['memory_limit'],
                    problem_data['author'], problem_data['difficulty'],
                    1 if problem_data.get('public_cases') else 0
                )
            )
            
        for submission in data["submissions"]:
            cursor.execute(
                """INSERT OR REPLACE INTO submissions (
                    id, user_id, problem_id, code,
                    language, status, counts, log
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    submission["submission_id"],
                    submission["user_id"],
                    submission["problem_id"],
                    submission["code"],
                    submission["language"],
                    "success",
                    submission["counts"],
                    json.dumps(submission["details"])
                )
            )
            
        conn.commit()
        
    response.status_code = 200
    return {"code": 200, "msg": "import success", "data": None}
    
user_keys = [
    "user_id", "username", "password", "role",
    "join_time", "submit_count", "resolve_count"
]

problem_keys = [
    "id", "title", "description", "input_description", "output_description",
    "samples", "constraints", "testcases", "hint", "source", "tags",
    "time_limit", "memory_limit", "author", "difficulty"
]

submission_keys = [
    "submission_id", "user_id", "problem_id",
    "language", "code", "details", "score", "counts",
]

result_list = ["AC", "WA", "TLE", "MLE", "RE", "CE", "UNK"]
    
def validate(data: dict) -> bool:
    """
    Validate data to be imported.

    Args:
        data (dict): A dict of data to be imported.

    Returns:
        bool: True means the dict can be imported.
    """
    # Check elementary keys
    if "users" not in data:
        return False
    if "problems" not in data:
        return False
    if "submissions" not in data:
        return False
    
    # Check users
    users = data["users"]
    if not isinstance(users, list):
        return False
    
    for user in users:
        if not isinstance(user, dict):
            return False
        for user_key in user_keys:
            if user_key not in user:
                return False
        
        if not isinstance(user["submit_count"], int):
            return False
        if not isinstance(user["resolve_count"], int):
            return False
    
    # Check problems
    problems = data["problems"]
    if not isinstance(problems, list):
        return False
    
    for problem in problems:
        if not isinstance(problem, dict):
            return False
        
        for problem_key in problem_keys:
            if problem_key not in problem:
                return False
            
        if not isinstance(problem["tags"], list):
            return False
        if not isinstance(problem["memory_limit"], int):
            return False
        if not isinstance(problem["time_limit"], float):
            return False
        
        if not isinstance(problem["samples"], list):
            return False
        for sample in problem["samples"]:
            if not isinstance(sample, dict):
                return False
            if "input" not in sample:
                return False
            if "output" not in sample:
                return False
            
        if not isinstance(problem["testcases"], list):
            return False
        for testcase in problem["testcases"]:
            if not isinstance(testcase, dict):
                return False
            if "input" not in testcase:
                return False
            if "output" not in testcase:
                return False
    
    # Check submissions
    submissions = data["submissions"]
    if not isinstance(submissions, list):
        return False
    
    for submission in submissions:
        if not isinstance(submission, dict):
            return False
        for submission_key in submission_keys:
            if submission_key not in submission:
                return False
        if not isinstance(submission["score"], int):
            return False
        if not isinstance(submission["counts"], int):
            return False
        
        if not isinstance(submission["details"], list):
            return False
        for detail in submission["details"]:
            if "id" not in detail:
                return False
            if not isinstance(detail["id"], int):
                return False
            if "time" not in detail:
                return False
            if not isinstance(detail["time"], float) and\
                not isinstance(detail["time"], int):
                return False
            if "memory" not in detail:
                return False
            if not isinstance(detail["memory"], float) and\
                not isinstance(detail["memory"], int):
                return False
            if "result" not in detail:
                return False
            if detail["result"] not in result_list:
                return False
    
    return True