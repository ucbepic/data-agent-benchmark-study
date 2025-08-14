from typing import Any
import json


class RepeatedCallTracker:
    """
    Tracks repeated tool calls with the same arguments.
    Terminates if the same tool and arguments are repeated more than `max_repeats` times.
    """
    def __init__(self, max_repeats: int = 5):
        self.last_call = None
        self.repeat_count = 0
        self.max_repeats = max_repeats

    def _serialize_args(self, args: dict) -> str:
        try:
            return json.dumps(args, sort_keys=True)
        except Exception:
            return str(args)

    def check_and_update(self, tool_name: str, tool_args: dict) -> bool:
        current = (tool_name, self._serialize_args(tool_args))

        if current == self.last_call:
            self.repeat_count += 1
        else:
            self.last_call = current
            self.repeat_count = 1

        if self.repeat_count >= self.max_repeats:
            print(f"⚠️ Detected {self.repeat_count} repeated calls to tool '{tool_name}' with same arguments.")
            return True
        return False


class QueryDbFailureTracker:
    """
    Tracks consecutive query_db failures.
    Terminates if failures exceed `max_failures`.
    """
    def __init__(self, max_failures: int = 5):
        self.max_failures = max_failures
        self.failure_count = 0

    def record(self, success: bool) -> bool:
        if success:
            self.failure_count = 0
        else:
            self.failure_count += 1

        if self.failure_count > self.max_failures:
            print(f"⚠️ Detected {self.failure_count} consecutive query_db failures.")
            return True
        return False
