from fastapi import APIRouter, Request, Response, UploadFile, File, HTTPException
import sqlite3
import json

import_data = APIRouter()

@import_data.post('/')
async def importing(file: UploadFile, request: Request, response: Response):
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
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files supported")
    
    # Read file
    content = await file.read()
    data = json.loads(content.decode('utf-8'))
    
    
    
    
    