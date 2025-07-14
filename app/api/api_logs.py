from fastapi import APIRouter, Request, Response
import sqlite3
from app.page import get_page_detail

logs = APIRouter()

@logs.get('/access/')
async def see_access(
    request: Request,
    response: Response,
    user_id: int = None,
    problem_id: str = None,
    page: int = None,
    page_size: int = None
):
    """
    Let admin see all visits of logs.
    
    Args:
        user_id (int, optional): id of the user. Defaults to None.
        problem_id (str, optional): id of the problem. Defaults to None.
        page: page number.
        page_size: number of items in one page.

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
    
    view_logs: list = []
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM view_logs")
        rows = cursor.fetchall()
        
    # Filter data    
    for row in rows:
        if user_id is not None and user_id != row[1]:
            continue
            
        if problem_id is not None and problem_id != row[2]:
            continue    
        view_logs.append({
                "user_id": str(row[1]),
                "problem_id": row[2],
                "action": "view_log",
                "time": row[3],
                "status": str(row[4])
            })
    
    if view_logs:
        try:
            result = get_page_detail(
                view_logs,
                page,
                page_size
            )
        except KeyError:
            response.status_code = 400
            return {
                "code": 400, 
                "msg": "format error", 
                "data": None
            }
        response.status_code = 200
        return {
            "code": 200, 
            "msg": "success", 
            "data": result
        }
    else:
        response.status_code = 200
        return {
            "code": 200, 
            "msg": "success", 
            "data": []
        }     