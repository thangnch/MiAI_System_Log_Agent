import os
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import time
from datetime import datetime
from logAgent import LogAgent
from agentState import AgentState
from kbAgent import KBAgent
from resolveAgent import ResolveAgent
from dotenv import load_dotenv

# --- 1. LOAD API_KEY FROM .ENV FILE
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# --- 2. CONFIG LOG FILE
log_file = "/Users/thangnch/PycharmProjects/vinuni_agenticai/logs/syslog_clock"

# --- 3. INIT LLM
llm = ChatOpenAI(model="gpt-4.1", temperature=0, api_key=api_key)

# --- 4. INIT AGENTS
log_agent = LogAgent(llm=llm, log_file=log_file)
kb_agent = KBAgent(llm=llm)
resolve_agent = ResolveAgent(llm=llm)


# --- 5. DEFINE NODES (AGENTS) ---

def log_agent_node(state: AgentState):
    return log_agent.run(state)


def kb_agent_node(state: AgentState):
    return kb_agent.run(state)


def resolve_agent_node(state: AgentState):
    return resolve_agent.run(state)


# --- 6. DEFINE GRAPH LOGIC ---

def route_after_analyze_log(state: AgentState):
    if state["error_found"]:
        # Nếu đã fix rồi mà vẫn báo lỗi -> Quay lại tìm KB tiếp hoặc thoát nếu quá số lần thử
        if state.get("is_fixed") and state["iteration"] > 3:
            print("‼️!!! Error persists after multiple attempts. Manual intervention required.")
            return END
        return "kb_lookup"
    else:
        print("✅--- System is healthy. ---")
        return END


def route_after_kb_lookup(state: AgentState):
    if state["kb_solution"] != "FAIL":
        return "execute_fix"
    else:
        print("❌️--- Manual intervention required. ---")
        return END


# --- 4. BUILD THE GRAPH ---

def build_graph(
        _log_agent_node,
        _kb_agent_node,
        _resolve_agent_node,
        _route_after_analyze_log,
        _route_after_kb_lookup,
        enable_loop: bool = False
):
    """
    Build và compile LangGraph workflow

    :param _log_agent_node: function / callable cho analyze_log
    :param _kb_agent_node: function / callable cho kb_lookup
    :param _resolve_agent_node: function / callable cho execute_fix
    :param _route_after_analyze_log: router function sau bước analyze_log
    :param _route_after_kb_lookup: router function sau bước kb_lookup
    :param enable_loop: bật vòng lặp self-healing
    :return: compiled graph (app)
    """

    workflow = StateGraph(AgentState)

    # --- Nodes ---
    workflow.add_node("analyze_log", _log_agent_node)
    workflow.add_node("kb_lookup", _kb_agent_node)
    workflow.add_node("execute_fix", _resolve_agent_node)

    # --- Entry ---
    workflow.set_entry_point("analyze_log")

    # --- Routing ---
    workflow.add_conditional_edges(
        "analyze_log",
        _route_after_analyze_log,
        {
            "kb_lookup": "kb_lookup",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "kb_lookup",
        _route_after_kb_lookup,
        {
            "execute_fix": "execute_fix",
            END: END
        }
    )

    # --- Optional Loop (self-healing) ---
    if enable_loop:
        workflow.add_edge("execute_fix", "analyze_log")

    # --- Compile ---
    app = workflow.compile()

    return app


# --- MAIN APP ENTRY
if __name__ == "__main__":

    app = build_graph(
        log_agent_node,
        kb_agent_node,
        resolve_agent_node, route_after_analyze_log,
        route_after_kb_lookup,
        enable_loop=False)

    mermaid = app.get_graph().draw_mermaid()
    print(mermaid)  # https://mermaid.live/

    print("🤖Starting Agentic AI System Monitoring (every 5 minutes)...")

    while True:
        print(f"\n⏰ Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        initial_state = {
            "logs": "",
            "error_found": False,
            "kb_solution": "",
            "iteration": 0,
            "is_fixed": False
        }

        try:
            app.invoke(initial_state)
        except Exception as e:
            print(f"❌ Error during execution: {e}")

        # Sleep 5 phút (300 giây)
        print("😴 Sleeping for 5 seconds...\n")
        time.sleep(30)
