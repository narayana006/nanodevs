Keep all project files, virtualenvs, caches and results in this directory.
Do not download model weights, dependencies, benchmark assets or images without explicit approval naming source and size.
Local only: no remotes, pushes, public repositories or external services.
Use the Python standard library for the first harness milestone.
Fake model runs are pipeline validation, never model accuracy evidence.
Keep hidden tests out of model prompts and candidate selection. Never modify benchmark tests to pass a candidate.
Freeze task selection and budgets before evaluating real models. Count all timeouts, OOMs and exhausted budgets.
Run tests with TMPDIR="$PWD/.tmp" .venv/bin/python -B -m unittest discover -s tests -v (create .tmp first).
