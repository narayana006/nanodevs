"""Read cgroup v2 accounting, including file-backed model pages."""
from pathlib import Path
import platform

TIERS = {"lite": 2 * 1024 ** 3, "standard": 4 * 1024 ** 3}


def snapshot(root=Path("/sys/fs/cgroup")):
    root = Path(root)
    result = {"platform": platform.platform(), "machine": platform.machine(), "verified": False}
    for name in ("memory.max", "memory.swap.max", "memory.peak", "memory.current", "memory.events", "cpu.max", "cpu.stat"):
        path = root / name
        result[name] = path.read_text().strip() if path.is_file() else None
    return result


def verify_limits(tier, root=Path("/sys/fs/cgroup")):
    result = snapshot(root)
    if result["memory.max"] != str(TIERS[tier]):
        raise RuntimeError("Expected the exact Docker tier memory limit")
    if result["memory.swap.max"] != "0":
        raise RuntimeError("Swap must be disabled for scored execution")
    try:
        quota, period = map(int, result["cpu.max"].split())
    except (ValueError, TypeError, AttributeError) as error:
        raise RuntimeError("Finite cgroup CPU quota required") from error
    if quota / period != 2:
        raise RuntimeError("Expected a 2-CPU quota")
    result["verified"] = True
    return result
