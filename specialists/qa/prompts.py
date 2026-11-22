"""Render a task into a model prompt and extract/grade the answer (same conventions as phase0/harness2.py)."""
import re

import sandbox


def show(files):
    return "\n\n".join(f"```python\n# file: {n}\n{c.strip()}\n```" for n, c in files.items())


def render_prompt(task):
    """Full prompt text for a task: the files the model may see, then the instruction."""
    parts = []
    label = "Buggy code" if task["kind"] == "regression" else "Code under test"
    parts.append(f"{label}:\n{show(task['files'])}")
    if task["kind"] == "improve":
        parts.append("Existing test file:\n```python\n# file: test_solution.py\n" + task["starting_tests"].strip() + "\n```")
    parts.append(task["instruction"])
    return "\n\n".join(parts)


def extract_tests(text):
    """Content of the ```python block starting with `# file: test_solution.py` (None if absent)."""
    for block in re.findall(r"```[A-Za-z]*[ \t]*\n(.*?)```", text, re.S):
        m = re.match(r"\s*#\s*file:\s*test_solution\.py[ \t]*\n", block)
        if m:
            return block[m.end():]
    return None


def grade_answer(task, text):
    """(passed, detail): the extracted test file must pass on the correct code and kill every mutant."""
    code = extract_tests(text)
    if code is None:
        return False, "NO test_solution.py block"
    return sandbox.grade(task, code)
