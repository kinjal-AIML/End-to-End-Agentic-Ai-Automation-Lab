from autogen_agentchat.agents import AssistantAgent
from prompt.data_analyzer_Smessages import DATA_ANALYZER_SYSTEM_MESSAGES

def getDataAnalyzerAgent(model_clint):
    data_analyzer_agent = AssistantAgent(
        name="Data_Analyzer_Agent",
        description="An agent that solve data analysis problem and gives the code as well.",
        model_client=model_clint,
        system_message=DATA_ANALYZER_SYSTEM_MESSAGES
    )
    
    return data_analyzer_agent