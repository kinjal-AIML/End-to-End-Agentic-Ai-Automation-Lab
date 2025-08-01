import streamlit as st
import asyncio
import os
from teams.analyzer_gpt import getDataAnalyzerTeam
from config.docker_util import start_docker_container, stop_docker_container, getDockerCommandLineExecutor
from model.ollama_model_clint import get_ollama_model_clint
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import TaskResult






st.title("Analyzer GPT-Digital Data Analyzer")
st.sidebar.title("Settings")
st.sidebar.selectbox("Select The Model",["Ollama","GroQ","Openai"])



## TODO: Chat input

upload_file = st.file_uploader("",type=["csv"])

task = st.chat_input("Enter your task hare....")

  
    
## TODO: Team building and Agent call

async def run_analyzer_gpt(docker, ollama_model_client, task):
    try:
        await start_docker_container(docker)
        team = getDataAnalyzerTeam(docker, ollama_model_client)
        
        async for messages in team.run_stream(task=task):
            if isinstance(messages, TextMessage):
                st.markdown(f"--: {messages.content}")
            elif isinstance(messages, TaskResult):
                st.markdown(messages.stop_reason)
        
        return None
    
    except Exception as e:
        st.error(f"Error is: {e}")
        return e
    
    finally:
        await stop_docker_container(docker)



if task:
    if upload_file is not None:
        
        if not os.path.exists("/temp"):
            os.makedirs("temp", exist_ok=True)
        
        with open("temp/data.csv", "wb") as f:
            f.write(upload_file.getbuffer())
            
        ollama_model_client = get_ollama_model_clint()    
        docker = getDockerCommandLineExecutor()
        
        error = asyncio.run(run_analyzer_gpt(docker, ollama_model_client, task))
        
        if error:
            st.error(f"An error occurred: {error}")
    else:
        st.error("Please uploaded the file and provide the task.")

else:
    st.error("Please Provide the Task.")