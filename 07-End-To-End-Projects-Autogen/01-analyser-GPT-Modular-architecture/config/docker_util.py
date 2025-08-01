from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from .constants import WORK_DIR_DOCKER, TIMEOUT_DOCKER


def getDockerCommandLineExecutor():
    docker = DockerCommandLineCodeExecutor(
        image="amancevice/pandas",
        work_dir=WORK_DIR_DOCKER,
        timeout=TIMEOUT_DOCKER
    )
    
    return docker

async def start_docker_container(docker):
    print("---Docker is Starting---")
    await docker.start()
    print("---Docker is Started---")
    
async def stop_docker_container(docker):
    print("---Stopping Docker---")
    await docker.stop()
    print("---Docker has Stopped---")