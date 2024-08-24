import os

from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
UPSTASH_VECTOR_URL = os.environ.get('UPSTASH_VECTOR_URL')
UPSTASH_VECTOR_TOKEN = os.environ.get('UPSTASH_VECTOR_TOKEN')

from langchain_community.vectorstores import UpstashVectorStore
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
store = UpstashVectorStore(
    embedding=embeddings,
    index_url=UPSTASH_VECTOR_URL,
    index_token=UPSTASH_VECTOR_TOKEN,
)
retriever = store.as_retriever(
    search_type='similarity',
    search_kwargs={"k":2}
)
retriever.invoke("Which city is known as city of temples")
from langchain_openai import ChatOpenAI, OpenAI

LLM_CONFIG = {
    "model": "gpt-4o-min",
    "api_key": OPENAI_API_KEY,
}
llm = ChatOpenAI(**LLM_CONFIG)
from langchain_core.prompts import ChatPromptTemplate

message = """
Answer this question
{question}
Context: {context}
"""

prompt = ChatPromptTemplate.from_messages([("human", message)])
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

runnable = RunnableParallel(
    passed = RunnablePassthrough(),
    modified = lambda x: x["num"] + 1,
)
runnable.invoke({"num": 1})
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()

def get_chain():
    chain = {"context": retriever, "question": RunnablePassthrough()} | prompt | llm | parser
    chain.invoke("Where is the best place to eat")
    return chain