# """mcp_client
# ----------------
# Minimal, dependency-free MCP client for stdio-based MCPs.

# This implements a small, testable wrapper around a subprocess that communicates
# via STDIN/STDOUT. It exposes a simple API to start/stop the process, send
# line-oriented messages and receive responses.

# Design goals / contract (small):
# - Inputs: a command (list[str]) to spawn the MCP process.
# - Outputs: strings read from the MCP process stdout (line-oriented).
# - Error modes: raises RuntimeError or TimeoutError for obvious lifecycle issues.
# - Success criteria: basic send/read/stop lifecycle works in unit tests.

# Edge cases considered:
# - Subprocess exit while waiting for response
# - Timeouts when reading
# - Clean shutdown and resource release

# Note: This intentionally keeps the protocol layer out; it provides raw
# line-oriented send/read primitives so higher layers (JSON-RPC, framing)
# can be implemented on top.
# """

# from __future__ import annotations

# import subprocess
# import threading
# import queue
# import time
# import json
# import re
# from datetime import datetime
# from typing import Iterable, Optional


# class MCPClient:
# 	"""Spawn/connect to an MCP over stdio and exchange line-oriented messages.

# 	Example:
# 		client = MCPClient(["/usr/bin/some-mcp", "--stdio"]) 
# 		client.start()
# 		client.send_line('hello')
# 		resp = client.read_line(timeout=2.0)
# 		client.stop()
# 	"""

# 	def __init__(self, cmd: Iterable[str], read_buffer: int = 1000) -> None:
# 		self._cmd = list(cmd)
# 		self._proc: Optional[subprocess.Popen] = None
# 		self._reader_thread: Optional[threading.Thread] = None
# 		self._out_queue: queue.Queue[str] = queue.Queue(maxsize=read_buffer)
# 		self._stop_event = threading.Event()

# 	def start(self, cwd: Optional[str] = None, env: Optional[dict] = None) -> None:
# 		"""Start the subprocess and background reader thread.

# 		Raises RuntimeError if the process is already started or fails to spawn.
# 		"""
# 		if self._proc is not None:
# 			raise RuntimeError("MCPClient already started")

# 		# start the subprocess with unbuffered text streams
# 		self._proc = subprocess.Popen(
# 			self._cmd,
# 			stdin=subprocess.PIPE,
# 			stdout=subprocess.PIPE,
# 			stderr=subprocess.PIPE,
# 			universal_newlines=True,
# 			bufsize=1,
# 			cwd=cwd,
# 			env=env,
# 		)

# 		# start reader thread
# 		self._stop_event.clear()
# 		self._reader_thread = threading.Thread(target=self._reader, daemon=True)
# 		self._reader_thread.start()

# 	def _reader(self) -> None:
# 		"""Background reader: read lines from process stdout and push to queue."""
# 		assert self._proc is not None
# 		stdout = self._proc.stdout
# 		if stdout is None:
# 			return

# 		for line in stdout:
# 			if self._stop_event.is_set():
# 				break
# 			# strip trailing newline but preserve other whitespace
# 			self._put_line(line.rstrip("\n"))

# 		# if we exit the loop, mark process EOF
# 		self._put_line("")

# 	def _put_line(self, line: str) -> None:
# 		try:
# 			self._out_queue.put(line, block=False)
# 		except queue.Full:
# 			# drop oldest if full to avoid blocking reader thread
# 			try:
# 				_ = self._out_queue.get_nowait()
# 			except Exception:
# 				pass
# 			try:
# 				self._out_queue.put(line, block=False)
# 			except Exception:
# 				# give up silently - best-effort to avoid reader blocking
# 				pass

# 	def send_line(self, message: str, flush: bool = True) -> None:
# 		"""Send a single line to the MCP process (adds newline).

# 		Raises RuntimeError if the process is not running or stdin is closed.
# 		"""
# 		if self._proc is None:
# 			raise RuntimeError("Process not started")
# 		if self._proc.stdin is None:
# 			raise RuntimeError("Process stdin not available")

