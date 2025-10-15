from fastapi import FastAPI, HTTPException,Depends,Response,status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from anthropic import Anthropic
from anthropic.types import ToolParam
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import uvicorn
import traceback
import os
import time
from . import models
from .database import engine,get_db,Base
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import schemas

# Create database tables
models.Base.metadata.create_all(bind=engine)

from contextlib import contextmanager

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(BaseModel):
    username: str
    email: str
    password: str
    subscriber: bool = False
    ai_personality: Optional[str] = None

# Database connection pool
db_pool = None

def init_db_pool():
    global db_pool
    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,  # min and max connections
            host='postgres',
            database='ai-chat-bot',
            user='postgres',
            password='4166',
            cursor_factory=RealDictCursor
        )
        print("🟢 🟢 🟢 Database connection pool created successfully! 🟢 🟢 🟢")
    except Exception as error:
        print("🔴 🔴 🔴 Database connection pool creation failed! 🔴 🔴 🔴")
        print("Error:", error)

def get_db_connection():
    global db_pool
    if db_pool:
        return db_pool.getconn()
    return None

def return_db_connection(conn):
    global db_pool
    if db_pool and conn:
        db_pool.putconn(conn)


@contextmanager
def get_db_cursor():
    """Context manager for database operations"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection not available")
        cursor = conn.cursor()
        yield cursor
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    else:
        if conn:
            conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_db_connection(conn)

# Initialize Anthropic client with API key from environment
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")
client = Anthropic(api_key=api_key)

# Use latest model for better performance
model = "claude-3-haiku-20240307"  # Using a stable model

class ChatRequest(BaseModel):
    message: str

class User(BaseModel):
    id: int
    username: str
    email: str
    subscriber: bool
    created_at: datetime
    updated_at: datetime
    password: str
    ai_personality: Optional[str] = None

def add_user_message(messages, content):
    user_message = {"role": "user", "content": content}
    messages.append(user_message)

def add_assistant_message(messages, content):
    assistant_message = {"role": "assistant", "content": content}
    messages.append(assistant_message)

def get_current_datetime(format="%Y-%m-%d %H:%M:%S"):
    if not format:
        raise ValueError("Format string cannot be empty")
    return datetime.now().strftime(format)

get_current_datetime_schema = ToolParam({
    "name": "get_current_datetime",
    "description": "Get the current date and time in a specified format",
    "input_schema": {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "description": "Python strftime format string (e.g., '%Y-%m-%d %H:%M:%S', '%B %d, %Y')",
                "default": "%Y-%m-%d %H:%M:%S"
            }
        },
        "additionalProperties": False
    }
})

def add_duration_to_datetime(
    datetime_str, duration=0, unit="days", input_format="%Y-%m-%d"
):
    date = datetime.strptime(datetime_str, input_format)

    if unit == "seconds":
        new_date = date + timedelta(seconds=duration)
    elif unit == "minutes":
        new_date = date + timedelta(minutes=duration)
    elif unit == "hours":
        new_date = date + timedelta(hours=duration)
    elif unit == "days":
        new_date = date + timedelta(days=duration)
    elif unit == "weeks":
        new_date = date + timedelta(weeks=duration)
    elif unit == "months":
        month = date.month + duration
        year = date.year + month // 12
        month = month % 12
        if month == 0:
            month = 12
            year -= 1
        day = min(
            date.day,
            [
                31,
                29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
            ][month - 1],
        )
        new_date = date.replace(year=year, month=month, day=day)
    elif unit == "years":
        new_date = date.replace(year=date.year + duration)
    else:
        raise ValueError(f"Unsupported time unit: {unit}")

    return new_date.strftime("%A, %B %d, %Y %I:%M:%S %p")

def process_tool_call(tool_name, tool_input):
    if tool_name == "get_current_datetime":
        return get_current_datetime(tool_input.get("format", "%Y-%m-%d %H:%M:%S"))
    else:
        return f"Unknown tool: {tool_name}"

def chat(messages, system=None, temperature=0, stop_sequences=None):
    if stop_sequences is None:
        stop_sequences = []

    params = {
        "model": model,
        "max_tokens": 1024,
        "messages": messages,
        "temperature": temperature,
        "tools": [get_current_datetime_schema]
    }

    if system:
        params["system"] = system

    message = client.messages.create(**params)

    # Handle tool use loop
    while message.stop_reason == "tool_use":
        # Add assistant message with tool use
        add_assistant_message(messages, message.content)

        # Process tool calls and create tool results
        tool_results = []
        for content_block in message.content:
            if content_block.type == "tool_use":
                tool_result = process_tool_call(content_block.name, content_block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": tool_result
                })

        # Add user message with tool results
        add_user_message(messages, tool_results)

        # Continue conversation
        params["messages"] = messages
        message = client.messages.create(**params)

    return message.content

# Use a dictionary to store conversation history per session
# In production, use Redis or a database
conversation_store = {}

@app.on_event("startup")
async def startup_event():
    """Initialize database connection pool on startup"""
    init_db_pool()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection pool on shutdown"""
    global db_pool
    if db_pool:
        db_pool.closeall()
        print("🔴 Database connection pool closed")

@app.get("/")
async def root():
    return {"message": "FastAPI server is running!"}

@app.post("/chat")
async def chatting(chat_request: ChatRequest):
    system_prompt = """
    You are an expert mathematician and helpful assistant.
    """
    try:
        # For this simple version, use a global messages list
        # In production, use session IDs
        if "default" not in conversation_store:
            conversation_store["default"] = []
        
        messages = conversation_store["default"]
        
        user_input = chat_request.message
        add_user_message(messages, user_input)
        response = chat(messages, system=system_prompt, temperature=0, stop_sequences=[])
        add_assistant_message(messages, response)

        # Extract text from content blocks for React frontend
        response_text = ""
        for block in response:
            if hasattr(block, 'text'):
                response_text += block.text

        return {"message": response_text, "messageHistory": messages}
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/reset_conversation")
async def reset_conversation():
    """Reset conversation history"""
    conversation_store["default"] = []
    return {"message": "Conversation reset successfully"}

@app.get("/users", status_code=status.HTTP_200_OK)
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    # Convert to UserResponse format manually to exclude password
    user_responses = [schemas.UserResponse.model_validate(user) for user in users]
    return {"data": user_responses}

@app.get("/users/{email}", status_code=status.HTTP_200_OK)
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {email} not found"
        )
    # Convert to UserResponse format to exclude password
    user_response = schemas.UserResponse.model_validate(user)
    return {"data": user_response} 

@app.post("/user", status_code=status.HTTP_201_CREATED)
def create_user(new_user: schemas.CreateUser, db: Session = Depends(get_db)):
    try:
        # Check if user with this email already exists
        existing_user = db.query(models.User).filter(models.User.email == new_user.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {new_user.email} already exists"
            )
        
        # Create new user
        db_user = models.User(**new_user.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        # Convert to UserResponse format to exclude password
        user_response = schemas.UserResponse.model_validate(db_user)
        return {"message": "User created successfully", "data": user_response}
    
    except IntegrityError as e:
        db.rollback()
        # Handle unique constraint violations
        if "users_email_key" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {new_user.email} already exists"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database constraint violation"
            )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the user: {str(e)}"
        ) 

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)