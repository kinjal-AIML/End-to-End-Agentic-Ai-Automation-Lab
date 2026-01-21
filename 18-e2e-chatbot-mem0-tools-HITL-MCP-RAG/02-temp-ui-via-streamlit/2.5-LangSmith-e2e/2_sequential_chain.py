from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
load_dotenv()

os.environ["LANGCHAIN_PROJECT"]="Sequential Projects"

prompt1 = PromptTemplate(
    template='Generate a detailed report on {topic}',
    input_variables=['topic']
)

prompt2 = PromptTemplate(
    template='Generate a 5 pointer summary from the following text \n {text}',
    input_variables=['text']
)

model = ChatOpenAI(model="gpt-4o-mini")

parser = StrOutputParser()

chain = prompt1 | model | parser | prompt2 | model | parser

config = {
    'tags': ["llm apps", "report gen"],
    "metadata": {"model": "gpt-4o-mini"}
}

result = chain.invoke({'topic': 'Unemployment in Bangladesh.'}, config=config)

print(result)