from fastapi import APIRouter, Request, Response
import sqlite3

export = APIRouter()

@export.get('/')
async def export_data(request: Request, response: Response):
    pass


