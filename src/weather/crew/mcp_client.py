import json
import subprocess
from weather.api.errors import ProviderError
from weather.mcp_weather.cache import weather_cache
from weather.api._logging import LogDuration, logging, logger



def send_message(proc, message):
    proc.stdin.write(json.dumps(message) + "\n")
    proc.stdin.flush()
    x = proc.stdout.readline()
    return json.loads(x)

def mcp_client(params: dict):
    # Launch the MCP server as a subprocess
    ServerProcess = subprocess.Popen(
        ["python3", "src/weather/mcp_weather/server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    key = f"{params['location']}:{params['start_date']}:{params['end_date']}:{params['units']}"
    res = None
    if days := weather_cache.get(key):
        logger.log(logging.INFO, f"...found cache for {key}, not calling mcp")
        res =  {
			"daily": days,
			"source": "cached - open-meteo"
		}
    else:
          if not "fetch_weather" in send_message(ServerProcess, {
              "jsonrpc": "2.0",
              "id": 1,
              "method": "tools"
              })['result'] :
              raise ProviderError("MCP server does not support fetch_weather tool")
          with LogDuration("calling mcp", 2):
            res = send_message(ServerProcess, {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "fetch_weather",
                "params": params
                })
          if error := res.get("error"):
              raise ProviderError(f"MCP error: {error}")
          weather_cache.set(key, res["result"]["daily"])
        
    ServerProcess.terminate()
    return res, "fetch_weather"

if __name__ == "__main__":
    mcp_client({"location": "40.7128,-74.0060", "start_date": "2024-01-01", "end_date": "2024-01-07", "units": "metric"})