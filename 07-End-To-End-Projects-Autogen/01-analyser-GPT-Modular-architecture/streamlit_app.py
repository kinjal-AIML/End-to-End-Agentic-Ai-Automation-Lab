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

## TODO: Create Streamlit Session state.
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "autogen_team_state" not in st.session_state:
    st.session_state.autogen_team_state = None
    
if ("images_shown") not in st.session_state:
    st.session_state.images_shown = []

task = st.chat_input("Enter your task hare....")

  
    
## TODO: Team building and Agent call

async def run_analyzer_gpt(docker, ollama_model_client, task):
    try:
        await start_docker_container(docker)
        team = getDataAnalyzerTeam(docker, ollama_model_client)
        
        if st.session_state.autogen_team_state is not None:
            await team.load_state(st.session_state.autogen_team_state)
        
        async for messages in team.run_stream(task=task):
            if isinstance(messages, TextMessage):
                if messages.source.startswith("user"):
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(messages.content)
                elif messages.source.startswith("Data_Analyzer_Agent"):
                    with st.chat_message("Data Analyzer", avatar="🤖"):
                        st.markdown(messages.content)
                        
                elif messages.source.startswith("Python_Code_Executor"):
                    with st.chat_message("Code Executor", avatar="🧑‍💻"):
                        st.markdown(messages.content)
            
                st.session_state.messages.append(messages.content)
                        
            elif isinstance(messages, TaskResult):
                st.markdown(f"Stop Reason is : {messages.stop_reason}")
                
                st.session_state.messages.append(messages.stop_reason)
        
        st.session_state.autogen_team_state = await team.save_state()
        return None
    
    except Exception as e:
        st.error(f"Error is: {e}")
        return e
    
    finally:
        await stop_docker_container(docker)


# TODO: Check the Session State Messages.
if st.session_state.messages:
    for msg in st.session_state.messages:
        st.markdown(msg)
        

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
            
        if os.path.exists("temp/output.png"):
            # if("output.png" not in st.session_state.images_shown):
            #     st.session_state.images_shown.append("output.png")
            
            # if "output.png" not in st.session_state.images_shown:
            #     st.session_state.images_shown.append("output.png")
            
            st.image("temp/output.png", caption="Output Image")
    else:
        st.error("Please uploaded the file and provide the task.")

else:
    st.error("Please Provide the Task.")