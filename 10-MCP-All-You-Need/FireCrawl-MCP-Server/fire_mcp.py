import asyncio
import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama

# Load environment variables from a .env file
load_dotenv()

async def main():
    
    
    serper_api_key = os.getenv("SERPER_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")

    if not all([serper_api_key, groq_api_key, firecrawl_api_key]):
        print("Please ensure SERPER_API_KEY, GROQ_API_KEY, and FIRECRAWL_API_KEY are set in your .env file.")
        return

    # --- Step 2: Configure the MultiServerMCPClient ---
    client = MultiServerMCPClient(
        {
           
            "firecrawl": {
                "command": "npx",              
                "args": ["-y", "firecrawl-mcp"], 
                "env": {
                    "FIRECRAWL_API_KEY": firecrawl_api_key 
                },
                "transport": "stdio"          
            }
            
        }
    )

    # --- Step 3: Get Tools, Create Model and Agent ---
    print("Fetching tools from all MCP servers...")
    tools = await client.get_tools()
    print("\n--- Available Tools ---")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
    print("-----------------------\n")
    
    # model = ChatGroq(model=os.getenv("OPENAI_MODEL"))
    model = ChatOllama(model="qwen3:14b") # this is my local model.
    agent_executor = create_react_agent(model, tools)

    
    prompt_scrape = """
    Extract business lead information from the website at the provided URL.
        Return the result as structured below format with the following fields:

        output format: 
        "business_name": "",
        "address": "",
        "phone": "",
        "email": "",
        "website": "",
        "social_links": []
        

If any field is not found, return it as an empty string or empty list.
if can not fine phone number or other info then go to about page there will be contain phone number and full info.
first look at the home if not get the info then find about page hopefully you will get the data.
URL to process: http://www.bengalexpressbd.com

the output is:
    output format: 
        "business_name": "",
        "address": "",
        "phone": "",
        "email": "",
        "website": "",
        "social_links": []


"""
    print(f"--- User Query: {prompt_scrape} ---")
    
    scrape_response = await agent_executor.ainvoke(
        {"messages": [{"role": "user", "content": prompt_scrape}]}
    )
    print("\n--- Agent Response ---")
    print(scrape_response['messages'][-1].content)
    print("------------------------\n")

    

if __name__ == "__main__":
    asyncio.run(main())