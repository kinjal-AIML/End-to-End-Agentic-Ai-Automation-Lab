import streamlit as st
st.title("Analyzer GPT-Digital Data Analyzer")
st.sidebar.title("Settings")
st.sidebar.selectbox("Select The Model",["Ollama","GroQ","Openai"])


## Chat input
user_input = st.chat_input("Enter your task hare....")

st.file_uploader("",type=["csv"])