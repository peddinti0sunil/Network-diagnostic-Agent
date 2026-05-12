from typing import TypedDict, Annotated
import operator
from langchain_groq import ChatGroq
from langchain_core.messages import AnyMessage
from tools import ALL_TOOLS

from langgraph.graph import StateGraph,END,START
from langgraph.prebuilt import ToolNode,tools_condition
# from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver
# import sqlite3

from pydantic import BaseModel
from typing import List

from langchain_core.messages import (HumanMessage, SystemMessage,AIMessage)
import os
from dotenv import load_dotenv
# import uuid
import socket

load_dotenv()
llm=ChatGroq(
    api_key=os.getenv("GROQ_API"),
    model="llama-3.3-70b-versatile",
    temperature=0)

LLM=llm.bind_tools(ALL_TOOLS)

class AgentState(TypedDict):
    messages:Annotated[list[AnyMessage],operator.add]

class DiagnosticReport(BaseModel):
    target: str
    healthy: List[str]
    warnings: List[str]
    critical: List[str]
    recommendation: str

def format_report(report: DiagnosticReport) -> str:

    healthy_section = "\n".join(
        f"  • {item}"
        for item in report.healthy
    ) or "  None"

    warning_section = "\n".join(
        f"  • {item}"
        for item in report.warnings
    ) or "  None"

    critical_section = "\n".join(
        f"  • {item}"
        for item in report.critical
    ) or "  None"

    return (
        f"=== NETWORK DIAGNOSTIC REPORT ===\n\n"

        f"Target: {report.target}\n\n"

        f"🟢 HEALTHY\n"
        f"{healthy_section}\n\n"

        f"🟡 WARNINGS\n"
        f"{warning_section}\n\n"

        f"🔴 CRITICAL\n"
        f"{critical_section}\n\n"

        f"RECOMMENDATION\n"
        f"{report.recommendation}\n"
    )


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

def report_node(state):
    structured_llm=llm.with_structured_output(DiagnosticReport)
    system= SystemMessage(
        content=(
            "Based on the following conversation and tool results, "
            "generate a diagnostic report summarizing the network issue, "
            "categorizing findings into healthy, warning, and critical sections, "
            "and providing a recommendation for next steps."
        )
    )
    report =structured_llm.invoke(
        [system]+state['messages']
    )
    formatted_report=format_report(report)
    return {'messages':[AIMessage(content=formatted_report)]}

# conn=sqlite3.connect("agent_memory.db",check_same_thread=False)
# memory =SqliteSaver(conn)

memory =MemorySaver()

graph=StateGraph(AgentState)
graph.add_node("llm",llm_node)
graph.add_node("tools",ToolNode(ALL_TOOLS))
graph.add_node("report",report_node)

graph.set_entry_point("llm")

graph.add_conditional_edges(
    "llm",
    tools_condition,
    {"tools":"tools",END:"report"}
)

graph.add_edge("tools","llm")
graph.add_edge("report",END)

agent=graph.compile(
    checkpointer=memory
)


if __name__ == "__main__":
    thread_id=socket.gethostname()

    config={
        "configurable":{
            "thread_id":thread_id
        }

    }
    while True:
        query=input("Enter your network diagnostic issue query or type [exit] to exit: ")
        if query.lower() == "exit":
            break
        if not query:
            continue
        result = agent.invoke({
            "messages": [HumanMessage(content=query)]
        }
        ,config=config)
        
        print(result["messages"][-1].content)
        