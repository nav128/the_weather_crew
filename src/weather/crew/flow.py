import io
import sys
import json

from crewai import Agent
from weather.crew.mcp_client import mcp_client
from weather.crew.tasks import FetchWeatherTask, ParseTask, SummaryTask
from weather.api._logging import LogDuration, logging, logger

class CapturePrints:
    def __init__(self):
        self.fake_file = io.StringIO()
    def __enter__(self):
        sys.stdout = self.fake_file 
    def __exit__(self, *args, **kwargs):
        sys.stdout = sys.__stdout__


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


def run_weather_pipeline(query: dict) -> dict:
    context = query.copy()
    agent = MyAgent()
    
    logger.log(logging.DEBUG, "...runing parse")
    with LogDuration("Parse Task", 1):
        ParseTask(agent).run(context)

    logger.log(logging.DEBUG, "...runing fetch weather")
    with LogDuration("Fetcher Task",1):
        FetchWeatherTask(agent).run(context)

    logger.log(logging.DEBUG, "...runing summary")
    with LogDuration("Summary Task", 1):
        with CapturePrints():
            summary_raw: str = agent.execute_task(SummaryTask(agent), context)
        try:
            context["summary"] = json.loads(summary_raw)
        except Exception as e:
            if summary_raw.startswith("```json") and summary_raw.endswith("```"):
                try:
                    context["summary"] = json.loads(summary_raw[7:-3])
                except:
                    raise 
            
    return context
    
    
    

