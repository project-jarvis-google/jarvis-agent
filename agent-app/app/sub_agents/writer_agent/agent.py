from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents import SequentialAgent
from .config import MODEL
from .prompt import WRITER_AGENT_PROMPT
from .writer import save_generated_report_py

writer_agent = LlmAgent(
    name="Cloud_Service_Advisor_AI_Agent",
    model=MODEL,
    description=("Answers user's query about service recommendation."),
    instruction=WRITER_AGENT_PROMPT,
    #after_agent_callback=save_generated_report_py
    tools=[
        save_generated_report_py
    ],
)