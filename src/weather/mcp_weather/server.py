import sys
import json

from weather.mcp_weather.provider import OpenMeteoProvider

def send_response(response):
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

provider = OpenMeteoProvider()
def main():
    
    for line in sys.stdin:
        try:
            request = json.loads(line, strict=False)
            
            method = request.get("method")
            params = request.get("params", {})

            if method == "ping":
                result = {"reply": "pong"}
            if method == "tools":
                result = ["fetch_weather"]
            elif method == "fetch_weather":
                result = provider.fetch(params)

            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
            send_response(response)

        except Exception as e:
            send_response({
                "jsonrpc": "2.0",
                "error": str(e)
            })


if __name__ == "__main__":
    main()