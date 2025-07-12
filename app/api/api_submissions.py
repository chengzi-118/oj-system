from fastapi import APIRouter, Request, Response
import os
import json
import sqlite3
from app.problem_data import ProblemProfile
import asyncio
from app.code_judge import judge_in_docker

submissions = APIRouter()

SCORE = 10

@submissions.post('/')
async def submit(request: Request, response: Response):
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    if "problem_id" not in data or "language" not in data or "code" not in data:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    if request.session["role"] == "banned":
        response.status_code = 403
        return {"code": 403, "msg": "banned user", "data": None}
    
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        
        # Check problem exists
        cursor.execute("SELECT * FROM problems WHERE id = ?", (data["problem_id"],))
        row = cursor.fetchone()
        
        if not row:
            response.status_code = 404
            return {"code": 404, "msg": "problem not found", "data": None}
        
        cursor.execute(
                """INSERT INTO submissions (
                    user_id, problem_id, code, language, status
                ) VALUES (?, ?, ?, ?, ?)""",
                (
                    request.session["user_id"],
                    data["problem_id"],
                    data["code"],
                    data["language"],
                    "pending",
                )
            )
        conn.commit()
        
        submission_id = cursor.lastrowid
    
    # Start to judge    
    asyncio.create_task(
        judge_in_docker(
            submission_id, 
            data["problem_id"], 
            data["code"],
            data["language"]
        )
    )
        
    response.status_code = 200
    return {
        "code": 200,
        "msg": "success",
        "data": {"submission_id": submission_id, "status": "pending"}
    }
        
@submissions.get('/{submission_id}/')
async def get_submission_info(
    submission_id: int,
    request: Request,
    response: Response
):     
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
        row = cursor.fetchone()
        if row:
            # Check permission
            if request.session["user_id"] != row[1]:
                if request.session["role"] != "admin":
                    response.status_code = 403
                    return {
                        "code": 403,
                        "msg": "insufficient permissions",
                        "data": None
                    }
    
            return {
              "code": 200,
              "msg": "success",
              "data": {
                "score": SCORE,
                "counts": row[6],
              }
            }
        else:
            response.status_code = 404
            return {"code": 404, "msg": "submission not found", "data": None}
        
@submissions.get('/')
async def get_all_submissions(request: Request, response: Response):
    pass
 
@submissions.put('/{submission_id}/rejudge')
async def rejudge(
    submission_id: int,
    request: Request,
    response: Response
):     
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    # Check permission
    if request.session["role"] != "admin":
        response.status_code = 403
        return {"code": 403, "msg": "insufficient permissions", "data": None}
    
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
        row = cursor.fetchone()
        if not row:
            response.status_code = 404
            return {"code": 404, "msg": "submission not found", "data": None}
        else:
            asyncio.create_task(judge_in_docker(submission_id, row[2], row[3], row[4]))
            response.status_code = 200
            return {
                "code": 200,
                "msg": "rejudge started",
                "data": {"submission_id": submission_id, "status": "pending"}
            }
    
    
    """pagesize: int = len(match_users)
        if "page_size" in data:
            pagesize = data["page_size"]
           
        page: int = 0 
        if "page" in data:
            page = data["page"]
        
        result = match_users[
            pagesize * page : pagesize * (page + 1)
        ]
        response.status_code = 200
        return {
            "code": 200, 
            "msg": "success", 
            "data": {"total": len(result), "users": result}
        }"""
    
    
    
    
           