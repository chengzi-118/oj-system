from fastapi import APIRouter, Request, Response
import sqlite3
import json
import bcrypt

users = APIRouter()

@users.post('/admin')
async def create_admin(request: Request, response: Response):
    """
    Create admin account.
    
    Access:
        Admin.

    Args:
        username(str).
        password(str).

    Returns:
        200: success.
        400: user exists / format error.
        403: insufficient permissions.
    """
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    # Check params
    if "username" not in data or "password" not in data:
        response.status_code = 400
        return {"code": 400, "msg": "missing field", "data": None}
    if len(data["username"]) < 3 or len(data["username"]) > 21:
        response.status_code = 400
        return {"code": 400, "msg": "username invalid", "data": None}
    if len(data["password"]) < 6:
        response.status_code = 400
        return {"code": 400, "msg": "password too short", "data": None}
    
    # Check permission
    if "role" not in request.session or request.session["role"] != "admin":
        response.status_code = 403
        return {"code": 403, "msg": "insufficient permissions", "data": None}

    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, password, role) VALUES (?, ?, ?)",
                (
                    data["username"],
                    bcrypt.hashpw(
                        data["password"].encode('utf-8'),
                        bcrypt.gensalt(rounds = 12)
                    ).decode('utf-8'),
                    "admin",
                )
            )
            conn.commit()
            
            # Get user_id
            cursor.execute(
                "SELECT * FROM users WHERE name = ?",
                (data["username"], )
            )
            result = cursor.fetchone()
            return {
                "code": 200, 
                "msg": "success", 
                "data": {
                    "user_id": int(result[0]),
                    "username": data["username"]
                }
            }
        except sqlite3.IntegrityError:
            response.status_code = 400
            return {"code": 400, "msg": "user exists", "data": None}

@users.post('/')
async def create_user(request: Request, response: Response):
    """
    Create user.
    
    Access:
        Public.

    Args:
        username(str).
        password(str).

    Returns:
        200: success.
        400: user exists / format error.
    """
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    # Check params
    if "username" not in data or "password" not in data:
        response.status_code = 400
        return {"code": 400, "msg": "missing field", "data": None}
    if len(data["username"]) < 3 or len(data["username"]) > 20:
        response.status_code = 400
        return {"code": 400, "msg": "username invalid", "data": None}
    if len(data["password"]) < 6:
        response.status_code = 400
        return {"code": 400, "msg": "password too short", "data": None}

    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, password, role) VALUES (?, ?, ?)",
                (
                    data["username"],
                    bcrypt.hashpw(
                        data["password"].encode('utf-8'),
                        bcrypt.gensalt(rounds = 12)
                    ).decode('utf-8'),
                    "user",
                )
            )
            conn.commit()
            
            # Get user_id
            cursor.execute(
                "SELECT * FROM users WHERE name = ?",
                (data["username"], )
            )
            result = cursor.fetchone()
            return {
                "code": 200,
                "msg": "register success",
                "data": {"user_id": int(result[0])}
            }
        except sqlite3.IntegrityError:
            response.status_code = 400
            return {"code": 400, "msg": "user exists", "data": None}

# TODO
@users.get('/{user_id}')
async def get_info(user_id: int, request: Request, response: Response):
    """
    Get user's information.

    Args:
        user_id (int): id of the user.

    Returns:
        200: success.
        400: format error.
        401: not logged in.
        403: insufficient permissions.
        404: user not found.
    """
    # Check permission
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    if request.session["role"] != "admin" and request.session["user_id"] != user_id:
        response.status_code = 403
        return {"code": 403, "msg": "insufficient permissions", "data": None}
        
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id, )
            )
        result = cursor.fetchone()
        
        # Check whether result is None
        if result:
            response.status_code = 200
            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "user_id": result[0],
                    "username": result[1],
                    "role": result[3]
                }
            }
        else:
            response.status_code = 404
            return {"code": 404, "msg": "user not found", "data": None}

@users.put('/{user_id}/role')
async def change_role(user_id: int, request: Request, response: Response):
    """
    Change user's role.

    Args:
        user_id (int): id of the user.
        role(str): new role of the user.

    Returns:
        200: success.
        400: format error.
        401: not logged in.
        403: insufficient permissions.
        404: user not found.
    """
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    # Check permission
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    if request.session["role"] != "admin":
        response.status_code = 403
        return {"code": 403, "msg": "insufficient permissions", "data": None}
    
    # Check data
    role_list = ["user", "admin", "banned"]
    if "role" not in data or data["role"] not in role_list:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}

    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET role = ? WHERE id = ?",
            (data["role"], user_id, )
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            response.status_code = 404
            return {
                "code": 404, 
                "msg": "user not found",
                "data": None
            }
        
        response.status_code = 200
        return {
            "code": 200, 
            "msg": "role updated",
            "data": {"user_id": user_id, "role": data["role"]}
        }
 
# TODO       
@users.get('/')
async def get_users(request: Request, response: Response):
    """
    Get information of all users.

    Args:
        page(int)
        page_size(int)

    Returns:
        200: success.
        400: format error.
        401: not logged in.
        403: insufficient permissions.
        404: user not found.
    """
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        data = dict()
    
    # Check permission
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    if request.session["role"] != "admin":
        response.status_code = 403
        return {"code": 403, "msg": "insufficient permissions", "data": None}
    
    # Get all data
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        
    match_users = []
    
    for row in rows:
        match_users.append({"user_id": row[0]})
       
    if match_users:
        pagesize: int = len(match_users)
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
        }
    else:
        response.status_code = 200
        return {
            "code": 200, 
            "msg": "success", 
            "data": {"total": 0, "users": []}
        }
