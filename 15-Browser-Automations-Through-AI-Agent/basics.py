# from browser_use import Agent, Browser, ChatOllama
import asyncio
import os

async def main():
    browser = Browser(
        executable_path="/usr/bin/google-chrome",  # verify with 'which google-chrome'
        user_data_dir=os.path.expanduser("~/.config/google-chrome"),
        profile_directory="Default",
        headless=False,
        args=[
            "--remote-debugging-port=9222",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check"
        ],
    )

    llm = ChatOllama(model="qwen2.5:14b")  # Or any model available

    task = """
    1. Go to linkedin.com and search for "Google company employees"
    2. Click on the 'People' tab
    3. Scroll 5 times to load more
    4. Extract:
       - full_name
       - job_title
       - profile_url
    5. Save as 'google_employees.csv'
    """

    agent = Agent(task=task, browser=browser, llm=llm)
    await agent.run()

asyncio.run(main())
