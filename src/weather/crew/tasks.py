from crewai import Task
from weather.crew.mcp_client import mcp_client
from crewai.agents.agent_builder.base_agent import BaseAgent

from weather.crew.parser import parse_range

class ParseTask(Task):
    def __init__(self, agent: BaseAgent):
        super().__init__(
            name = "Parse Range Task",
            description = "Parses a natural language weather query into structured parameters.",
            expected_output = "strict json or error message",
            agent=agent
        )

    def run(self, context):
        query = context.get("query", "")
        context["params"] = parse_range(query)


class FetchWeatherTask(Task):
    # params: dict = None
    def __init__(self, agent: BaseAgent):
        super().__init__(
        name = "Fetch Weather Task",
        description = "Fetches weather data based on structured parameters.",
        expected_output = "weather data in json format",
        agent=agent
        )
        # object.__setattr__(self, 'params', params)  # Use object.__setattr__ for Pydantic models


    def run(self, context: dict):        
        try:
            # Send the parameters as JSON
            resp, tool = mcp_client(context.get("params"))            
            context["weather_raw"] = resp
            context["tool_used"] = tool
        except Exception as e:
            print("Error during MCP communication:", str(e))
            context["error"] = str(e)



class SummaryTask(Task):
    def __init__(self, agent: BaseAgent):
        super().__init__(
        name = "Summary Task",
        description = "Summarizes the weather data into a human-readable format.",
        expected_output = """
                ● 2–3 sentences overview + bullets for highlights.
                ● Mention coldest/hottest day with values & dates.
                ● Call out any day with precip_mm >= 5 (or provider’s “rainy” threshold) and
                    wind_max_kph >= 40.
                ● Provide a confidence score (0 to 1) for the summary accuracy.
                ● Format the output as JSON-like string (not actual json value) with the structure:
                {
                "summary_text":"human-friendly synopsis (150–250 words)",
                "highlights":{
                "pattern":"hot/cool, wet/dry, windy/calm",
                "extremes":{"coldest":{"date":"...","tmin":..},"hottest":{"date":"...","tmax":..}},
                "notable_days":[{"date":"...","note":"heavy rain"}, {"date":"...","note":"strong winds"}]
                },
                "confidence": float between 0 and 1
                }
                Style: concise, factual, no hallucinated units; mention notable days.
        """,
        agent=agent
        )