# 		try:
# 			self._proc.stdin.write(message + "\n")
# 			if flush:
# 				self._proc.stdin.flush()
# 		except BrokenPipeError:
# 			raise RuntimeError("Process stdin closed (BrokenPipe)")

# 	def read_json(self, timeout: Optional[float] = None) -> Optional[dict]:
# 		"""Read a line and parse it as JSON, returning a dict.

# 		Returns None if EOF is reached. Raises ValueError on invalid JSON or
# 		if the decoded value is not a mapping. For schema validation call
# 		`validate_request` on the returned dict.
# 		"""
# 		line = self.read_line(timeout=timeout)
# 		if line is None:
# 			return None
# 		try:
# 			obj = json.loads(line)
# 		except json.JSONDecodeError as exc:
# 			raise ValueError(f"Invalid JSON from MCP: {exc.msg}") from exc
# 		if not isinstance(obj, dict):
# 			raise ValueError("MCP JSON message must be an object")
# 		return obj

# 	def send_json(self, obj: dict, flush: bool = True) -> None:
# 		"""Send a JSON object as a single line to the MCP process.

# 		The object is serialized with json.dumps and a single trailing newline is
# 		written. This method does NOT alter the object (no filtering). Callers
# 		should ensure the object conforms to the expected schema by calling
# 		`validate_request` first when appropriate.
# 		"""
# 		# ensure this is a plain mapping
# 		# if not isinstance(obj, dict):
# 		# 	raise TypeError("send_json expects a dict")
# 		# payload = json.dumps(obj, separators=(",", ":"))
# 		self.send_line(obj, flush=flush)

# 	def read_line(self, timeout: Optional[float] = None) -> Optional[str]:
# 		"""Read a line from the MCP process output queue.

# 		Returns the line (without trailing newline), or None on EOF. Raises
# 		queue.Empty wrapped as TimeoutError on timeout.
# 		"""
# 		try:
# 			line = self._out_queue.get(block=True, timeout=timeout)
# 		except queue.Empty:
# 			raise TimeoutError("Timeout waiting for line from MCP")

# 		# empty string represents EOF marker from reader
# 		if line == "":
# 			return None
# 		return line

# 	def stop(self, kill_timeout: float = 1.0) -> None:
# 		"""Stop the MCP process and wait for the reader thread to finish."""
# 		if self._proc is None:
# 			return

# 		try:
# 			# try graceful termination: close stdin so child may exit
# 			if self._proc.stdin is not None:
# 				try:
# 					self._proc.stdin.close()
# 				except Exception:
# 					pass

# 			# wait a short while
# 			try:
# 				self._proc.wait(timeout=kill_timeout)
# 			except subprocess.TimeoutExpired:
# 				# escalate to kill
# 				try:
# 					self._proc.kill()
# 				except Exception:
# 					pass
# 				self._proc.wait()
# 		finally:
# 			self._stop_event.set()
# 			# join reader thread if running
# 			if self._reader_thread is not None:
# 				self._reader_thread.join(timeout=0.5)

# 			# cleanup handles
# 			if self._proc.stdout is not None:
# 				try:
# 					self._proc.stdout.close()
# 				except Exception:
# 					pass
# 			if self._proc.stderr is not None:
# 				try:
# 					self._proc.stderr.close()
# 				except Exception:
# 					pass

# 			self._proc = None
# 			self._reader_thread = None


# 	def validate_request(obj: dict) -> None:
# 		"""Validate the strict request schema expected by the MCP.

# 		Expected schema (all required):
# 		{
# 		  "location": "<string>",
# 		  "start_date": "YYYY-MM-DD",
# 		  "end_date": "YYYY-MM-DD",
# 		  "units": "metric|imperial",
# 		  "confidence": 0.0
# 		}

# 		Raises ValueError with a helpful message if invalid.
# 		"""
# 		if not isinstance(obj, dict):
# 			raise ValueError("request must be a JSON object")

