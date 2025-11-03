import json
import os
from dotenv import load_dotenv

from weather.crew.mcp_client import mcp_client

# Load environment variables from .env file
load_dotenv()
from crewai import Agent, Crew, Process, Task
from crewai.tools import BaseTool
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from weather.crew.parser import parse_range
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators
    
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
        res = parse_range(query)
        return res

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
            resp = mcp_client(context.get("params"))            
            context["weather_raw"] = resp
        except Exception as e:
            print("Error during MCP communication:", str(e))
            context["error"] = str(e)

# --- 3. Define the Agent ---
class MyAgent(Agent):
    name: str = "Range Parser Agent"
    def __init__(self):
        super().__init__(
            role="orchestrator agent that parses weather queries, fetches weather data, and summarizes it",
            goal="return a structured weather data",
            backstory="I will be used by the python script to run various tasks.",
            allow_delegation=False,
            verbose=True,
            # tools=[ParseTool()],
        )



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
                ● Format the output as JSON with the structure:
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


context = {
    "query": "Summarize weather in Tel Aviv from last Monday to Friday, fe"
}
agent = MyAgent()

context["params"] = ParseTask(agent).run(context)
# print(context)
context["weather_raw"] =  FetchWeatherTask(agent).run(context)#agent.execute_task()
context["summary"] = agent.execute_task(SummaryTask(agent), context)

