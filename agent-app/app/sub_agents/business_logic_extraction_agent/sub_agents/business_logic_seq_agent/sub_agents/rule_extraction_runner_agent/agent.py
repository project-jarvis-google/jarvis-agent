
from google.adk.agents import Agent
from google.adk.tools import ToolContext

from ..parallel_codebase_analyzer_agent.sub_agents.rule_extraction_agent import rule_extraction_agent

class RuleExtractionRunnerAgent(Agent):
    def __init__(self):
        super().__init__(
            name="rule_extraction_runner_agent",
            description="Runs the rule_extraction_agent on all keyword hotspots.",
        )

    async def run(self, tool_context: ToolContext) -> None:
        keyword_hotspots = tool_context.state.get("keyword_hotspots", {})
        business_rules = []

        for file_path, hotspots in keyword_hotspots.items():
            for hotspot in hotspots:
                code_snippet = hotspot["code"]
                line_number = hotspot["line"]

                tool_context.state["code_snippet"] = code_snippet
                tool_context.state["file_path"] = file_path
                tool_context.state["line_number"] = line_number

                # Run the rule_extraction_agent
                async for event in rule_extraction_agent.run_async(tool_context):
                    if event.is_agent_output():
                        business_rules.append({
                            "file_path": file_path,
                            "rules": event.output.final_answer,
                        })

        tool_context.state["business_rules"] = business_rules

rule_extraction_runner_agent = RuleExtractionRunnerAgent()
