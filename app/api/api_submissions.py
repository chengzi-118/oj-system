from fastapi import APIRouter, Request, Response
import os
import json
from problem_data import ProblemProfile
import shutil

submissions = APIRouter()

@submissions.post('/')
async def post(request: Request, response: Response):
    pass