from fastapi import APIRouter, Request, Response
import sqlite3
import json

languages = APIRouter()

@languages.post('/')
async def add_language(request: Request, response: Response):
    """
    Add a new language.
    
    Args:
        name: name of the language.
        file_ext: extension name of the file.
        run_cmd: command of running the code.
        compile_cmd: command of compiling the code.
        source_template: template of the code.
        time_limit: limit of time by default.
        memory_limit: limit of memory by default.
    """
    # Check whether user logged in
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    if "name" not in data or "file_ext" not in data or "run_cmd" not in data:
        response.status_code = 400
        return {"code": 400, "msg": "format error", "data": None}
    
    # Check whether optional needs in data.
    optional = ["compile_cmd", "source_template", "time_limit", "memory_limit"]
    for item in optional:
        if item not in data:
            data[item] = ""
    
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                    """INSERT INTO languages (
                        name, file_ext, compile_cmd, run_cmd,
                        source_template, time_limit, memory_limit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        data["name"], data["file_ext"],data["compile_cmd"],
                        data["run_cmd"], data["source_template"],
                        data["time_limit"], data["memory_limit"]
                    )
                )
        except sqlite3.IntegrityError:
            response.status_code = 400
            return {"code": 400, "msg": "language exists", "data": None}

    response.status_code = 200
    return {
        "code": 200,
        "msg": "language registered",
        "data": {"name": data["name"]}
    }    
        
@languages.get('/')
async def get_language_info(request: Request, response: Response):
    """
    Get information of all languages.

    Returns:
        401: not logged in.
        200: success.
    """
    # Check whether user logged in
    if "user_id" not in request.session:
        response.status_code = 401
        return {"code": 401, "msg": "not logged in", "data": None}
    
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM languages")
        rows = cursor.fetchall()
    
    all_languages = []
    for item in rows:
        all_languages.append(item[0])
        
    return {
        "code": 200,
        "msg": "success",
        "data": {"name": all_languages}
    }
    