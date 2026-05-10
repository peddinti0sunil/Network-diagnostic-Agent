from typing import TypedDict, Annotated
import operator
from langchain_groq import ChatGroq
from langchain_core.messages import AnyMessage
from tools import ALL_TOOLS

from langgraph.graph import StateGraph,END,START
from langgraph.prebuilt import ToolNode,tools_condition

from langchain_core.messages import (HumanMessage, SystemMessage)
import os
from dotenv import load_dotenv
load_dotenv()
llm=ChatGroq(
    api_key=os.getenv("GROQ_API"),
    model="llama-3.3-70b-versatile",
    temperature=0)

LLM=llm.bind_tools(ALL_TOOLS)

class AgentState(TypedDict):
    messages:Annotated[list[AnyMessage],operator.add]

def llm_node(state: AgentState):
    system= SystemMessage(
        content=(
            "You are a network diagnostic assistant that helps users "
            "troubleshoot websites, servers, and network connectivity problems.\n\n"

            "You have access to tools for:\n"
            "- checking website health and HTTP responses\n"
            "- pinging hosts to test reachability\n"
            "- scanning common network ports\n"
            "- performing DNS lookups\n\n"

            "Use tools whenever network verification is needed instead of guessing.\n\n"

            "When responding:\n"
            "- clearly explain what you checked\n"
            "- summarize the results in simple language\n"
            "- identify possible causes of failures\n"
            "- suggest next troubleshooting steps when appropriate\n\n"

            "Be concise, technical, and accurate."
        )
    )
    response=LLM.invoke(
        [system]+state['messages']
        )
    return {'messages':[response]}


graph=StateGraph(AgentState)
graph.add_node("llm",llm_node)
graph.add_node("tools",ToolNode(ALL_TOOLS))

graph.set_entry_point("llm")

graph.add_conditional_edges(
    "llm",
    tools_condition
)

graph.add_edge("tools","llm")

agent=graph.compile()


if __name__ == "__main__":
    
    query=input("Enter your network diagnostic issue query: ")
    result = agent.invoke({
        "messages": [HumanMessage(content=query)]
    })
    
    print(result["messages"][-1].content)