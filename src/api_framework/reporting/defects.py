import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

DOMAINS = {"authentication", "documents", "persistence", "contracts", "framework", "public-apis"}


def failure_receipt(node_id: str, domain: str, phase: str, duration: float) -> dict:
    if domain not in DOMAINS or phase not in {"setup", "call", "teardown"}:
        raise ValueError("Use a supported defect domain and test phase")
    # Parameter values can be credentials: hash the complete ID, never store its parameters.
    case = re.sub(r"[^A-Za-z0-9_./:-]", "_", node_id.split("[")[0])
    return {
        "schema_version": 1,
        "case": case,
        "case_hash": hashlib.sha256(node_id.encode()).hexdigest()[:16],
        "domain": domain,
        "phase": phase,
        "outcome": "failed",
        "duration_seconds": round(max(0, duration), 3),
        "observed_at": datetime.now(UTC).isoformat(),
        "classification": "untriaged",
        "rca_status": "unknown",
    }


def write_receipt(root: Path, run_id: str, worker: str, receipt: dict) -> Path:
    if not re.fullmatch(r"[a-f0-9]{32}", run_id) or not re.fullmatch(r"(?:main|gw[0-9]+)", worker):
        raise ValueError("Invalid report run or worker identity")
    folder = root / run_id / worker / receipt["domain"]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{receipt['case_hash']}-{receipt['phase']}.json"
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    path.chmod(0o600)
    return path
