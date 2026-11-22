import ast
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from nanodevs.checks import run_checks
from nanodevs.context import EditRejected, apply_function_edit, select_context
from nanodevs.fixtures import CORRECT, SCENARIOS, SOURCE, fixture
from nanodevs.harness import Config, run_task
from nanodevs.models import FakeModel, OUTPUT_SCHEMA, OutputRejected, Reply, code_reply, parse_reply
from nanodevs.resources import verify_limits


class TestOutputContract(unittest.TestCase):
    def test_schema_on_disk_matches_transport_contract(self):
        disk = json.loads((Path(__file__).resolve().parents[1] / "contracts/output.schema.json").read_text())
        self.assertEqual(disk, OUTPUT_SCHEMA)

    def test_accepts_exact_object(self):
        self.assertEqual(parse_reply(code_reply(CORRECT)), CORRECT)

    def test_rejects_malformed_unknown_duplicate_empty_and_truncated(self):
        bad = [Reply('not json'), Reply('{"code":"a","code":"b"}'), Reply('{"code":"a","path":"secret.py"}'), Reply('{"code":""}'), Reply('{"code":42}'), Reply('[]'), Reply('{}'), Reply('{"code":"a"}', truncated=True), code_reply('a' * 8193)]
        for reply in bad:
            with self.subTest(reply=reply), self.assertRaises(OutputRejected):
                parse_reply(reply)


class TestContextAndEdits(unittest.TestCase):
    def test_retrieves_helper_and_constant_without_unrelated_function(self):
        source = 'VALUE = 4\n\ndef helper(x):\n    return x + VALUE\n\ndef adjust(value):\n    return helper(value)\n\ndef unrelated():\n    return "do not send this"\n'
        context = select_context(source, 'adjust')
        self.assertIn('VALUE = 4', context.code)
        self.assertIn('def helper', context.code)
        self.assertNotIn('unrelated', context.code)
        self.assertLessEqual(context.source_lines, 50)

    def test_only_relevant_imports_enter_context(self):
        source = 'import os\nimport math as m\n\ndef adjust(value):\n    return m.floor(value)\n'
        context = select_context(source, 'adjust')
        self.assertIn('import math as m', context.code)
        self.assertNotIn('import os', context.code)

    def test_return_annotation_cannot_be_changed(self):
        source = 'def adjust(value) -> int:\n    return value - 1\n'
        with self.assertRaises(EditRejected):
            apply_function_edit(source, 'adjust', 'def adjust(value) -> str:\n    return str(value)\n')

    def test_excess_context_is_rejected_not_truncated(self):
        source = 'def adjust(value):\n' + '    value += 1\n' * 51 + '    return value\n'
        with self.assertRaises(EditRejected):
            select_context(source, 'adjust')

    def test_missing_and_decorated_targets_are_rejected(self):
        for source, name in [(SOURCE, 'missing'), ('@decorator\n' + SOURCE, 'adjust')]:
            with self.subTest(source=source), self.assertRaises(EditRejected):
                select_context(source, name)

    def test_only_target_function_changes(self):
        prefix = 'import math\n\nSENTINEL = "unchanged"\n\n'
        suffix = '\ndef other():\n    return SENTINEL\n'
        edited = apply_function_edit(prefix + SOURCE + suffix, 'adjust', CORRECT)
        self.assertEqual(edited, prefix + CORRECT + suffix)
        ast.parse(edited)

    def test_rejects_changed_signature_extra_code_and_invalid_python(self):
        for proposal in ['def other(value):\n    return 2\n', 'def adjust(x):\n    return x + 1\n', CORRECT + '\nimport os\n', 'def adjust(value):\n    return (\n']:
            with self.subTest(proposal=proposal), self.assertRaises(EditRejected):
                apply_function_edit(SOURCE, 'adjust', proposal)


