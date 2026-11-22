"""Original synthetic fixtures for pipeline proof, not a model benchmark."""
from .harness import Task
from .models import FakeModel, Reply, code_reply

SOURCE = "def adjust(value):\n    return value - 1\n"
CORRECT = "def adjust(value):\n    return value + 1\n"
WRONG = "def adjust(value):\n    return value\n"
TIMEOUT = "def adjust(value):\n    while True:\n        pass\n"
OVERFIT = "def adjust(value):\n    return 2 if value == 1 else 5\n"
SCENARIOS = (
    "success", "wrong_then_correct", "malformed_then_correct", "truncated_then_correct",
    "syntax_then_correct", "boundary_then_correct", "timeout_then_correct", "all_wrong",
    "hidden_overfit", "model_error_then_correct",
)


def fixture(scenario):
    if scenario not in SCENARIOS:
        raise ValueError("Unknown fake scenario")
    task = Task("fake-" + scenario, SOURCE, "adjust", "Fix adjust so that it returns the integer one greater than its input.", ({"args": [1], "expected": 2}, {"args": [4], "expected": 5}), ({"args": [-1], "expected": 0}, {"args": [0], "expected": 1}))
    good = code_reply(CORRECT)
    replies = {
        "success": [good],
        "wrong_then_correct": [code_reply(WRONG), good],
        "malformed_then_correct": [Reply('not JSON'), good],
        "truncated_then_correct": [Reply('{"code": "def', truncated=True), good],
        "syntax_then_correct": [code_reply('def adjust(value):\n    return (\n'), good],
        "boundary_then_correct": [code_reply(CORRECT + '\nimport os\n'), good],
        "timeout_then_correct": [code_reply(TIMEOUT), good],
        "all_wrong": [code_reply(WRONG)],
        "hidden_overfit": [code_reply(OVERFIT), good],
        "model_error_then_correct": [RuntimeError('simulated model transport failure'), good],
    }
    expected = {"all_wrong": "candidate_budget_exhausted", "hidden_overfit": "failed_hidden"}.get(scenario, "passed")
    return task, FakeModel(replies[scenario]), expected
