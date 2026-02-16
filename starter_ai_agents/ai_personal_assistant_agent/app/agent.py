from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from langgraph.prebuilt import create_react_agent

SYSTEM_PROMPT = (
    "You are a practical AI personal assistant. "
    "Be concise, friendly, and action-oriented. "
    "Use tools whenever task/note memory is relevant. "
    "If you have web search: use it for lists, facts, companies, news, or anything outside your memory. "
    "Formulate clear, specific search queries (e.g. 'list of X in Y'); if results are poor, try alternative phrasings. "
    "If dates are needed, request YYYY-MM-DD format. "
    "If asked to do something you cannot do with your tools, say what you can do instead."
)

CONTROLLER_PROMPT = (
    "You are the controller agent for a personal assistant. You coordinate capability agents. "
    "When a capability agent cannot do something (or you have no tool for it): "
    "1) Use web_search to find how to implement it (e.g. 'python how to fetch emails', 'python read database'). "
    "2) Use add_capability to add a new capability: generate complete Python code for a capability module that "
    "defines _get_tools(**kwargs) with @tool functions and calls register_capability. "
    "3) After adding, tell the user to ask again. "
    "Be concise. Use tools for tasks/notes when relevant. Formulate clear search queries."
)


def build_agent_executor(llm, tools, controller_mode: bool = False):
    prompt = CONTROLLER_PROMPT if controller_mode else SYSTEM_PROMPT
    return create_react_agent(llm, tools, prompt=prompt)


def _evolution_triggered(messages: list) -> bool:
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                if getattr(tc, "name", "") == "add_capability":
                    return True
    return False


def run_chat_loop(agent, rebuild_agent_fn=None) -> None:
    print("Personal Assistant ready. Type 'exit' to quit.\n")
    chat_history: list[BaseMessage] = []

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Assistant: Bye!")
            return
        if not user_input:
            continue

        messages = chat_history + [HumanMessage(content=user_input)]
        result = agent.invoke({"messages": messages})
        out_messages = result["messages"]
        output = ""
        for m in reversed(out_messages):
            if isinstance(m, AIMessage) and m.content:
                output = m.content
                break
        if not output:
            output = str(out_messages[-1]) if out_messages else "No response."
        print(f"Assistant: {output}\n")
        chat_history = list(out_messages)

        if rebuild_agent_fn and _evolution_triggered(out_messages):
            print("[Controller] New capability added. Rebuilding agent...\n")
            agent = rebuild_agent_fn()
