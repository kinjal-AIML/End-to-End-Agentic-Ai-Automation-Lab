
# from langchain_ollama import ChatOllama
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client
# from langchain_mcp_adapters.tools import load_mcp_tools
# from langgraph.prebuilt import create_react_agent
# from dotenv import load_dotenv
# from langchain_groq import ChatGroq
# import os
# import asyncio

# # --- Setup ---
# load_dotenv()
# os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# llm = ChatGroq(model="qwen/qwen3-32b")
# model = ChatOllama(model="qwen3:14b")

# # --- Server Configuration ---
# # Switched from "chrome" to "chromium" to use the browser Playwright installs by default.
# server_params = StdioServerParameters(
#     command="npx",
#     args=[
#         "@playwright/mcp@latest",
#         "--browser", "chromium",  # Use the browser we know is installed
#         "--viewport-size", "1280,720"
#     ]
# )

# async def run_agent_with_playwright():
#     print("Attempting to start Playwright MCP server with Chromium...")
#     try:
#         async with stdio_client(server_params) as (read, write):
#             print("MCP server process started.")
#             async with ClientSession(read, write) as session:
#                 await session.initialize()
#                 tools = await load_mcp_tools(session)
#                 print("Tools loaded successfully.")

#                 agent = create_react_agent(model, tools)

#                 # New prompt: Start by ensuring the browser is installed,
#                 # then navigate and wait.
#                 prompt = (
#                     "First, run the browser_install tool to make sure the browser is ready. "
#                     "Then, open https://www.whatismybrowser.com/, wait for 15 seconds, and take a screenshot."
#                 )
                
#                 print(f"\nSending prompt to agent: '{prompt}'")
#                 agent_response = await agent.ainvoke({"messages": prompt})
                
#                 print("\n--- Agent Final Response ---")
#                 print(agent_response)
#                 print("--------------------------")

#                 print("\nAgent task finished. The browser will remain open for 10 more seconds.")
#                 await asyncio.sleep(10)

#     except Exception as e:
#         print(f"\n--- AN ERROR OCCURRED ---")
#         print(f"Error: {e}")
#         print("This could be due to missing system dependencies for the browser.")
#         print("On Linux, try running 'npx playwright install-deps' and then run this script again.")
#         print("-------------------------\n")


# # --- Run the Script ---
# if __name__ == "__main__":
#     print("Running the agent with Playwright...")
#     # On Linux, if you still have issues, you may need to run this command in your terminal first:
#     # npx playwright install-deps
#     asyncio.run(run_agent_with_playwright())
#     print("\nScript finished.")


from langchain_ollama import ChatOllama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import os
import asyncio
import json
import tempfile
import atexit
import traceback

# --- Setup ---
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["PLAYWRIGHT_LOG"] = "debug"  # Enable Playwright debug logs

# Use ChatOllama
model = ChatOllama(model="qwen3:14b")  # Revert to qwen3:14b if needed

# --- Create Temporary Config File ---
def create_mcp_config():
    config = {
        "launchOptions": {
            "headless": False,
            "slowMo": 500
        },
        "contextOptions": {
            "viewport": {
                "width": 1280,
                "height": 720
            }
        }
    }
    temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(config, temp_config, indent=2)
    temp_config.close()
    return temp_config.name

config_path = create_mcp_config()
atexit.register(lambda: os.unlink(config_path))

# --- Server Configuration ---
server_params = StdioServerParameters(
    command="npx",
    args=[
        "@playwright/mcp@latest",
        "--browser", "chromium",
        f"--config={config_path}",
        "--verbose"  # Enable verbose MCP logs
    ]
)

async def test_direct_browser():
    """Test MCP server directly to ensure browser launches visibly."""
    print("\n--- Testing Direct Browser Launch ---")
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                await session.execute("goto", {"url": "https://www.whatismybrowser.com/"})
                print("Browser should be open to whatismybrowser.com")
                await asyncio.sleep(10)  # Keep open briefly
    except Exception as e:
        print(f"Direct browser test failed: {e}")
        traceback.print_exc()

async def run_agent_with_playwright():
    print("Attempting to start Playwright MCP server with Chromium (non-headless via config)...")
    print(f"Using config file: {config_path}")
    try:
        async with stdio_client(server_params) as (read, write):
            print("MCP server process started.")
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                print("Tools loaded successfully.")

                agent = create_react_agent(model, tools)

                # Simplified prompt to isolate issue
                prompt = (
                    "Open https://www.whatismybrowser.com/, wait for 10 seconds, "
                    "take a screenshot, and save it to 'screenshot.png'."
                )
                
                print(f"\nSending prompt to agent: '{prompt}'")
                agent_response = await agent.ainvoke({"messages": prompt})
                
                print("\n--- Agent Final Response ---")
                print(agent_response)
                print("--------------------------")

                print("\nKeeping browser open for 30 seconds to observe actions...")
                await asyncio.sleep(30)

    except Exception as e:
        print(f"\n--- AN ERROR OCCURRED ---")
        print(f"Error: {e}")
        print("Full stack trace:")
        traceback.print_exc()
        print("\nPossible causes:")
        print("- Ollama server not running or model 'qwen3:7b' not pulled. Run 'ollama serve' and 'ollama pull qwen3:7b'.")
        print("- Playwright dependencies missing. Run 'npx playwright install-deps' on Linux.")
        print("- No display server (e.g., X11/Wayland). Check 'echo $DISPLAY' or use 'xvfb-run'.")
        print("- Agent tool execution failure. Check MCP tool compatibility with Ollama.")
        print(f"To debug MCP, run: 'npx @playwright/mcp@latest --browser chromium --config {config_path} --verbose'")
        print("-------------------------\n")

# --- Run the Script ---
if __name__ == "__main__":
    print("Running the agent with Playwright...")
    # First, test direct browser launch
    asyncio.run(test_direct_browser())
    # Then, run agent
    asyncio.run(run_agent_with_playwright())
    print("\nScript finished.")