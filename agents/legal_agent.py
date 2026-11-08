
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import MessagesState
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.messages import HumanMessage, AIMessage

from core.legal_response import answer_legal_question


# ==========================================
# 1. LANGGRAPH STATE
# ==========================================

class LegalAgentState(MessagesState):
    sources: list
    retrieved_count: int
    is_emergency: bool


# ==========================================
# 2. LEGAL RESPONSE NODE
# ==========================================

def legal_response_node(state: LegalAgentState):

    messages = state["messages"]

    # Get latest user question
    latest_message = messages[-1]
    question = latest_message.content

    # Convert previous messages into chat history
    history = []

    for message in messages[:-1][-6:]:

        if isinstance(message, HumanMessage):
            history.append({
                "role": "user",
                "content": message.content
            })

        elif isinstance(message, AIMessage):
            history.append({
                "role": "assistant",
                "content": message.content
            })

    # Call RAG + Cloudflare LLM + Emergency Detector
    result = answer_legal_question(
        question=question,
        chat_history=history,
        original_question=question
    )

    # Return answer and metadata
    return {
        "messages": [
            AIMessage(content=result["answer"])
        ],
        "sources": result.get("sources", []),
        "retrieved_count": result.get("retrieved_count", 0),
        "is_emergency": result.get("is_emergency", False)
    }


# ==========================================
# 3. BUILD LANGGRAPH WORKFLOW
# ==========================================

workflow = StateGraph(LegalAgentState)

workflow.add_node(
    "legal_response",
    legal_response_node
)

workflow.add_edge(START, "legal_response")
workflow.add_edge("legal_response", END)


# ==========================================
# 4. CONVERSATIONAL MEMORY
# ==========================================

memory = MemorySaver()

legal_agent = workflow.compile(
    checkpointer=memory
)


# ==========================================
# 5. CHAT FUNCTION
# ==========================================

def chat_with_legal_agent(
    question: str,
    thread_id: str
):

    result = legal_agent.invoke(
        {
            "messages": [
                HumanMessage(content=question)
            ]
        },
        config={
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    return {
        "answer": result["messages"][-1].content,
        "sources": result.get("sources", []),
        "retrieved_count": result.get("retrieved_count", 0),
        "is_emergency": result.get("is_emergency", False)
    }
