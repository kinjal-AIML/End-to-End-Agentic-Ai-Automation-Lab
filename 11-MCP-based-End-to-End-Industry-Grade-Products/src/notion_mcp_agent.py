from models import get_model_clint, get_ollama_model
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams, mcp_server_tools
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import FunctionCallTermination, TextMentionTermination
import os
from dotenv import load_dotenv
import asyncio
load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_SECRET")
print(NOTION_API_KEY)

# """
# {
#   "mcpServers": {
#     "notionMCP": {
#       "command": "npx",
#       "args": ["-y", "mcp-remote", "https://mcp.notion.com/mcp"]
#     }
#   }
# }
# """

async def config():
    
    params = StdioServerParams(
    command="/usr/bin/npx",   # full path to npx
    args=["-y", "mcp-remote", "https://mcp.notion.com/mcp"],
    env={
        "NOTION_API_KEY": NOTION_API_KEY
    },
    read_timeout_seconds=20
    )


    # model = get_ollama_model()
    model = get_model_clint()

    mcp_tools = await mcp_server_tools(server_params=params)

    print("Loaded MCP tools:", [t.name for t in mcp_tools])

    system_prompt = f"""
    You are a helpful assistant connected to the Notion MCP server.

    Available tools:
    - notion-create-pages (create a new page)
    - notion-update-page (update an existing page)
    - notion-move-pages
    - notion-duplicate-page
    - notion-create-database
    - notion-update-database
    - notion-create-comment
    - notion-get-comments
    - notion-get-users
    - notion-get-self
    - notion-get-user
    - search
    - fetch

    Rules:
    - When the user asks you to create a page, you MUST call `notion-create-pages`.
    - Do not return JSON or curl commands unless explicitly asked.
    - Always use a tool invocation when completing a task.
    - Say TERMINATE when you are done.
"""



    agent = AssistantAgent(
        name="notion_agent",
        system_message=system_prompt,
        model_client=model,
        tools=mcp_tools,
        reflect_on_tool_use=True
    )

    team = RoundRobinGroupChat(
        participants=[agent],
        max_turns=20,
        termination_condition=TextMentionTermination("TERMINATE"),
    )

    return team



async def orchestrate(team, task):
    async for msg in team.run_stream(task=task):
        yield msg



async def main():
    team = await config()
    task = "write a simple paragraph about machinelearning in the 'Machine_learning' titled page. "

    async for msg in orchestrate(team, task):
        print("-"*120)
        print(msg)
        print("-"*100)

if __name__ == "__main__":
    asyncio.run(main())
