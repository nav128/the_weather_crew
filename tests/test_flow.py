"""Unit tests for crew flow (A -> B -> C).

These tests exercise parsing, provider invocation (injected), retry behavior,
and summarization logic.
"""

from weather.crew.flow import run_flow, FlowError, task_c_summarize
import pytest


def test_run_flow_happy_path():
    # agent text that parse_request_from_text understands
    agent_text = "location: 31.77,35.21; start_date: 2025-01-01; end_date: 2025-01-02; units: metric; confidence: 0.9"

    # provider callable returns an Open-Meteo-like structure
    def provider_call(req):
        return {"data": {"hourly": {"temperature_2m": [10, 14, 12]}}}

    summary = run_flow(agent_text, provider_call, max_retries=0)
    # summary should include average and samples
    assert "summary" in summary
    assert summary["summary"]["samples"] == 3
    assert summary["summary"]["avg_temperature"] == pytest.approx((10 + 14 + 12) / 3)


def test_run_flow_retry_and_fail():
    agent_text = "location: 31.77,35.21; start_date: 2025-01-01; end_date: 2025-01-02; units: metric; confidence: 0.9"

    # provider that always fails
    def failing_provider(req):
        raise RuntimeError("network")

    with pytest.raises(FlowError):
        run_flow(agent_text, failing_provider, max_retries=1)


def test_run_flow_retry_then_success():
    agent_text = "location: 31.77,35.21; start_date: 2025-01-01; end_date: 2025-01-02; units: metric; confidence: 0.9"

    calls = {"n": 0}

    def flaky_provider(req):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("temporary")
        return {"data": {"hourly": {"temperature_2m": [5, 7]}}}

    summary = run_flow(agent_text, flaky_provider, max_retries=1)
    assert summary["summary"]["samples"] == 2
