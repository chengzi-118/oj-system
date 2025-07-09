from fastapi import FastAPI
import uvicorn
from api.api_problems import problems
from api.api_submissions import submissions

app = FastAPI(
    title="Simple OJ System - Student Template",
    description="A simple online judge system for programming assignments",
    version="1.0.0"
)

app.include_router(problems, prefix = '/api/problems')
app.include_router(submissions, prefix = '/api/submissions')

@app.get("/")
async def welcome():
    return "Welcome!"


if __name__ == '__main__':
    uvicorn.run(app)