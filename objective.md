Assignment — “WeatherSense: MCP +
CrewAI (Multi-Task) + API + Cloud Run”
Objective
Build an end-to-end system that:
1. Accepts a natural-language query about weather over a date range via HTTP.
2. Uses Agent/Task A to convert that text into a strict JSON spec.
3. Uses Agent/Task B to call a Python MCP server tool (weather.get_range) with that
JSON and attach results to context.
4. Uses Agent/Task C to summarize the weather results into clear natural language.
5. Returns both the summary and the structured data.
6. Deploys the API to Google Cloud Run.
Components to Build
1) MCP Server (Python, stdio)
Tool: weather.get_range
Input JSON Schema:
{
"type": "object",
"properties": {
"location": {"type":"string", "description":"City or 'lat,lon'"},
"start_date": {"type":"string","format":"date"},
"end_date": {"type":"string","format":"date"},
"units": {"type":"string","enum":["metric","imperial"],"default":"metric"}
},
"required": ["location","start_date","end_date"]
}
Behavior:
● Resolve location (name or lat,lon) → coordinates.
● Query a free provider (e.g., Open-Meteo) for daily: tmin, tmax, precip_mm,
wind_max_kph, code.
● Validate (end_date >= start_date, span ≤ 31 days); partial future data allowed.
● Return:
{
"location":"Tel Aviv, IL",
"latitude":32.08,
"longitude":34.78,
"units":"metric",
"start_date":"2025-10-01",
"end_date":"2025-10-07",
"daily":[
{"date":"2025-10-01","tmin":22.1,"tmax":29.3,"precip_mm":0.0,"wind_max_kph":31.2,"code":1
}
],
"source":"open-meteo"
}
● Add a 10-minute in-memory cache keyed by (lat,lon,start,end,units).
2) CrewAI Flow (3 Tasks, shared context)
Create one crew with three agents (or one agent with three tasks—either is fine as long as
tasks are distinct and sequential). The key is separate responsibilities and context
passing.
Task A — Parse NL Query → JSON Params
Agent A: “Range Parser”
Input: { query: string } (e.g., “weather in Tel Aviv from last Monday to Friday, metric”)
Output (STRICT JSON):
{
"location":"<string>",
"start_date":"YYYY-MM-DD",
"end_date":"YYYY-MM-DD",
"units":"metric|imperial",
"confidence": 0.0
}
Notes:
● Use deterministic parsing (e.g., small Python function + dateparser) and/or LLM—but
final output must match schema (auto-retry if not).
● Enforce span ≤ 31 days; on violation, emit a structured error for the API.
Task B — Fetch Data via MCP Tool
Agent B: “Weather Fetcher”
Inputs: Context from Task A (params), MCP tool weather.get_range.
Action: Call the MCP tool with params; put result into context:
{
"params": { ... },
"weather_raw": { ...MCP result... }
}
Notes: Log tool call duration; gracefully handle provider gaps.
Task C — Summarize to Natural Language
Agent C: “Weather Analyst”
Inputs: params + weather_raw from Task B
Output:
{
"summary_text":"human-friendly synopsis (150–250 words)",
"highlights":{
"pattern":"hot/cool, wet/dry, windy/calm",
"extremes":{"coldest":{"date":"...","tmin":..},"hottest":{"date":"...","tmax":..}},
"notable_days":[{"date":"...","note":"heavy rain"}, {"date":"...","note":"strong winds"}]
},
"confidence": 0.0
}
Style: concise, factual, no hallucinated units; mention notable days.
3) HTTP API (Python FastAPI preferred)
Auth: x-api-key header.
Endpoints:
● POST /v1/weather/ask
○ Body: { "query": "natural language" }
○ Response:
{
"summary": "...",
"params": { "location":"...", "start_date":"...", "end_date":"...", "units":"..." },
"data": { "daily":[ ... ], "source":"open-meteo" },
"confidence": 0.82,
"tool_used": "weather.get_range",
"latency_ms": 1234,
"request_id": "uuid"
}
○
○ Errors: 400 for invalid ranges/unknown location; 429 if rate-limited; 502 for
provider failure (with safe message).
● GET /healthz → { "ok": true }
Operational requirements
● Structured logs (request_id, durations per task/tool).
● Config via env: API_KEY, TZ, LOG_LEVEL, WEATHER_PROVIDER, [optional]
WEATHER_API_KEY.
4) Deployment (Google Cloud Run)
● Single Docker image that launches the API and spawns the MCP server as a child
process (stdio).
● Provide Dockerfile + exact gcloud run deploy steps in README.md.
● Allow unauthenticated invocations at Cloud Run but require x-api-key.
Acceptance Checklist (what you’ll be graded on)
1. Task A reliably returns strict JSON params; spans > 31 days rejected.
2. Task B actually calls the MCP tool (visible in logs) and attaches raw data.
3. Task C produces an accurate, compact summary with highlights & extremes.
4. API responds within reasonable time; returns both human summary & raw data.
5. Cloud Run deployment works from a fresh machine using your README steps.
6. Tests cover: parser (Task A), MCP tool client (mocked), one end-to-end API test.
Project Layout (suggested)
weather-sense/
api/
main.py # FastAPI entry
security.py # API key check
logging.py
crew/
flow.py # defines Tasks A→B→C and orchestration
agents.py # agent configs/prompts
parser.py # deterministic helpers for Task A
mcp_client.py # spawn/connect to MCP stdio
mcp_weather/
server.py # MCP tool impl
provider.py # Open-Meteo client
cache.py
tests/
test_parser.py
test_mcp_client.py
test_api_e2e.py
Dockerfile
pyproject.toml
README.md
NOTES.md
Example Contracts (copy into the brief)
Task A system rules (must enforce):
● Extract location, start_date, end_date, units.
● Use ISO dates. If units unspecified → "metric".
● If parsing fails or range > 31 days, output:
{"error":"<reason>","hint":"<how to fix>"}
●
● Otherwise output the strict params JSON (no extra keys).
Task C summary rubric:
● 2–3 sentences overview + bullets for highlights.
● Mention coldest/hottest day with values & dates.
● Call out any day with precip_mm >= 5 (or provider’s “rainy” threshold) and
wind_max_kph >= 40.
Deliverables
1. Repo URL with code and tests.
2. Cloud Run URL + test x-api-key.
3. README.md: local run, envs, curl examples, deploy steps.
4. NOTES.md: design choices, trade-offs, what you’d improve next.
Quick test commands we’ll run
# Health
curl -s $BASE/healthz
# Natural language range (Task A → B → C)
curl -s -X POST $BASE/v1/weather/ask \
-H "Content-Type: application/json" \
-H "x-api-key: $KEY" \
-d '{"query":"Summarize weather in Tel Aviv from last Monday to Friday, metric"}' | jq
# Explicit dates & imperial
curl -s -X POST $BASE/v1/weather/ask \
-H "Content-Type: application/json" \
-H "x-api-key: $KEY" \
-d '{"query":"NYC weather 2025-10-01 to 2025-10-07, imperial"}' | jq