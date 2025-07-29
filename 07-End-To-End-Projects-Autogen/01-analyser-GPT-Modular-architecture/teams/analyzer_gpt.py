from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from agents.code_executor_agent import getCodeExecutorAgent
from agents.data_analyser_agent import getDataAnalyzerAgent


def getDataAnalyzerTeam(docker, model_clint):
    code_executor_agent = getCodeExecutorAgent(docker)
    data_analyzer_agent = getDataAnalyzerAgent(model_clint)
    
    text_mention_termination = TextMentionTermination("STOP")
    
    team = RoundRobinGroupChat(
        participants=[code_executor_agent, data_analyzer_agent],
        max_turns=10,
        termination_condition = text_mention_termination
    )
    
    return team