from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import Agent
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OrgNet API",
    description="API for processing organizational network queries",
    version="1.0.0"
)

# Add CORS middleware with more specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Explicitly allow OPTIONS
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Initialize the agent
agent = Agent()

# Register functions
from agent import (
    create_task,
    generate_and_verify_certificate,
    create_notice,
    manage_leave,
    process_employee_payment
)

functions = [
    create_task,
    generate_and_verify_certificate,
    create_notice,
    manage_leave,
    process_employee_payment
]

for func in functions:
    agent.register_function(func)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    tool_called: str
    result: str

@app.post("/process-query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query using the agent.
    
    Args:
        request: QueryRequest object containing the query string
        
    Returns:
        QueryResponse object containing the tool called and result
    """
    try:
        result = agent.process_query(request.query)
        return QueryResponse(
            tool_called=result.get('tool_name', 'unknown'),
            result=result['result']
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """
    Root endpoint that returns API information.
    """
    return {
        "message": "Welcome to OrgNet API",
        "endpoints": {
            "/process-query": "POST - Process a query using the agent"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)