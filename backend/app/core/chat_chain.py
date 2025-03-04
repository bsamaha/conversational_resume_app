# NOTE: This chat chain is implemented synchronously using chat_model.invoke. If heavy concurrency is expected, consider implementing an async version using chat_model.ainvoke.

from langgraph.checkpoint.memory import MemorySaver  # type: ignore
from langgraph.graph import StateGraph, START  # type: ignore
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.core.llm import get_chat_model
from app.core.vector_db import get_relevant_context
from langgraph.graph import StateGraph
from typing import TypedDict, Type, Annotated, List
from langchain_core.runnables.config import RunnableConfig
import asyncio

# Initialize the language model from our existing configuration
chat_model = get_chat_model()

# Define a prompt template that takes a conversation, context, and language parameter
prompt_template = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant answering questions about Blake's resume. You are to take on the persona of Blake and answer questions as if you are him.
    Use the following context from the resume to answer questions. If you don't find 
    relevant information in the context, say so.
    
    Context: {context}
    
    Answer all questions to the best of your ability in {language}."""),
    MessagesPlaceholder(variable_name="messages")
])

class ChatState(TypedDict):
    messages: List[str]
    language: str
    context: str

state_schema: Type[ChatState] = ChatState

async def get_context(query: str) -> str:
    """Retrieve relevant context from the vector database."""
    try:
        context = await get_relevant_context(query)
        return context
    except Exception as e:
        print(f"Error retrieving context: {e}")
        return "No relevant context found."

# Node function that retrieves context and calls the language model
def call_model(state: dict):
    # Get the user's query (last message)
    query = state["messages"][-1]
    
    # Retrieve context synchronously (we're in a sync function)
    context = asyncio.run(get_context(query))
    
    # Build the prompt using the conversation history, context, and language
    prompt = prompt_template.invoke({
        "messages": state["messages"],
        "context": context,
        "language": state["language"]
    })
    
    # Call the language model synchronously
    response = chat_model.invoke(prompt)
    
    # Append the AI response to the conversation history
    new_messages = state["messages"] + [response]
    return {
        "messages": new_messages,
        "language": state["language"],
        "context": context
    }

# Build the state graph
workflow = StateGraph(state_schema=state_schema)
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

# Initialize a memory checkpointer
memory = MemorySaver()

# Compile the workflow into a callable application
chat_app = workflow.compile(checkpointer=memory)

# Helper function to invoke the conversation chain. 
# It starts a new conversation with the human query and specified language, using the provided thread_id for persistence.

def chat_invoke(query: str, language: str, thread_id: str) -> str:
    # The initial state has the human's query as the first message
    state_input = {
        "messages": [query],
        "language": language,
        "context": ""  # Initial empty context
    }
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    result = chat_app.invoke(state_input, config)
    # Return the AI's response (the last message in the conversation history)
    return result["messages"][-1] 