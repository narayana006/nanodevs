import argparse
import json

from .fixtures import SCENARIOS, fixture
from .harness import Config, run_task
from .resources import verify_limits


def main():
    parser = argparse.ArgumentParser(description="nanodevs step 1: fake-model pipeline proof only")
    parser.add_argument("command", choices=["run-fake"])
    parser.add_argument("--scenario", required=True, choices=SCENARIOS)
    parser.add_argument("--tier", required=True, choices=["lite", "standard"])
    parser.add_argument("--candidates", type=int, default=5)
    args = parser.parse_args()
    before = verify_limits(args.tier)
    task, model, expected = fixture(args.scenario)
    result = run_task(task, model, Config(max_candidates=args.candidates, check_timeout=0.5))
    result.update(mode="fake_pipeline", real_model_evaluated=False, tier=args.tier, expected_status=expected, pipeline_contract_passed=result["status"] == expected, model_calls=len(model.prompts), limits=before, resources=verify_limits(args.tier))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
