# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client
# from langchain_mcp_adapters.tools import load_mcp_tools
# from langgraph.prebuilt import create_react_agent # Example for agent creation
from langchain_ollama import ChatOllama

# # Configure server parameters for stdio connection (adjust path if needed)
# server_params = StdioServerParameters(
#     command="npx",
#     args=["@playwright/mcp@latest"]
# )

model = ChatOllama(model="qwen3:14b")

# async def run_agent_with_playwright():
#     async with stdio_client(server_params) as (read, write):
#         async with ClientSession(read, write) as session:
#             await session.initialize()
#             tools = await load_mcp_tools(session)
#             print(tools)

#             # Example: Create and run a LangChain agent with these tools
#             # Replace "openai:gpt-4.1" with your desired LLM
#             agent = create_react_agent(model, tools)
#             agent_response = await agent.ainvoke({"messages": "Open gtrbd.com and take a screenshot."})
#             print(agent_response)

# # Run the asynchronous function
# import asyncio
# asyncio.run(run_agent_with_playwright())


# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client
# from langchain_mcp_adapters.tools import load_mcp_tools
# from langgraph.prebuilt import create_react_agent # Example for agent creation
# from dotenv import load_dotenv
# load_dotenv()
# from langchain_groq import ChatGroq
# import os
# os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")


# llm = ChatGroq(model="qwen/qwen3-32b")

# # Configure server parameters for stdio connection
# server_params = StdioServerParameters(
#     command="npx",
#     args=[
#         "@playwright/mcp@latest",
#         "--browser", "chrome",  # Explicitly select a browser, e.g., chrome, firefox, webkit
#         "--viewport-size", "1280,720" # Set a specific window size
#     ]
# )

# async def run_agent_with_playwright():
#     async with stdio_client(server_params) as (read, write):
#         async with ClientSession(read, write) as session:
#             await session.initialize()
#             tools = await load_mcp_tools(session)
#             print("TOols are---> ", tools, "<---- tools end")

#             # Example: Create and run a LangChain agent with these tools
#             # Replace "openai:gpt-4.1" with your desired LLM
#             agent = create_react_agent(llm, tools)
#             agent_response = await agent.ainvoke({"messages": "Open gtrbd.com and take a screenshot."})
#             print(agent_response)

# # Run the asynchronous function
# import asyncio
# asyncio.run(run_agent_with_playwright())


from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os
import asyncio

# --- Setup ---
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

llm = ChatGroq(model="qwen/qwen3-32b")

# --- Server Configuration ---
# Switched from "chrome" to "chromium" to use the browser Playwright installs by default.
server_params = StdioServerParameters(
    command="npx",
    args=[
        "@playwright/mcp@latest",
        "--browser", "chromium",  # Use the browser we know is installed
        "--viewport-size", "1280,720"
    ]
)

async def run_agent_with_playwright():
    print("Attempting to start Playwright MCP server with Chromium...")
    try:
        async with stdio_client(server_params) as (read, write):
            print("MCP server process started.")
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                print("Tools loaded successfully.")

                agent = create_react_agent(model, tools)

                # New prompt: Start by ensuring the browser is installed,
                # then navigate and wait.
                prompt = (
                    "First, run the browser_install tool to make sure the browser is ready. "
                    "Then, open https://www.whatismybrowser.com/, wait for 15 seconds, and take a screenshot."
                )
                
                print(f"\nSending prompt to agent: '{prompt}'")
                agent_response = await agent.ainvoke({"messages": prompt})
                
                print("\n--- Agent Final Response ---")
                print(agent_response)
                print("--------------------------")

                print("\nAgent task finished. The browser will remain open for 10 more seconds.")
                await asyncio.sleep(10)

    except Exception as e:
        print(f"\n--- AN ERROR OCCURRED ---")
        print(f"Error: {e}")
        print("This could be due to missing system dependencies for the browser.")
        print("On Linux, try running 'npx playwright install-deps' and then run this script again.")
        print("-------------------------\n")


# --- Run the Script ---
if __name__ == "__main__":
    print("Running the agent with Playwright...")
    # On Linux, if you still have issues, you may need to run this command in your terminal first:
    # npx playwright install-deps
    asyncio.run(run_agent_with_playwright())
    print("\nScript finished.")