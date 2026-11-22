"""The model boundary. A real model transport is deliberately not enabled yet."""
import json
from dataclasses import dataclass
from typing import Protocol

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {"code": {"type": "string", "minLength": 1, "maxLength": 8192}},
    "required": ["code"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class Prompt:
    description: str
    function_name: str
    source_context: str
    development_failure: dict
    seed: int
    json_schema: dict


@dataclass(frozen=True)
class Reply:
    text: str
    truncated: bool = False


class Model(Protocol):
    def propose(self, prompt: Prompt) -> Reply: ...


class OutputRejected(ValueError):
    pass


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise OutputRejected("Duplicate JSON key")
        result[key] = value
    return result


def parse_reply(reply):
    if reply.truncated:
        raise OutputRejected("Generation was truncated")
    if len(reply.text.encode("utf-8")) > 16384:
        raise OutputRejected("Response byte budget exceeded")
    try:
        value = json.loads(reply.text, object_pairs_hook=_unique_object)
    except (ValueError, TypeError) as error:
        raise OutputRejected(f"Invalid JSON: {error}") from error
    if not isinstance(value, dict) or set(value) != {"code"}:
        raise OutputRejected("Expected exactly one JSON field: code")
    code = value["code"]
    if not isinstance(code, str) or not 1 <= len(code) <= 8192:
        raise OutputRejected("code must be a nonempty string of at most 8192 characters")
    return code


class FakeModel:
    """Scripted fault injection; its oracle answers are not accuracy evidence."""
    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    def propose(self, prompt):
        self.prompts.append(prompt)
        index = len(self.prompts) - 1
        value = self.replies[min(index, len(self.replies) - 1)]
        if isinstance(value, Exception):
            raise value
        return value


def code_reply(code):
    return Reply(json.dumps({"code": code}))
