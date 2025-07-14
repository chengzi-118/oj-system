from fastapi import APIRouter, Request, Response
import sqlite3
from app.initialize_table import create_table
from shutil import rmtree
import time

reset = APIRouter()

@reset.post('/')
async def reset_sys(request: Request, response: Response):
    """
    Reset system.

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
    
    # Clear submissions
    try:
        rmtree("./app/submission")
    except Exception:
        pass

    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        # Clear all data
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS problems")
        cursor.execute("DROP TABLE IF EXISTS submissions")
        cursor.execute("DROP TABLE IF EXISTS languages")
        
    await create_table()
    request.session.pop("user_id")
    request.session.pop("user_name")
    request.session.pop("role")
    response.status_code = 200
    return {"code": 200, "msg": "system reset successfully", "data": None}
