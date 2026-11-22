#!/usr/bin/env python3
"""Run each fake task in a fresh, resource-capped Docker container. Never pull."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tinycoder.fixtures import SCENARIOS
from tinycoder.resources import TIERS


def docker(*args, timeout=60, check=True):
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout, check=check)


def run_container(image, memory, command, timeout=60, mount_project=True):
    started = time.monotonic()
    args = ["create", "--pull=never", "--memory", str(memory), "--memory-swap", str(memory), "--cpus", "2", "--network", "none", "--pids-limit", "128", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--user", "65532:65532", "--tmpfs", "/tmp:rw,nosuid,nodev,size=100663296", "--env", "HOME=/tmp", "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "PYTHONPATH=/work", "--workdir", "/work", "--entrypoint", "python"]
    if mount_project:
        args += ["--mount", f"type=bind,source={ROOT},target=/work,readonly"]
    args += [image, "-B", *command]
    container = docker(*args).stdout.strip()
    if not container:
        raise RuntimeError("Docker did not return a container ID")
    state = {}
    stdout = stderr = ""
    timed_out = False
    try:
        try:
            finished = docker("start", "--attach", container, timeout=timeout, check=False)
            stdout, stderr = finished.stdout, finished.stderr
        except subprocess.TimeoutExpired:
            timed_out = True
            docker("kill", container, check=False)
        inspection = json.loads(docker("inspect", container).stdout)[0]
        state = inspection["State"]
        config = inspection["HostConfig"]
        if config["Memory"] != memory or config["MemorySwap"] != memory or config["NanoCpus"] != 2_000_000_000:
            raise RuntimeError("Docker did not apply the requested limits")
        if config["NetworkMode"] != "none" or not config["ReadonlyRootfs"]:
            raise RuntimeError("Docker did not apply the isolation profile")
        return {"container_id": container, "image_id": inspection["Image"], "state": state, "timed_out": timed_out, "stdout": stdout, "stderr": stderr[-4096:], "container_wall_seconds": time.monotonic() - started, "limits": {"memory": config["Memory"], "memory_swap_total": config["MemorySwap"], "nano_cpus": config["NanoCpus"], "network": config["NetworkMode"], "root_readonly": config["ReadonlyRootfs"]}}
    finally:
        # Only this owned container, never a global prune or another user's job.
        docker("rm", "--force", container, check=False)


def classify(record):
    if record["state"].get("OOMKilled"):
        return {"status": "container_oom", "pipeline_contract_passed": False}
    if record["timed_out"]:
        return {"status": "container_timeout", "pipeline_contract_passed": False}
    if record["state"].get("ExitCode") != 0:
        return {"status": "container_error", "pipeline_contract_passed": False}
    try:
        result = json.loads(record["stdout"])
        if result.get("mode") != "fake_pipeline" or result.get("real_model_evaluated") is not False:
            raise ValueError("Unexpected result protocol")
        return result
    except (ValueError, AttributeError):
        return {"status": "result_protocol_error", "pipeline_contract_passed": False}


def summarize(records):
    summary = {}
    for tier in TIERS:
        rows = [r for r in records if r["tier"] == tier]
        peaks = [int(r["result"]["resources"]["memory.peak"]) for r in rows if r["result"].get("resources", {}).get("memory.peak")]
        summary[tier] = {"fixtures_run": len(rows), "contracts_satisfied": sum(r["result"].get("pipeline_contract_passed", False) for r in rows), "max_observed_container_peak_bytes": max(peaks, default=None), "total_task_seconds": sum(r["result"].get("seconds", 0) for r in rows), "model_pass_rate": None}
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="Already cached Python image. Resolved to its immutable local ID; never pulled.")
    parser.add_argument("--output", default="reports/fake-docker.json")
    parser.add_argument("--probe-oom", action="store_true", help="Also verify OOM classification in a separate 64 MiB fault container")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT):
        parser.error("Report output must stay inside tinycoder")
    output.parent.mkdir(parents=True, exist_ok=True)
    image_info = json.loads(docker("image", "inspect", args.image).stdout)[0]
    image = image_info["Id"]
    if image_info["Os"] != "linux" or image_info["Architecture"] != "arm64":
        parser.error("Use a native Linux ARM64 image; do not benchmark under x86 emulation")
    version = json.loads(docker("version", "--format", "{{json .}}").stdout)
    records = []
    report = {"schema_version": 1, "mode": "fake_pipeline_only", "model_pass_rate": None, "decision_gate": "not_evaluated_no_real_model", "created_at_utc": datetime.now(timezone.utc).isoformat(), "image_id": image, "image_reference": args.image, "docker": version, "records": records, "notice": "These scripted fault-injection fixtures prove pipeline behavior; they are NOT QuixBugs results or model accuracy measurements. Each fixture runs in a fresh container. Cached personal-project image is a temporary interpreter donor for fake validation only; no application code is invoked."}
    for tier, memory in TIERS.items():
        for scenario in SCENARIOS:
            run = run_container(image, memory, ["-m", "tinycoder", "run-fake", "--scenario", scenario, "--tier", tier])
            result = classify(run)
            # Keep raw output separately on failure; successful JSON is already stored.
            raw = run.pop("stdout")
            row = {"tier": tier, "scenario": scenario, "result": result, "execution": run}
            if result.get("mode") != "fake_pipeline":
                row["unparsed_stdout"] = raw[-8192:]
            records.append(row)
            report["summary"] = summarize(records)
            output.write_text(json.dumps(report, indent=2) + "\n")
            print(f"{tier:8s} {scenario:28s} {result['status']:28s} contract={result.get('pipeline_contract_passed')}", flush=True)
    if args.probe_oom:
        probe = run_container(image, 64 * 1024 ** 2, ["-c", "x = bytearray(256 * 1024 * 1024); x[::4096] = b'x' * (len(x) // 4096)"], mount_project=False)
        report["oom_fault_probe"] = {"memory_bytes": 64 * 1024 ** 2, "scored_task": False, "oom_detected": probe["state"].get("OOMKilled", False), "execution": probe}
    report["summary"] = summarize(records)
    output.write_text(json.dumps(report, indent=2) + "\n")
    passed = all(r["result"].get("pipeline_contract_passed") for r in records)
    if args.probe_oom:
        passed = passed and report["oom_fault_probe"]["oom_detected"]
    print(json.dumps(report["summary"], indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
