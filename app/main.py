from fastapi import FastAPI
import uvicorn
from app.api.api_problems import problems
from app.api.api_submissions import submissions
from app.api.api_auth import auth
from app.api.api_users import users
from app.api.api_languages import languages
from app.api.api_reset import reset
from app.api.api_export import export_data
from app.api.api_import import import_data
from app.api.api_logs import logs
from app.initialize_table import create_table
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

# Call the function before the app starts listening for requests
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_table()
    yield
        
app = FastAPI(
    title="Simple OJ System - Student Template",
    description="A simple online judge system for programming assignments",
    version="1.0.0",
    lifespan = lifespan
)

app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

app.include_router(problems, prefix = '/api/problems')
app.include_router(submissions, prefix = '/api/submissions')
app.include_router(auth, prefix = '/api/auth')
app.include_router(users, prefix = '/api/users')
app.include_router(languages, prefix = '/api/languages')
app.include_router(reset, prefix = '/api/reset')
app.include_router(export_data, prefix = '/api/export')
app.include_router(import_data, prefix = '/api/import')
app.include_router(logs, prefix = '/api/logs')

@app.get("/")
async def welcome():
    return "Welcome!"

if __name__ == '__main__':
    uvicorn.run(app)
