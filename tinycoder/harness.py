"""One fixed recipe: locate -> read -> propose -> check; no model planning."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tempfile
import time

from .checks import run_checks
from .context import EditRejected, apply_function_edit, select_context
from .models import OUTPUT_SCHEMA, OutputRejected, Prompt, parse_reply


@dataclass(frozen=True)
class Task:
    task_id: str
    source: str
    function_name: str
    description: str
    development_cases: tuple
    hidden_cases: tuple


@dataclass(frozen=True)
class Config:
    max_candidates: int = 10
    seed: int = 1729
    max_context_lines: int = 50
    check_timeout: float = 1.0
    task_timeout: float = 30.0

    def __post_init__(self):
        if not 1 <= self.max_candidates <= 10:
            raise ValueError("Candidate budget must be between 1 and 10")
        if not 1 <= self.max_context_lines <= 50:
            raise ValueError("Context budget must be between 1 and 50 source lines")
        if self.check_timeout <= 0 or self.task_timeout <= 0:
            raise ValueError("Timeouts must be positive")


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def run_task(task, model, config=Config()):
    started = time.monotonic()
    result = {"task_id": task.task_id, "skill": "bugfix", "status": "pending", "source_sha256": digest(task.source), "budget": {"max_candidates": config.max_candidates, "repair_rounds": 0, "context_lines_max": config.max_context_lines, "check_timeout_seconds": config.check_timeout, "task_timeout_seconds": config.task_timeout}, "cards_enabled": False, "attempts": []}
    original_cases = json.dumps([task.development_cases, task.hidden_cases], sort_keys=True)
    try:
        context = select_context(task.source, task.function_name, config.max_context_lines)
    except (EditRejected, SyntaxError) as error:
        result.update(status="context_rejected", reason=str(error), seconds=time.monotonic() - started)
        return result
    result["context_source_lines"] = context.source_lines
    with tempfile.TemporaryDirectory(prefix="tinycoder-task-") as tmp:
        directory = Path(tmp)
        baseline = run_checks(task.source, task.function_name, task.development_cases, directory, min(config.check_timeout, config.task_timeout))
        result["baseline"] = baseline
        if baseline["status"] != "failed":
            result.update(status="invalid_baseline", seconds=time.monotonic() - started)
            return result
        for attempt in range(config.max_candidates):
            remaining = config.task_timeout - (time.monotonic() - started)
            if remaining <= 0:
                result["status"] = "task_timeout"
                break
            event = {"attempt": attempt + 1, "seed": config.seed + attempt, "kind": "fresh_sample", "context_sha256": digest(context.code)}
            result["attempts"].append(event)
            # No hidden cases and no preceding candidate are supplied to the model.
            prompt = Prompt(task.description, task.function_name, context.code, baseline, config.seed + attempt, OUTPUT_SCHEMA)
            try:
                reply = model.propose(prompt)
                event.update(raw_response=reply.text, truncated=reply.truncated)
            except Exception as error:
                event.update(status="model_error", reason=str(error)[:250])
                continue
            if time.monotonic() - started >= config.task_timeout:
                event["status"] = "task_timeout"
                result["status"] = "task_timeout"
                break
            try:
                replacement = parse_reply(reply)
                candidate = apply_function_edit(task.source, task.function_name, replacement)
            except (OutputRejected, EditRejected) as error:
                event.update(status="output_rejected", reason=str(error))
                continue
            event["candidate_sha256"] = digest(candidate)
            remaining = config.task_timeout - (time.monotonic() - started)
            check = run_checks(candidate, task.function_name, task.development_cases, directory, min(config.check_timeout, max(0.001, remaining)))
            event.update(status="development_" + check["status"], development=check)
            if check["status"] != "passed":
                continue
            result["selected_attempt"] = attempt + 1
            result["selected_code"] = candidate
            remaining = config.task_timeout - (time.monotonic() - started)
            if remaining <= 0:
                result["status"] = "task_timeout"
                break
            # Final evaluation only. Its outcome never controls another sample.
            hidden = run_checks(candidate, task.function_name, task.hidden_cases, directory, min(config.check_timeout, remaining))
            result["hidden"] = hidden
            result["status"] = "passed" if hidden["status"] == "passed" else "failed_hidden"
            break
        else:
            result["status"] = "candidate_budget_exhausted"
    assert original_cases == json.dumps([task.development_cases, task.hidden_cases], sort_keys=True)
    result["seconds"] = time.monotonic() - started
    result["first_attempt_success"] = result["status"] == "passed" and result.get("selected_attempt") == 1
    return result
