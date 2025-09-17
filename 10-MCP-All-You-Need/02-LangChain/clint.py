

import asyncio
import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load environment variables from a .env file
load_dotenv()

async def main():
    # --- Step 1: Ensure Prerequisites ---
    # Make sure you have the necessary packages installed:
    # pip install langchain-mcp-adapters langgraph langchain-groq python-dotenv "uv"
    #
    # Also, ensure your SERPER_API_KEY is set in your .env file.
    serper_api_key = os.getenv("SERPER_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")

    if not serper_api_key or not groq_api_key:
        print("Please make sure SERPER_API_KEY and GROQ_API_KEY are set in your .env file.")
        return

    # --- Step 2: Configure the MultiServerMCPClient ---
    # This client will manage the connections to all your tool servers.
    client = MultiServerMCPClient(
        {
            # Configuration for the Google Serper MCP server.
            # LangChain will start this server for you using these instructions.
            "serper": {
                "command": "uvx",  # The command to execute. [2, 7]
                "args": ["serper-mcp-server"],  # Arguments for the command. [2, 7]
                "env": {
                    "SERPER_API_KEY": serper_api_key  # Pass the API key as an environment variable. [2, 7]
                },
                "transport": "stdio" # Use standard input/output for communication.
            },
            
            # # You can still include your other servers
            # "math": {
            #     "command": "python",
            #     "args": ["mathserver.py"],  # Ensure this file is in the same directory
            #     "transport": "stdio",
            # },
            # "weather": {
            #     "url": "http://localhost:8000/mcp",  # Assumes this server is running separately
            #     "transport": "streamable_http",
            # }
        }
    )

    # --- Step 3: Get Tools, Create Model and Agent ---
    print("Fetching tools from MCP servers...")
    # The client connects to the servers and gets a list of available LangChain-compatible tools.
    tools = await client.get_tools()
    print("\n--- Available Tools ---")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
    print("-----------------------\n")
    
    # Initialize the language model you want to use
    # model = ChatGroq(model="openai/gpt-oss-20b")
    model = ChatOllama(model="qwen3:14b")

    # Create a ReAct agent that can use the fetched tools
    agent_executor = create_react_agent(model, tools)


    # --- Step 4: Use the Agent ---
    
    # Example 1: Using the Google Serper search tool
    prompt_search = (
        "Extract the wolton hith tech company, including:\n"
        "- Company name\n"
        "- Location/address\n"
        "- Chairman/CEO info\n"
        "- Social media links\n"
        "- Best product/service\n"
        "- Other relevant information"
        "-decision maker "
    )
    print(f"--- User Query: {prompt_search} ---")
    
    search_response = await agent_executor.ainvoke(
        {"messages": [{"role": "user", "content": prompt_search}]}
    )
    print("\n--- Agent Response ---")
    print(search_response['messages'][-1].content)
    print("------------------------\n")

    # # Example 2: Using the math tool
    # prompt_math = "what's (12 + 8) * 5?"
    # print(f"--- User Query: {prompt_math} ---")
    
    # math_response = await agent_executor.ainvoke(
    #     {"messages": [{"role": "user", "content": prompt_math}]}
    # )
    # print("\n--- Agent Response ---")
    # print(math_response['messages'][-1].content)
    # print("------------------------\n")
    
    # Close the connections to the servers when done
    # await client.close()

if __name__ == "__main__":
    asyncio.run(main())