import asyncio
from teams.analyzer_gpt import getDataAnalyzerTeam
from config.docker_util import start_docker_container, stop_docker_container, getDockerCommandLineExecutor
from model.ollama_model_clint import get_ollama_model_clint


async def main():
    ollama_model_clint = get_ollama_model_clint()
    docker = getDockerCommandLineExecutor()
    
    team = getDataAnalyzerTeam(docker, ollama_model_clint)
    
    try:
        task = "can you give me a graph of flower types in my data iris.csv"
        
        await start_docker_container(docker)
        
        async for msg in team.run_stream(task=task):
            print(msg)
        
    except Exception as e:
        print(e)
    finally:
        await stop_docker_container(docker)
        

if __name__ == "__main__":
    asyncio.run(main())
