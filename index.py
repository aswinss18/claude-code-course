from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from anthropic import Anthropic
from anthropic.types import ToolParam
from fastapi import Request
from pydantic import BaseModel
from datetime import datetime,timedelta
import uvicorn
import traceback


load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

client = Anthropic()
model = "claude-3-haiku-20240307"

class ChatRequest(BaseModel):
    message: str

def add_user_message(messages, content):
    user_message= {"role": "user", "content": content}
    messages.append(user_message)

def add_assistant_message(messages, content):
    assitant_message= {"role": "assistant", "content": content}
    messages.append(assitant_message)    
def get_current_datetime(format="%Y-%m-%d %H:%M:%S"):
    if not format:
        raise ValueError("Format string cannot be empty")
    return datetime.now().strftime(format)

get_current_datetime_schema=ToolParam({
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
                29
                if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
                else 28,
                31,
                30,
                31,
                30,
                31,
                31,
                30,
                31,
                30,
                31,
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

def chat(messages,system=None,temperature=0,stop_sequences=[]):

    params={"model":model,"max_tokens":1024,"messages":messages,"temperature":temperature,"tools":[get_current_datetime_schema]}

    if system:
        params["system"]=system

    message= client.messages.create(**params)

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

messages = []

@app.get("/")
async def root():
    return {"message": "FastAPI server is running!"}

@app.post("/chat")
async def chatting(chat_request: ChatRequest):
    system_prompt=""""
    You are an ai agents use the tools and give solution for users query.
    """
    try:
        user_input = chat_request.message
        add_user_message(messages, user_input)
        response = chat(messages,system=system_prompt,temperature=0,stop_sequences=[])
        add_assistant_message(messages, response)

        # Extract text from content blocks for React frontend
        response_text = ""
        for block in response:
            if hasattr(block, 'text'):
                response_text += block.text

        return {"message": response_text,"messageHistory": messages}
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

