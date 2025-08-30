from models import get_model_clint
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams, mcp_server_tools
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import FunctionCallTermination, TextMentionTermination
import os
from dotenv import load_dotenv
load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_SECRET")

"""
{
  "mcpServers": {
    "notionMCP": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.notion.com/mcp"]
    }
  }
}
"""

async def config():
    params = StdioServerParams(
        command="npx",
        args = ["-y", "mcp-remote", "https://mcp.notion.com/mcp"],
        env = {
            "NOTION_API_KEY": NOTION_API_KEY
        },
        read_timeout_seconds=20
    )

    model = get_model_clint()

    mcp_tools = mcp_server_tools(server_params=params)
    system_prompt = "You are a helpful assistant that can search and summarize content from the user's Notion workspace and also list what is asked. Try to assume the tool and call the same and get the answer. Say TERMINATE when you are done with the task."

    agent = AssistantAgent(
        name="notion_agent",
        system_message=system_prompt,
        model_client=model,
        tools=mcp_tools,
        reflect_on_tool_use=True
    )

    team = RoundRobinGroupChat(
        participants=[agent],
        max_turns=8,
        termination_condition=TextMentionTermination("TERMINATE")
    )

    return team