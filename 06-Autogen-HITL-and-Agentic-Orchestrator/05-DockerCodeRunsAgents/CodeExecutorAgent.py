from autogen_agentchat.agents import CodeExecutorAgent
import asyncio
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

async def main():
    
    docker = DockerCommandLineCodeExecutor(
        work_dir="/temp",
        timeout=120
    )
    
    code_executor_agent = CodeExecutorAgent(
        name="CodeExecutorAgent",
        code_executor=docker
    )
    
    task = TextMessage(
        content="""Hare is the code to execution.
```python
print("test line.")
```

""",
    source="user"
    )
    
    await docker.start()
    
    result = await code_executor_agent.on_messages(
        messages = [task],
        cancellation_token = CancellationToken()
    )
    
    print("Hare is output of the code: ", result)
    
    await docker.stop()
    
if (__name__ == "__main__"):
    asyncio.run(main())