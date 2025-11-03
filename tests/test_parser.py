# tests/test_task_parser.py
import pytest
from weather.crew.parser import parse_range, EMPTY_QUERY_ERROR, DATE_RANGE_ERROR, DATE_ORDER_ERROR, lOCATION_ERROR, PARSE_ERROR, DATE_PARSE_ERROR


valid_queries = [
    # minimal
    {"query": "Weather in Tel Aviv from 2025-10-01 to 2025-10-07"},
    # with units
    {"query": "What's the weather in New York from 2025-09-15 to 2025-09-20, imperial"},
    # human dates
    {"query": "Forecast in London from October 5, 2025 to October 10, 2025, metric"},
    # coordinates
    {"query": "Forecast in 34.0522,-118.2437 from 2025-11-01 to 2025-11-05, metric"},
    # relative dates
    {"query": "Weather in Paris from next Monday to next Friday"},
]

@pytest.mark.parametrize("input_query", valid_queries)
def test_parse_range_valid(input_query):
    result = parse_range(input_query)
    assert "error" not in result, input_query


invalid = [
    # empty
    ({"query": ""}, EMPTY_QUERY_ERROR),
    # unparseable
    ({"query": "Tell me the weather"}, PARSE_ERROR),
    # invalid dates
    ({"query": "Weather in Berlin from foo to bar"}, DATE_PARSE_ERROR),
    # end before start
    ({"query": "Weather in Tokyo from 2025-12-10 to 2025-12-05"}, DATE_ORDER_ERROR),
    # span too long
    ({"query": "Weather in Tokyo from 2025-01-01 to 2025-03-15"}, DATE_RANGE_ERROR),
    # invalid location
    ({"query": "Weather in NowhereLand from 2025-10-01 to 2025-10-05"}, lOCATION_ERROR),
]   
    
@pytest.mark.parametrize("input_query, expected_error", invalid)
def test_parse_range_invalid(input_query, expected_error):
    result = parse_range(input_query)
    assert "error" in result, input_query
    assert expected_error in result["error"]

