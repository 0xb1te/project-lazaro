import os
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.retrievers.multi_query import MultiQueryRetriever
from get_vector_db import get_vector_db

LLM_MODEL = os.getenv('LLM_MODEL')

# Function to get the prompt templates for generating alternative questions and answering based on context
def get_prompt():
    QUERY_PROMPT = PromptTemplate(
        input_variables=["question"],
        template="""You are an AI programmer assistant. Your task is to generate five
        different versions of the given user question to retrieve relevant documents from
        a vector database which holds a Codebase. By generating multiple perspectives on the user question, your
        goal is to help the user overcome some of the limitations of the distance-based
        similarity search. Provide these alternative questions separated by newlines.
        Original question: {question}""",
    )

    template = """Answer the question based ONLY on the following context:
    {context}
    Question: {question}
    """

    prompt = ChatPromptTemplate.from_template(template)

    return QUERY_PROMPT, prompt

# Main function to handle the query process
def query(input):
    if input:
        llm = ChatOllama(model=LLM_MODEL)
        db = get_qdrant_db()
        
        # Encode the question using your model
        question_embedding = llm.encode(input).tolist()
        
        # Search for similar documents in Qdrant
        hits = db.search(
            collection_name="code_vectors",
            query_vector=question_embedding,
            limit=5
        )
        
        # Extract relevant contexts from search results
        contexts = []
        for hit in hits:
            contexts.append(hit.payload["text"])
            
        # Generate prompt with all contexts
        prompt_template = ChatPromptTemplate.from_template("""
            Answer the question based ONLY on the following context:
            {context}
            Question: {question}
        """)
        
        # Combine contexts and execute the query
        final_context = "\n\n".join(contexts)
        response = llm(prompt_template.format(context=final_context, question=input))
        
        return response