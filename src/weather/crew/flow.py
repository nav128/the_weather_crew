
import json
from dotenv import load_dotenv

from weather.crew.mcp_client import mcp_client
from weather.crew.tasks import FetchWeatherTask, ParseTask, SummaryTask

# Load environment variables from .env file
load_dotenv()
from crewai import Agent


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
    ParseTask(agent).run(context)
    print("\n\n\n",context, "\n\n\n\n")
    if "error" in context:
        return context
    FetchWeatherTask(agent).run(context)
    context["summary"] = agent.execute_task(SummaryTask(agent), context)
    return context
    
    
    

