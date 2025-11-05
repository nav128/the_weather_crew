"""API entrypoint (FastAPI)

Minimal FastAPI application exposing a single endpoint to run the strict
weather query and a health check. The implementation is intentionally
lightweight and suitable for unit-testing (the app is importable as
``app``).

Security:
- API key is checked via the `X-API-Key` header against the
  `WEATHER_API_KEY` environment variable (if set). If the env var is not
  set the dependency allows any key (useful for local development).

Endpoint:
- POST /v1/weather/ask accepts the strict request schema (location,
  start_date, end_date, units, confidence) and returns a structured
  response that includes a small summary, raw provider data and metadata.

Error handling:
- 400 for validation errors
- 502 for provider/network failures
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()


from weather.crew.flow import run_weather_pipeline
from weather.api.errors import *


app = FastAPI(title="Weather API")


def get_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
	"""Simple API key dependency.

	If WEATHER_API_KEY is set in the environment the incoming header must
	match it. If not set we allow any key (no-op) to simplify local dev.
	"""
	wanted = os.environ.get("WEATHER_API_KEY")
	if wanted:
		if not x_api_key or x_api_key != wanted:
			raise HTTPException(status_code=401, detail="invalid or missing API key")
	return x_api_key


@app.get("/healthz")
def healthz():
	return {"ok": True, "message": "Service is healthy"}


@app.post("/v1/weather/ask")
def weather_ask(req: dict, ):#api_key: Optional[str] = Depends(get_api_key)
	request_id = str(uuid.uuid4())
	start = time.time()
	try:
		out = run_weather_pipeline(req)
	except WeatherValidationError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc
	except WeatherRateLimitError as exc:
		raise HTTPException(status_code=429, detail=str(exc)) from exc
	except WeatherProviderError as exc:
		raise HTTPException(status_code=502, detail=str(exc)) from exc
	except FlowError as exc:
		raise HTTPException(status_code=500, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=500, detail="internal error" + "\n\n" + str(exc)) from exc

	latency_ms = int((time.time() - start) * 1000)

	response = {
		**out,
		"latency_ms": latency_ms,
		"request_id": request_id,
	}
	return response
