from fastapi import APIRouter, Request, Response
import os
import json
import sqlite3
import asyncio
from app.code_judge import judge_in_docker
from app.page import get_page_detail
from datetime import datetime

submissions = APIRouter()

@submissions.post('/')
async def submit(request: Request, response: Response):
    """
    Submit for problems.
    
    Args: 
        problem_id: id of the problem.
        language: language of the code.
        code: code to be judged.
        
    Returns:
        200: success.
        400: format error.
        403: banned user.
        404: problem not found.
        429: frequncy out of limit.
        
    """
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    if request.session["role"] == "banned":
        response.status_code = 403
        return {"code": 403, "msg": "banned user", "data": None}
    
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    if "problem_id" not in data or "language" not in data or "code" not in data:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    now_time = datetime.now()
    if len(request.session["submit_time_list"]) == 3:
        if (
            now_time - datetime.fromisoformat(request.session["submit_time_list"][0])
        ).total_seconds() < 60:
            response.status_code = 429
            return {"code": 429, "msg": "frequncy out of limit", "data": None}
        else:
            request.session["submit_time_list"].pop(0)
            request.session["submit_time_list"].append(now_time.isoformat())
    else:
        request.session["submit_time_list"].append(now_time.isoformat())
    
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
        "data": {"submission_id": str(submission_id), "status": "pending"}
    }
        
@submissions.get('/{submission_id}/')
async def get_submission_info(
    submission_id: int,
    request: Request,
    response: Response
):
    """

    Args:
        submission_id (int): id of submission

    Returns:
        200: success.
        401: not logged in.
        403: insufficient permissions.
        404: submission not found.
        
    """
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
                "score": row[6],
                "counts": row[7],
              }
            }
        else:
            response.status_code = 404
            return {"code": 404, "msg": "submission not found", "data": None}
        
@submissions.get('/')
async def get_submissions(
    request: Request,
    response: Response,
    user_id: int = None,
    problem_id: str = None,
    status: str = None,
    page: int = None,
    page_size: int = None
):
    """
    Get submissions of certain requirements

    Args:
        user_id: id of the user.
        problem_id: id of the problem.
        status: status of the submission.
        page: page number.
        page_size: number of items in one page.

    Returns:
        _type_: _description_
    """
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    if user_id is None and problem_id is None:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    submissions: list = []
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM submissions")
        rows = cursor.fetchall()
        
    # Filter data    
    for row in rows:
        # User can only check own submission
        if request.session["role"] != "admin":
            if request.session["user_id"] != row[1]:
                continue
            
        if user_id is not None and user_id != row[1]:
            continue
            
        if problem_id is not None and problem_id != row[2]:
            continue    
        
        if status is not None and status != row[5]:
            continue    
        
        if row[5] == "success":
            submissions.append({
                "submission_id": str(row[0]),
                "status": row[5],
                "score": row[6],
                "counts": row[7]
            })
        else:
            submissions.append({
                "submission_id": str(row[0]),
                "status": row[5],
            })
        
    if submissions:
        result = get_page_detail(
            submissions,
            page,
            page_size
        )
        response.status_code = 200
        return {
            "code": 200, 
            "msg": "success", 
            "data": {"total": len(submissions), "submissions": result}
        }
    else:
        response.status_code = 200
        return {
            "code": 200, 
            "msg": "success", 
            "data": {"total": 0, "submissions": []}
        }     
                
@submissions.put('/{submission_id}/rejudge')
async def rejudge(
    submission_id: int,
    request: Request,
    response: Response
):
    """
    Rejudge by admin.
    
    Args:
        submission_id (int): id of submission
    
    Returns:
        200: success.
        401: not logged in.
        403: insufficient permissions.
        404: submission not found.
        
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
                "data": {"submission_id": str(submission_id), "status": "pending"}
            }
 
@submissions.get('/{submission_id}/log')   
async def see_log(submission_id: int, request: Request, response: Response):
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
        row = cursor.fetchone()
        if row:
            # Update view_logs
            cursor.execute(
                """INSERT INTO view_logs (
                    user_id, problem_id, time, status
                    ) VALUES (?, ?, ?, ?)""",
                (
                    row[1],
                    row[2],
                    datetime.now().strftime("%Y-%m-%d"),
                    "403" if request.session["role"] != "admin" \
                        and request.session["user_id"] != row[1] \
                        else "200",
                )
            )
            conn.commit()
            
            # Check permission
            if request.session["role"] == "admin":
                response.status_code = 200
                return {
                  "code": 200,
                  "msg": "success",
                  "data": {
                    "details": json.loads(str(row[8])),
                    "score": row[6],
                    "counts": row[7],
                  }
                }
            if request.session["user_id"] != row[1]:
                response.status_code = 403
                return {
                    "code": 403,
                    "msg": "insufficient permissions",
                    "data": None
                }
            
            # Search public cases
            cursor.execute("SELECT public_cases FROM problems WHERE id = ?", (row[2],))
            public_cases: bool = cursor.fetchone()[0]
            
            response.status_code = 200
            if public_cases:
                return {
                  "code": 200,
                  "msg": "success",
                  "data": {
                    "details": json.loads(str(row[8])),
                    "score": row[6],
                    "counts": row[7],
                  }
                }
            else:
                return {
                  "code": 200,
                  "msg": "success",
                  "data": {
                    "score": row[6],
                    "counts": row[7],
                  }
                }
        else:
            response.status_code = 404
            return {"code": 404, "msg": "submission not found", "data": None}
    