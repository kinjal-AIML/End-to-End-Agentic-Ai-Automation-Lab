from autogen_ext.models.ollama import OllamaChatCompletionClient
from config.constants import OLLAMA_MODEL

def get_ollama_model_clint():
    ollama_model_clint = OllamaChatCompletionClient(
        model=OLLAMA_MODEL
    )
    
    return ollama_model_clint