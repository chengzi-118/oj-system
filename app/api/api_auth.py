from fastapi import APIRouter, Request, Response
import sqlite3
import bcrypt
import json

auth = APIRouter()

@auth.post('/login')
async def login(request: Request, response: Response):
    """
    Login with username and password.

    Access:
        Public.
        
    Args:
        username(str).
        password(str).

    Returns:
        dict of data of the user.
    """
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
        
    # Check whether data is legal
    if "username" not in data or "password" not in data:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    with sqlite3.connect('./users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name == ?", (data['username'], ))
        result = cursor.fetchone()
        if result:
            if result[3] == "banned":
                response.status_code = 403
                return {"code": 403, "msg": "banned user", "data": None}
            
            # Check password
            if bcrypt.checkpw(data['password'].encode('utf-8'), result[2].encode('utf-8')):
                request.session["user_id"] = result[0]
                request.session["user_name"] = data['username']
                request.session["role"] = result[3]
                response.status_code = 200
                return {
                    "code": 200,
                    "msg": "login success",
                    "data": {
                        "user_id": result[0],
                        "username": data['username'],
                        "role": result[3]
                    }
                }
    response.status_code = 401
    return {"code": 401, "msg": "wrong name or password", "data": None}

@auth.post('/logout')
async def logout(request: Request, response: Response):
    """
    Logout.

    Returns:
        200: success.
        401: fail.
    """
    
    # Check whether user has logged in
    if "user_id" in request.session:
        request.session.pop("user_id")
        request.session.pop("user_name")
        request.session.pop("role")
        response.status_code = 200
        return {"code": 200, "msg": "logout success", "data": None}
    else:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}

