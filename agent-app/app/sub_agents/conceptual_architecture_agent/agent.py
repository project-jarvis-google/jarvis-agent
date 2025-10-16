from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_google_vertexai import ChatVertexAI

# Step 1: Import your new tool alongside the existing one
from app.sub_agents.google_search_dummy_agent.tools import google_search
from app.sub_agents.conceptual_architecture_agent.tools import (
    analyze_architecture_document,
)


# --- Agent Definition ---
def create_root_agent():
    """Creates the main coordinating agent (root_agent)."""

    # Step 2: Add the new tool to the list of tools the agent can use
    tools = [
        google_search,
        analyze_architecture_document,
    ]

    prompt = hub.pull("hwchase17/react")

    llm = ChatVertexAI(model_name="gemini-pro", temperature=0)

    agent = create_react_agent(llm, tools, prompt)

    return AgentExecutor(agent=agent, tools=tools, verbose=True)


root_agent = create_root_agent()