class TestFixedRecipe(unittest.TestCase):
    def test_all_fault_injection_contracts(self):
        for scenario in SCENARIOS:
            task, model, expected = fixture(scenario)
            with self.subTest(scenario=scenario):
                result = run_task(task, model, Config(max_candidates=3, check_timeout=0.5))
                self.assertEqual(result['status'], expected)
                self.assertLessEqual(len(model.prompts), 3)
                self.assertTrue(all(p.source_context == model.prompts[0].source_context for p in model.prompts))
                self.assertTrue(all(e['kind'] == 'fresh_sample' for e in result['attempts']))
                self.assertEqual([p.seed for p in model.prompts], list(range(1729, 1729 + len(model.prompts))))

    def test_stops_at_first_development_acceptance_even_if_hidden_fails(self):
        task, model, _ = fixture('hidden_overfit')
        result = run_task(task, model)
        self.assertEqual(result['status'], 'failed_hidden')
        self.assertEqual(len(model.prompts), 1)
        self.assertEqual(result['selected_attempt'], 1)
        self.assertNotIn('hidden', model.prompts[0].development_failure)
        self.assertFalse(hasattr(model.prompts[0], 'hidden_cases'))

    def test_correct_baseline_never_calls_model(self):
        task, model, _ = fixture('success')
        result = run_task(replace(task, source=CORRECT), model)
        self.assertEqual(result['status'], 'invalid_baseline')
        self.assertEqual(len(model.prompts), 0)

    def test_context_rejection_never_calls_model(self):
        task, model, _ = fixture('success')
        result = run_task(task, model, Config(max_context_lines=1))
        self.assertEqual(result['status'], 'context_rejected')
        self.assertEqual(len(model.prompts), 0)

    def test_model_errors_consume_candidate_budget(self):
        task, _, _ = fixture('success')
        model = FakeModel([RuntimeError('offline')])
        result = run_task(task, model, Config(max_candidates=3))
        self.assertEqual(result['status'], 'candidate_budget_exhausted')
        self.assertEqual(len(model.prompts), 3)

    def test_cumulative_task_deadline_stops_sampling(self):
        task, model, _ = fixture('success')
        result = run_task(task, model, Config(task_timeout=0.000001))
        self.assertIn(result['status'], {'invalid_baseline', 'task_timeout'})
        self.assertEqual(len(model.prompts), 0)

    def test_invalid_budgets_are_rejected(self):
        for kwargs in [{'max_candidates': 0}, {'max_candidates': 11}, {'max_context_lines': 51}, {'check_timeout': 0}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Config(**kwargs)

    def test_worker_crash_is_not_a_passing_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_checks('import os\nos._exit(3)\n' + SOURCE, 'adjust', [{'args': [1], 'expected': 2}], Path(tmp))
        self.assertEqual(result['status'], 'process_error')
        self.assertEqual(result['returncode'], 3)

    def test_worker_timeout_is_not_a_passing_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_checks('def adjust(value):\n    while True:\n        pass\n', 'adjust', [{'args': [1], 'expected': 2}], Path(tmp), timeout=0.1)
        self.assertEqual(result['status'], 'timeout')


class TestCgroupLimits(unittest.TestCase):
    def write_cgroup(self, root, memory='2147483648', swap='0', cpu='200000 100000'):
        for filename, value in {'memory.max': memory, 'memory.swap.max': swap, 'cpu.max': cpu, 'memory.peak': '50000000', 'memory.events': 'oom_kill 0'}.items():
            (root / filename).write_text(value)

    def test_exact_limits_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_cgroup(root)
            self.assertTrue(verify_limits('lite', root)['verified'])

    def test_rejects_swap_unlimited_memory_and_wrong_cpu_quota(self):
        for kwargs in [{'swap': '2147483648'}, {'memory': 'max'}, {'cpu': '400000 100000'}, {'cpu': 'max 100000'}]:
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.write_cgroup(root, **kwargs)
                with self.assertRaises(RuntimeError):
                    verify_limits('lite', root)

    def test_standard_has_distinct_memory_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_cgroup(root, memory='4294967296')
            self.assertTrue(verify_limits('standard', root)['verified'])
            with self.assertRaises(RuntimeError):
                verify_limits('lite', root)


if __name__ == '__main__':
    unittest.main()
