"""Load scenario fixtures from disk into IncidentInput models."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from pagerzero.schemas import Deployment, IncidentInput, MetricPoint

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


def load_scenario(scenario_name: str) -> IncidentInput:
    """Read logs.txt + metrics.csv + deploys.json + meta.json for a scenario."""
    base = SCENARIOS_DIR / scenario_name
    if not base.is_dir():
        raise FileNotFoundError(f"Scenario directory not found: {base}")

    meta = json.loads((base / "meta.json").read_text())
    logs = (base / "logs.txt").read_text()

    with (base / "metrics.csv").open() as f:
        reader = csv.DictReader(f)
        metrics = [
            MetricPoint(
                timestamp=datetime.fromisoformat(row["timestamp"]),
                cpu_percent=float(row["cpu_percent"]),
                memory_gb=float(row["memory_gb"]),
                latency_ms=float(row["latency_ms"]),
                error_rate=float(row["error_rate"]),
                throughput_rps=float(row["throughput_rps"]),
            )
            for row in reader
        ]

    deploys_raw = json.loads((base / "deploys.json").read_text())
    deployments = [
        Deployment(
            timestamp=datetime.fromisoformat(d["timestamp"]),
            commit_sha=d["commit_sha"],
            author=d["author"],
            message=d["message"],
            files_changed=d["files_changed"],
            diff_summary=d["diff_summary"],
        )
        for d in deploys_raw
    ]

    return IncidentInput(
        scenario=scenario_name,
        service_name=meta["service_name"],
        alert_summary=meta["alert_summary"],
        logs=logs,
        metrics=metrics,
        deployments=deployments,
    )


def available_scenarios() -> list[str]:
    return sorted(d.name for d in SCENARIOS_DIR.iterdir() if d.is_dir())
