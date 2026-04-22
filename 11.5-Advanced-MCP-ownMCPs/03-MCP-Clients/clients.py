from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI    
from langchain_core.messages import ToolMessage
import json

import os
from dotenv import load_dotenv
# Load environment variables from a .env file
load_dotenv()
import asyncio

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o", temperature=0)

SERVERS = {
    # "my-mcp-server-expense": {
    #     "transport": "stdio",
    #     "command": "/home/md-al-amin/.local/bin/uv",
    #     "args":[
    #         "run",
    #         "/home/md-al-amin/My-Projects/End-to-End-Agentic-Ai-Automation-Lab/11.5-Advanced-MCP-ownMCPs/00-Locla-mcp-Server/01-adv-expence-tracker-server/main.py",
    #     ]
    # },

    "expense-tracker-cloud-server": {
        "transport": "streamable_http",
        "url": "https://gtr-mcp-expense.fastmcp.app/mcp",
        "headers": {
            "Authorization": f"Bearer {os.getenv('FASTMCP_API_KEY')}"
        }
    },

    "my-mcp-server-2dedc350": {
			"transport": "stdio",
			"command": "/home/md-al-amin/.local/bin/uv",
			"args": [
				"run",
				"/home/md-al-amin/My-Projects/End-to-End-Agentic-Ai-Automation-Lab/11.5-Advanced-MCP-ownMCPs/00-Locla-mcp-Server/00-basics-server/main.py"
			]
		}
}

async def main():
    
    client = MultiServerMCPClient(SERVERS)
    tools = await client.get_tools()


    named_tools = {}
    for tool in tools:
        named_tools[tool.name] = tool

    print("Available tools:", named_tools.keys())

    llm = ChatOpenAI(model="gpt-5")
    llm_with_tools = llm.bind_tools(tools)

    prompt = "can you add an expense of 100 dollars for food category with description 'lunch' and date '2024-10-01'?"
    response = await llm_with_tools.ainvoke(prompt)

    if not getattr(response, "tool_calls", None):
        print("\nLLM Reply:", response.content)
        return

    tool_messages = []
    for tc in response.tool_calls:
        selected_tool = tc["name"]
        selected_tool_args = tc.get("args") or {}
        selected_tool_id = tc["id"]

        result = await named_tools[selected_tool].ainvoke(selected_tool_args)
        tool_messages.append(ToolMessage(tool_call_id=selected_tool_id, content=json.dumps(result)))
        

    final_response = await llm_with_tools.ainvoke([prompt, response, *tool_messages])
    print(f"Final response: {final_response.content}")


if __name__ == '__main__':
    asyncio.run(main())