from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from pyngrok import ngrok
import uvicorn
from notion_mcp_agent import config
import asyncio

# Load env variables
load_dotenv()
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
print(f"NGROK_AUTH_TOKEN: {NGROK_AUTH_TOKEN}")

# --- API Setup Start ---
app = FastAPI()

# Enable CORS (allow all origins, adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "messages": "Welcome to API Tunneling."
    }

@app.get("/health")
def health():
    return {
        "messages": "Ok"
    }

@app.get("/api/hello")
async def test_line():
    return {"messages": "Hello from the Linux Machine."}


async def run_task(task: str) ->str:
    team = await config()

    output = []
    async for msg in team.run_stream(task=task):
        output.append(str(msg))

    return "\n\n\n".join(output)


# ============================================================

@app.post("/run")
def run(task: str):
    try:
        if task:
            result = asyncio.run(run_task(task))
            return result

    except Exception as e:
        return f"The error is{e}"

if __name__ == "__main__":
    port = 7001
    
    # Setup ngrok
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    public_url = ngrok.connect(port)
    
    print(f"Public URL: {public_url}/api/hello\n\n")

    # Run FastAPI with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
