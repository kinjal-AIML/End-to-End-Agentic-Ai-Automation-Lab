from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI    
import os
from dotenv import load_dotenv
# Load environment variables from a .env file
load_dotenv()
import asyncio

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0)

SERVERS = {
    "my-mcp-server-expense": {
        "transport": "stdio",
        "command": "/home/md-al-amin/.local/bin/uv",
        "args":[
            "run",
            "/home/md-al-amin/My-Projects/End-to-End-Agentic-Ai-Automation-Lab/11.5-Advanced-MCP-ownMCPs/00-Locla-mcp-Server/01-adv-expence-tracker-server/main.py",
        ]
    }
}

async def main():
    print("Starting MCP Client...")

    # Initialize the client directly (no "async with")
    client = MultiServerMCPClient(SERVERS)
    
    # Fetch the tools
    tools = await client.get_tools()
    
    print("\nSuccessfully connected!")
    print("Found tools:", tools)

if __name__ == "__main__":
    asyncio.run(main())