# 		required = {"location", "start_date", "end_date", "units", "confidence"}
# 		received = set(obj.keys())
# 		missing = required - received
# 		extra = received - required
# 		if missing:
# 			raise ValueError(f"missing required fields: {', '.join(sorted(missing))}")
# 		if extra:
# 			raise ValueError(f"unexpected fields present: {', '.join(sorted(extra))}")

# 		# location: non-empty string
# 		if not isinstance(obj["location"], str) or not obj["location"].strip():
# 			raise ValueError("location must be a non-empty string")

# 		# date format YYYY-MM-DD; ensure start <= end
# 		date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# 		for key in ("start_date", "end_date"):
# 			if not isinstance(obj[key], str) or not date_re.match(obj[key]):
# 				raise ValueError(f"{key} must be a string in YYYY-MM-DD format")
# 			try:
# 				# will raise ValueError if invalid date
# 				_ = datetime.strptime(obj[key], "%Y-%m-%d").date()
# 			except ValueError:
# 				raise ValueError(f"{key} is not a valid date in YYYY-MM-DD format")

# 		start = datetime.strptime(obj["start_date"], "%Y-%m-%d").date()
# 		end = datetime.strptime(obj["end_date"], "%Y-%m-%d").date()
# 		if start > end:
# 			raise ValueError("start_date must be <= end_date")

# 		# units: either metric or imperial
# 		if obj["units"] not in ("metric", "imperial"):
# 			raise ValueError("units must be either 'metric' or 'imperial'")

# 		# confidence: number between 0.0 and 1.0 (inclusive)
# 		conf = obj["confidence"]
# 		if not (isinstance(conf, float) or isinstance(conf, int)):
# 			raise ValueError("confidence must be a number between 0.0 and 1.0")
# 		conf_val = float(conf)
# 		if not (0.0 <= conf_val <= 1.0):
# 			raise ValueError("confidence must be between 0.0 and 1.0 inclusive")


# def _quick_demo() -> None:
# 	"""A tiny demo used only when running this module directly.

# 	It spawns a Python subprocess that echoes lines back and demonstrates
# 	send/read lifecycle. This function is not used by library code.
# 	"""
# 	import sys

# 	cmd = [sys.executable, "-u", "-c", "import sys\nfor l in sys.stdin:\n print('ECHO:'+l.strip())\n"]
# 	client = MCPClient(cmd)
# 	client.start()
# 	try:
# 		client.send_line("hello")
# 		resp = client.read_line(timeout=1.0)
# 		print("received:", resp)
# 	finally:
# 		client.stop()


# if __name__ == "__main__":
# 	_quick_demo()

import json
import subprocess
from weather.mcp_weather.cache import weather_cache


def send_message(proc, message):
    print("sending message:", message)
    proc.stdin.write(json.dumps(message) + "\n")
    proc.stdin.flush()
    x = proc.stdout.readline()
    print("received message:", x)
    return json.loads(x)

def mcp_client(params: dict):
    # Launch the MCP server as a subprocess
    proc = subprocess.Popen(
        ["python3", "src/weather/mcp_weather/server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    
    key = f"{params['location']}:{params['start_date']}:{params['end_date']}:{params['units']}"
    res = None
    if days := weather_cache.get(key):
        res =  {
			"daily": days,
			"source": "cached - open-meteo"
		}
    else:
          if not "fetch_weather" in send_message(proc, {
              "jsonrpc": "2.0",
              "id": 1,
              "method": "tools"
              })['result'] :
              raise RuntimeError("MCP does not support fetch_weather tool")
          
          res = send_message(proc, {
              "jsonrpc": "2.0",
              "id": 2,
              "method": "fetch_weather",
              "params": params
              })
          if error := res.get("error"):
              raise RuntimeError(f"MCP error: {error}")
          weather_cache.set(key, res["result"]["daily"])
        
    proc.terminate()
    return res, "fetch_weather"

if __name__ == "__main__":
    mcp_client({"location": "40.7128,-74.0060", "start_date": "2024-01-01", "end_date": "2024-01-07", "units": "metric"})