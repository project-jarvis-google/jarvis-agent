from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents import SequentialAgent
from .config import MODEL
from .prompt import AGENT_PROMPT
#from .writer import save_generated_report_py
from google.adk.artifacts import GcsArtifactService #InMemoryArtifactService
from google.adk.tools import FunctionTool
from ...utils.download import download_pdf_from_gcs, save_generated_report_py


infra_scanner_agent = LlmAgent(
    name="infrastructure_scanner_agent",
    model=MODEL,
    description=("Builds a comprehensive picture of the client's infrastructure."),
    instruction=AGENT_PROMPT,    
)