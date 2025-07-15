from fastapi import APIRouter, Request, Response
import sqlite3
from app.problem_data import ProblemProfile
import json

problems = APIRouter()

@problems.get('/')
async def get(request: Request, response: Response):
    """
    Check the list of problems.
        
    Returns:
        dict: dict of id and title of all problems
    """
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    problems_profile: list[dict] = [] 
    
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM problems")
        rows = cursor.fetchall()
        for row in rows:
            problems_profile.append({"id": row[0], "title": row[1]})
    response.status_code = 200
    return {
        "code": 200,
        "msg": "success",
        "data": problems_profile
    }

@problems.post('/')
async def post(request: Request, response: Response):
    """
    Add problems.
    POST /api/problems/

    Returns:
        200: success
        400: missing field / format error
        409: id exists
    """
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    # Check whether data is legal
    try:
        problem_profile = ProblemProfile(**data)
    except TypeError:
        response.status_code = 400
        return {"code": 400, "msg": "missing field / format error", "data": None}
    
    problem_data = problem_profile.to_dict()
    
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        
        # Check whether the problem exists
        cursor.execute("SELECT id FROM problems WHERE id = ?", (problem_profile.id,))
        if cursor.fetchone():
            response.status_code = 409
            return {"code": 409, "msg": "id exists", "data": None}
        
        # Add into sheet
        cursor.execute(
            """INSERT INTO problems (
                id, title, description, input_description, output_description, 
                samples, constraints, testcases, hint, source, tags, 
                time_limit, memory_limit, author, difficulty, public_cases
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                problem_data['id'], problem_data['title'],
                problem_data['description'], problem_data['input_description'],
                problem_data['output_description'], problem_data['samples'],
                problem_data['constraints'], problem_data['testcases'],
                problem_data['hint'], problem_data['source'], problem_data['tags'],
                problem_data['time_limit'], problem_data['memory_limit'],
                problem_data['author'], problem_data['difficulty'], 0
            )
        )
        conn.commit()
    
    response.status_code = 200
    return {
        "code": 200,
        "msg": "add success",
        "data": {"id": problem_profile.id}
    }

@problems.get('/{problem_id}')
async def get_info(problem_id: str, request: Request, response: Response):
    """
    Check the problem information.
        
    Args:
        problem_id (str): id of the problem
        
    Returns:
        dict: dict of problem's information
    """
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        
        # Check whether the problem exists
        cursor.execute("SELECT * FROM problems WHERE id = ?", (problem_id,))
        row = cursor.fetchone()
        if row:
            # Change information in sheet to dict
            problem_info: dict = {}
            
            problem_info["id"] = row[0]
            problem_info["title"] = row[1]
            problem_info["description"] = row[2]
            problem_info["input_description"] = row[3]
            problem_info["output_description"] = row[4]
            problem_info["samples"] = json.loads(row[5])
            problem_info["constraints"] = row[6]
            problem_info["testcases"] = json.loads(row[7])
            problem_info["hint"] = row[8] if row[8] else ''
            problem_info["source"] = row[9] if row[9] else ''
            problem_info["tags"] = json.loads(row[10]) if row[10] else []
            problem_info["time_limit"] = row[11]
            problem_info["memory_limit"] = row[12]
            problem_info["author"] = row[13] if row[13] else ''
            problem_info["difficulty"] = row[14] if row[14] else ''
            
            return {"code": 200, "msg": "success", "data": problem_info}
        
    response.status_code = 404
    return {"code": 404, "msg": "problem not found", "data": None}

@problems.delete('/{problem_id}')
async def delete(problem_id: str, request: Request, response: Response):
    """
    Delete problems.

    Args:
        problem_id (str): id of the problem
        
    Returns:
        200: successfully deleted
        401: not logged in
        404: problem not found
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
        cursor.execute("DELETE FROM problems WHERE id = ?", (problem_id,))
        conn.commit()
        
        # Check whether the problem exists
        if cursor.rowcount > 0:
            response.status_code = 200
            return {"code": 200, "msg": "delete success", "data": {"id": problem_id}}
        else:
            response.status_code = 404
            return {"code": 404, "msg": "problem not found", "data": None}

@problems.put('/{problem_id}/log_visibility')
async def set_visibility(problem_id: str, request: Request, response: Response):
    """
    Set visibility of problems.
    
    Args:
        problem_id (str): id of the problem.
        public_cases (bool): visibility, default to False

    Returns:
        401: not logged in.
        403: insufficient permissions.
        404: problem not found.
        200: success.
    """
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    # Check permission
    if request.session["role"] != "admin":
        response.status_code = 403
        return {"code": 403, "msg": "insufficient permissions", "data": None}
    
    public_cases: bool = False
    try:
        data = await request.json()
        public_cases = data["public_cases"]
    except Exception:
        pass
    
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE problems SET public_cases = ? WHERE id = ?",
            (1 if public_cases else 0, problem_id, )
        )
        
        conn.commit()
        
        if cursor.rowcount == 0:
            response.status_code = 404
            return {
                "code": 404, 
                "msg": "problem not found",
                "data": None
            }
        
        response.status_code = 200
        return {
            "code": 200, 
            "msg": "log visibility updated",
            "data": {"problem_id": problem_id, "public_cases": public_cases}
        }
