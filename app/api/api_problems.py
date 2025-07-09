from fastapi import APIRouter, Request, Response
import os
import json
from problem_data import ProblemProfile
import shutil

problems = APIRouter()

@problems.get('/')
async def get(response: Response) -> dict:
    """
    Check the list of problems.
    
    Access:
        Public.
        
    Returns:
        dict: dict of id and title of all problems
    """
    problems_profile: list[dict] = [] 
    for item_name in os.listdir('./problems'):
        with open(f'./problems/{item_name}/data.json', 'r', encoding = 'utf-8') as f:
            data = json.loads(f.read())
            filtered_data: dict = {"id": data["id"], "title": data["title"]}
            problems_profile.append(filtered_data)
    ret = {"code": 200, "msg": "success", "data": problems_profile}
    response.status_code = 200
    return ret

@problems.post('/')
async def post(request: Request, response: Response):
    """
    Add problems.
    
    Access:
        Public.

    Returns:
        200: success
        400: missing field / format error
        409: id exists
    """
    data = await request.json()
    
    # Check whether data is legal
    try:
        p = ProblemProfile(**data)
    except TypeError:
        response.status_code = 400
        return {"code": 400, "msg": "missing field / format error", "data": None}
    
    # Check whether the problem exists
    for item_name in os.listdir('./problems'):
        if item_name == str(p.id):
            response.status_code = 409
            return {"code": 409, "msg": "id exists", "data": None}
    
    p.save_to_local()
    response.status_code = 200
    ret = {"code": 200, "msg": "add success", "data": {"id": p.id}}
    return ret

@problems.get('/{problem_id}')
async def get_info(problem_id: str, response: Response):
    """
    Check the problem information.
    
    Access:
        Public.
        
    Args:
        problem_id (str): id of the problem
        
    Returns:
        dict: dict of problem's information
    """
    for item_name in os.listdir('./problems'):
        if problem_id == item_name:
            response.status_code = 200
            with open(f'./problems/{item_name}/data.json', 'r', encoding = 'utf-8') as f:
                data = json.loads(f.read())
                return {"code": 200, "msg": "success", "data": data}
    response.status_code = 404
    return {"code": 404, "msg": "problem not found", "data": None}

@problems.delete('/{problem_id}')
async def delete(problem_id: str, response: Response):
    """
    Delete problems.
    
    Access:
        Admin.

    Args:
        problem_id (str): id of the problem
        
    Returns:
        200: successfully deleted
        404: problem not found
    """
    for item_name in os.listdir('./problems'):
        if problem_id == item_name:
            response.status_code = 200
            shutil.rmtree(f'./problems/{problem_id}')
            return {"code": 200, "msg": "delete success", "data": {"id": problem_id}}
            
    response.status_code = 404
    return {"code": 404, "msg": "problem not found", "data": None}
