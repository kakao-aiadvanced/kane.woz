# %% [python]
import os
import openai
import dotenv

from tqdm import tqdm
from datasets import load_dataset

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS

from langchain import hub
from langchain.document_loaders import WebBaseLoader
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain.chains.router import MultiPromptChain
from langchain.chains.router.llm_router import LLMRouterChain
from langchain.tools import tool

from langchain_core.runnables import chain
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough

from langsmith.wrappers import wrap_openai
from langsmith import traceable

dotenv.load_dotenv()
# %% [python]
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o-mini")

# %% [python]
# pwd


class UserPipe(BaseModel):
    input: str = Field(description="User input string")


class CheckerPipe(BaseModel):
    input: str = Field(description="User input string")
    relevance: bool = Field(description="Is the input relevant to the prompt")


@chain
def input(input: str) -> UserPipe:
    return UserPipe(input=input)


@chain
def checker(input: UserPipe) -> CheckerPipe:
    parser = JsonOutputParser(pydantic_object=CheckerPipe)
    prompt = PromptTemplate(
        template="""
If the input is relevant to the AI prompt, please return 'relevance' field is True. Otherwise, False.

input: {input}

{format_instructions}
""",
        input_variables=["input"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()},
    )

    return (prompt | llm | parser).invoke(input)


chain = input | checker

# %% [python]
chain.invoke("""
LLM-powered agents differ from typical chatbot applications in that they have complex reasoning skills. Made up of an agent core, memory module, set of tools, and planning module, agents can generate highly personalized answers and content in a variety of enterprise settings—from data curation to advanced e-commerce recommendation systems.

For an overview of the technical ecosystem around agents, such as implementation frameworks, must-read papers, posts, and related topics, see Building Your First Agent Application. The walkthrough of a no-framework implementation of a Q&A agent helps you better talk to your data.

To delve into other types of LLM agents, see Build an LLM-Powered API Agent for Task Execution and Build an LLM-Powered Data Agent for Data Analysis.

""")
