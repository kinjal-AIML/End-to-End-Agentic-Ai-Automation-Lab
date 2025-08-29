from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from pyngrok import ngrok
import uvicorn

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

@app.get("/api/hello")
async def test_line():
    return {"messages": "Hello from the Linux Machine."}


if __name__ == "__main__":
    port = 7001
    
    # Setup ngrok
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    public_url = ngrok.connect(port)
    
    print(f"Public URL: {public_url}/api/hello\n\n")

    # Run FastAPI with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
