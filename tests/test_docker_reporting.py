import runpy
from pathlib import Path
import unittest

RUNNER = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/run_docker.py"))


class TestDockerFailureReporting(unittest.TestCase):
    def record(self, **kwargs):
        value = {"state": {"OOMKilled": False, "ExitCode": 0}, "timed_out": False, "stdout": ""}
        value.update(kwargs)
        return value

    def test_oom_is_reported_without_valid_json(self):
        result = RUNNER["classify"](self.record(state={"OOMKilled": True, "ExitCode": 137}))
        self.assertEqual(result["status"], "container_oom")
        self.assertFalse(result["pipeline_contract_passed"])

    def test_container_timeout_is_not_dropped(self):
        result = RUNNER["classify"](self.record(timed_out=True))
        self.assertEqual(result["status"], "container_timeout")

    def test_nonzero_exit_is_not_accepted_even_with_success_json(self):
        result = RUNNER["classify"](self.record(state={"ExitCode": 1}, stdout='{ "pipeline_contract_passed": true }'))
        self.assertEqual(result["status"], "container_error")

    def test_unparseable_results_are_recorded(self):
        self.assertEqual(RUNNER["classify"](self.record(stdout="crash"))["status"], "result_protocol_error")

    def test_fake_summary_cannot_claim_model_accuracy(self):
        self.assertIsNone(RUNNER["summarize"]([])["lite"]["model_pass_rate"])
