from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from anthropic import Anthropic
from fastapi import Request
from pydantic import BaseModel
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


def chat(messages,system=None,temperature=0,stop_sequences=[]):

    params={"model":model,"max_tokens":1024,"messages":messages,"temperature":temperature,"stop_sequences":["5"]}

    if system:
        params["system"]=system
   
    message= client.messages.create(
        **params)
    return message.content[0].text 

messages = []

@app.get("/")
async def root():
    return {"message": "FastAPI server is running!"}

@app.post("/chat")
async def chatting(chat_request: ChatRequest):
    system_prompt=""""
    You are an expert programmer. You will answer the user's questions in a concise manner with best code.
    """
    try:
        user_input = chat_request.message
        add_user_message(messages, user_input)
        response = chat(messages,system=system_prompt,temperature=0,stop_sequences=[])
        add_assistant_message(messages, response)
        return {"message": response,"messageHistory": messages}
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

