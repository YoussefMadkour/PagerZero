"""Generate fake incident data files for each demo scenario.

Each scenario writes four files into src/pagerzero/data/scenarios/<name>/:
  - meta.json:    service_name, alert_summary
  - logs.txt:     ~8,000 log lines mixing normal traffic with anomalies
  - metrics.csv:  per-minute time series of cpu/memory/latency/etc.
  - deploys.json: deploy events in the 24h window before the incident

Run: uv run python scripts/generate_scenarios.py
"""

from __future__ import annotations

import csv
import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

OUT_ROOT = Path(__file__).parent.parent / "src" / "pagerzero" / "data" / "scenarios"

# Use a fixed seed so demos are deterministic — same data every time.
random.seed(42)


def iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


# ---------- Scenario A: Memory Leak ----------


def generate_scenario_a() -> None:
    out_dir = OUT_ROOT / "scenario_a_memory_leak"
    out_dir.mkdir(parents=True, exist_ok=True)

    incident_window_start = datetime(2026, 5, 1, 14, 0, tzinfo=UTC)
    deploy_time = incident_window_start - timedelta(minutes=47)
    burst_start = incident_window_start + timedelta(minutes=43)

    # --- meta ---
    (out_dir / "meta.json").write_text(
        json.dumps(
            {
                "service_name": "payment-service",
                "alert_summary": (
                    "payment-service P99 latency > 4s, error rate 847% above "
                    "baseline. Possible heap exhaustion."
                ),
            },
            indent=2,
        )
    )

    # --- logs.txt ~8000 lines ---
    lines: list[str] = []
    routes = ["/v1/charge", "/v1/refund", "/v1/customer", "/v1/webhook", "/health"]
    user_ids = [f"usr_{random.randint(10000, 99999)}" for _ in range(200)]

    # Generate per minute with budgeted line counts so the burst window is
    # always represented even if normal traffic is dense.
    t = incident_window_start - timedelta(minutes=60)
    end = burst_start + timedelta(minutes=20)
    while t < end:
        minutes_after_deploy = (t - deploy_time).total_seconds() / 60
        burst_offset_min = (t - burst_start).total_seconds() / 60
        in_burst = 0 <= burst_offset_min < 15

        # Normal request traffic — denser pre-burst, sparser during the storm
        normal_per_min = 30 if in_burst else 55
        for _ in range(normal_per_min):
            ts = t + timedelta(seconds=random.uniform(0, 60))
            route = random.choice(routes)
            user = random.choice(user_ids)
            latency_ms = random.randint(40, 180)
            status = 200 if random.random() > 0.005 else random.choice([400, 404, 502])
            lines.append(
                f"{iso(ts)} INFO  [http-nio-8080-exec-{random.randint(1, 32)}] "
                f"req_id=req_{random.randint(100000, 999999)} user={user} "
                f"{route} status={status} latency={latency_ms}ms"
            )

        # GC warnings: start ~12 min after deploy, escalate as heap fills
        if minutes_after_deploy > 12:
            gc_count = min(int((minutes_after_deploy - 12) / 4), 8)
            heap_used = min(2.0 + (minutes_after_deploy - 12) * 0.13, 7.9)
            for _ in range(gc_count):
                ts = t + timedelta(seconds=random.uniform(0, 60))
                pause_ms = int(400 + (heap_used - 2.0) * 200 + random.uniform(-50, 50))
                lines.append(
                    f"{iso(ts)} WARN  [gc] pause exceeded {pause_ms}ms "
                    f"(heap={heap_used:.1f}GB/8GB) generation=old"
                )

        # OOM burst: heap-exhaustion errors + upstream timeouts
        if in_burst:
            burst_count = random.randint(35, 55)
            for _ in range(burst_count):
                ts = t + timedelta(seconds=random.uniform(0, 60))
                kind = random.random()
                if kind < 0.5:
                    lines.append(
                        f"{iso(ts)} ERROR [http-nio-8080-exec-{random.randint(1, 32)}] "
                        f"java.lang.OutOfMemoryError: Java heap space\n"
                        f"\tat com.payco.session.SessionCache.put(SessionCache.java:84)\n"
                        f"\tat com.payco.auth.AuthFilter.doFilter(AuthFilter.java:142)\n"
                        f"\tat com.payco.payment.ChargeHandler.handle(ChargeHandler.java:67)"
                    )
                elif kind < 0.85:
                    lines.append(
                        f"{iso(ts)} ERROR [http-nio-8080-exec-{random.randint(1, 32)}] "
                        f"upstream timeout after 4000ms route=/v1/charge "
                        f"req_id=req_{random.randint(100000, 999999)}"
                    )
                else:
                    lines.append(
                        f"{iso(ts)} WARN  [gc] FULL GC pause 8200ms "
                        f"(heap=7.9GB/8GB) generation=tenured"
                    )

        t += timedelta(minutes=1)

    # Sort chronologically so the timeline reads naturally for the LLM
    lines.sort(key=lambda line: line[:30])

    (out_dir / "logs.txt").write_text("\n".join(lines) + "\n")

    # --- metrics.csv (per-minute, 2h window) ---
    rows: list[dict[str, str]] = []
    metrics_start = incident_window_start - timedelta(minutes=60)
    for i in range(120):
        t = metrics_start + timedelta(minutes=i)
        minutes_after_deploy = (t - deploy_time).total_seconds() / 60
        # Memory grows linearly post-deploy from 2.0 to 7.9 over 60 min
        if minutes_after_deploy < 0:
            memory = 2.0 + random.uniform(-0.05, 0.05)
        else:
            memory = min(2.0 + minutes_after_deploy * 0.10, 7.9) + random.uniform(-0.05, 0.05)

        # Latency flat until burst, then 35x spike
        burst_offset_min = (t - burst_start).total_seconds() / 60
        if burst_offset_min < 0:
            latency = 120 + random.uniform(-15, 15)
        else:
            latency = min(120 + burst_offset_min * 800, 4200) + random.uniform(-50, 50)

        # Error rate flat until burst, then explodes
        if burst_offset_min < 0:
            error_rate = 0.002 + random.uniform(-0.001, 0.001)
        else:
            error_rate = min(0.002 + burst_offset_min * 0.18, 0.85)

        cpu = 35 + random.uniform(-5, 5) + max(0, burst_offset_min) * 1.5
        cpu = min(cpu, 95)
        throughput = max(50 - max(0, burst_offset_min) * 2, 5) + random.uniform(-3, 3)

        rows.append(
            {
                "timestamp": iso(t),
                "cpu_percent": f"{cpu:.2f}",
                "memory_gb": f"{memory:.2f}",
                "latency_ms": f"{latency:.1f}",
                "error_rate": f"{error_rate:.4f}",
                "throughput_rps": f"{throughput:.2f}",
            }
        )

    with (out_dir / "metrics.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # --- deploys.json (24h window) ---
    deploys = [
        {
            "timestamp": iso(deploy_time),
            "commit_sha": "abc123f",
            "author": "alice@payco.network",
            "message": "Optimized session caching for faster auth",
            "files_changed": [
                "src/com/payco/session/SessionCache.java",
                "src/com/payco/session/SessionLifecycleHook.java",
            ],
            "diff_summary": (
                "SessionCache.put: removed evict-on-expiry check. "
                "SessionLifecycleHook: removed cache.cleanup() call."
            ),
        },
        {
            "timestamp": iso(deploy_time - timedelta(hours=6)),
            "commit_sha": "9b2e4a1",
            "author": "bob@payco.network",
            "message": "Bump kotlin-stdlib 1.9.22 -> 1.9.24",
            "files_changed": ["build.gradle.kts"],
            "diff_summary": "Patch version bump, no logic changes.",
        },
        {
            "timestamp": iso(deploy_time - timedelta(hours=14)),
            "commit_sha": "4d77f02",
            "author": "carol@payco.network",
            "message": "Add structured logging to webhook handler",
            "files_changed": ["src/com/payco/webhook/WebhookHandler.java"],
            "diff_summary": "Add SLF4J markers, no behavioral changes.",
        },
    ]
    (out_dir / "deploys.json").write_text(json.dumps(deploys, indent=2))

    print(
        f"  scenario_a_memory_leak: {len(lines)} log lines, "
        f"{len(rows)} metric points, {len(deploys)} deploys"
    )


# ---------- Scenario B: Database connection pool exhaustion ----------


def generate_scenario_b() -> None:
    out_dir = OUT_ROOT / "scenario_b_pool_exhaust"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Flash-sale traffic spike at 14:00 exhausts the 50-conn pool by 14:08.
    incident_window_start = datetime(2026, 5, 1, 14, 0, tzinfo=UTC)
    burst_start = incident_window_start + timedelta(minutes=8)

    (out_dir / "meta.json").write_text(
        json.dumps(
            {
                "service_name": "checkout-service",
                "alert_summary": (
                    "checkout-service connection pool saturated, P99 latency "
                    "> 8s, traffic 340% above baseline."
                ),
            },
            indent=2,
        )
    )

    lines: list[str] = []
    routes = ["/v1/checkout", "/v1/cart", "/v1/inventory", "/health"]
    user_ids = [f"usr_{random.randint(10000, 99999)}" for _ in range(500)]

    t = incident_window_start - timedelta(minutes=30)
    end = burst_start + timedelta(minutes=30)
    while t < end:
        burst_offset_min = (t - burst_start).total_seconds() / 60
        in_burst = burst_offset_min >= 0
        traffic_multiplier = 3.4 if in_burst else 1.0
        normal_per_min = int(40 * traffic_multiplier)

        for _ in range(normal_per_min):
            ts = t + timedelta(seconds=random.uniform(0, 60))
            route = random.choice(routes)
            user = random.choice(user_ids)
            if in_burst and random.random() < 0.45:
                # Pool-exhaustion errors dominate in the burst
                lines.append(
                    f"{iso(ts)} ERROR [hikari-pool] connection timeout "
                    f"waiting for available connection from pool "
                    f"(active=50/50, waiting={random.randint(40, 200)}) "
                    f"route={route} user={user}"
                )
            else:
                latency = (
                    random.randint(40, 180)
                    if not in_burst
                    else random.randint(2000, 9000)
                )
                lines.append(
                    f"{iso(ts)} INFO  [http-nio-8080-exec-{random.randint(1, 32)}] "
                    f"req_id=req_{random.randint(100000, 999999)} user={user} "
                    f"{route} status=200 latency={latency}ms"
                )

        t += timedelta(minutes=1)

    lines.sort(key=lambda line: line[:30])
    (out_dir / "logs.txt").write_text("\n".join(lines) + "\n")

    rows: list[dict[str, str]] = []
    metrics_start = incident_window_start - timedelta(minutes=30)
    for i in range(90):
        t = metrics_start + timedelta(minutes=i)
        burst_offset_min = (t - burst_start).total_seconds() / 60
        in_burst = burst_offset_min >= 0

        cpu = (45 if in_burst else 30) + random.uniform(-3, 3)
        memory = 3.2 + random.uniform(-0.05, 0.05)
        latency = (
            random.uniform(80, 140)
            if not in_burst
            else min(80 + burst_offset_min * 1200, 8500) + random.uniform(-200, 200)
        )
        error_rate = (
            0.001 + random.uniform(-0.0005, 0.0005)
            if not in_burst
            else min(0.005 + burst_offset_min * 0.05, 0.42)
        )
        if not in_burst:
            throughput = 38 + random.uniform(-3, 3)
        elif burst_offset_min < 5:
            throughput = 130 + random.uniform(-15, 15)
        else:
            throughput = 60 + random.uniform(-10, 10)

        rows.append(
            {
                "timestamp": iso(t),
                "cpu_percent": f"{cpu:.2f}",
                "memory_gb": f"{memory:.2f}",
                "latency_ms": f"{latency:.1f}",
                "error_rate": f"{error_rate:.4f}",
                "throughput_rps": f"{throughput:.2f}",
            }
        )

    with (out_dir / "metrics.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # No suspicious deploys — this is a pure traffic event
    deploys = [
        {
            "timestamp": iso(incident_window_start - timedelta(hours=8)),
            "commit_sha": "5fa9e22",
            "author": "dan@payco.network",
            "message": "Improve checkout error message copy",
            "files_changed": ["src/com/payco/checkout/Errors.java"],
            "diff_summary": "Reword 4 user-facing error messages. No logic.",
        },
        {
            "timestamp": iso(incident_window_start - timedelta(hours=20)),
            "commit_sha": "1c33ab8",
            "author": "eve@payco.network",
            "message": "Update README badges",
            "files_changed": ["README.md"],
            "diff_summary": "Documentation only.",
        },
    ]
    (out_dir / "deploys.json").write_text(json.dumps(deploys, indent=2))
    print(
        f"  scenario_b_pool_exhaust: {len(lines)} log lines, "
        f"{len(rows)} metric points, {len(deploys)} deploys"
    )


# ---------- Scenario C: Cascading failure ----------


def generate_scenario_c() -> None:
    out_dir = OUT_ROOT / "scenario_c_cascade"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Config change disabled circuit breaker at 14:32; recommendation service
    # slowdown at 14:35; product service retry-storms by 14:40; full outage 14:43.
    incident_window_start = datetime(2026, 5, 1, 14, 0, tzinfo=UTC)
    config_change_time = incident_window_start + timedelta(minutes=32)
    rec_slowdown_time = incident_window_start + timedelta(minutes=35)
    cascade_time = incident_window_start + timedelta(minutes=40)

    (out_dir / "meta.json").write_text(
        json.dumps(
            {
                "service_name": "storefront",
                "alert_summary": (
                    "storefront fully down, thread pool exhausted across "
                    "product-service. Multiple downstream services degraded."
                ),
            },
            indent=2,
        )
    )

    lines: list[str] = []
    user_ids = [f"usr_{random.randint(10000, 99999)}" for _ in range(300)]

    t = incident_window_start
    end = cascade_time + timedelta(minutes=20)
    while t < end:
        # Phase 1: pre-config baseline
        if t < config_change_time:
            for _ in range(40):
                ts = t + timedelta(seconds=random.uniform(0, 60))
                lines.append(
                    f"{iso(ts)} INFO  [product-svc] GET /products "
                    f"user={random.choice(user_ids)} status=200 "
                    f"latency={random.randint(60, 120)}ms"
                )

        # Phase 2: config change ambient + recommendation slowdown begins
        elif t < cascade_time:
            for _ in range(35):
                ts = t + timedelta(seconds=random.uniform(0, 60))
                lines.append(
                    f"{iso(ts)} INFO  [product-svc] GET /products "
                    f"user={random.choice(user_ids)} status=200 "
                    f"latency={random.randint(60, 150)}ms"
                )
            if t >= rec_slowdown_time:
                for _ in range(15):
                    ts = t + timedelta(seconds=random.uniform(0, 60))
                    lines.append(
                        f"{iso(ts)} WARN  [rec-svc] slow response "
                        f"latency={random.randint(2500, 5500)}ms "
                        f"endpoint=/v1/recommendations/personalized"
                    )

        # Phase 3: cascade — retry storm in product-svc, thread pool exhaustion
        else:
            cascade_min = (t - cascade_time).total_seconds() / 60
            for _ in range(int(80 + cascade_min * 5)):
                ts = t + timedelta(seconds=random.uniform(0, 60))
                kind = random.random()
                if kind < 0.4:
                    lines.append(
                        f"{iso(ts)} ERROR [product-svc] retrying call to rec-svc "
                        f"(attempt={random.randint(1, 8)}/8) timeout=4000ms "
                        f"upstream=rec-svc.prod.svc"
                    )
                elif kind < 0.75:
                    lines.append(
                        f"{iso(ts)} ERROR [product-svc] thread pool exhausted "
                        f"active=200/200 queue_depth={random.randint(800, 3000)} "
                        f"rejected_requests=true"
                    )
                else:
                    lines.append(
                        f"{iso(ts)} ERROR [product-svc] GET /products "
                        f"user={random.choice(user_ids)} status=503 "
                        f"latency=4000ms reason=upstream_timeout"
                    )

        t += timedelta(minutes=1)

    lines.sort(key=lambda line: line[:30])
    (out_dir / "logs.txt").write_text("\n".join(lines) + "\n")

    rows: list[dict[str, str]] = []
    for i in range(75):
        t = incident_window_start + timedelta(minutes=i)
        cascade_min = (t - cascade_time).total_seconds() / 60
        in_cascade = cascade_min >= 0

        cpu = (
            (40 if t < rec_slowdown_time else 55) + random.uniform(-3, 3)
            if not in_cascade
            else min(60 + cascade_min * 4, 96) + random.uniform(-3, 3)
        )
        memory = 4.5 + random.uniform(-0.1, 0.1)
        latency = (
            (random.uniform(70, 140) if t < rec_slowdown_time else random.uniform(180, 600))
            if not in_cascade
            else min(600 + cascade_min * 600, 9000) + random.uniform(-100, 100)
        )
        error_rate = (
            0.001 + random.uniform(-0.0005, 0.0005)
            if not in_cascade
            else min(0.01 + cascade_min * 0.07, 0.92)
        )
        throughput = (
            85 + random.uniform(-5, 5)
            if not in_cascade
            else max(85 - cascade_min * 6, 8) + random.uniform(-3, 3)
        )

        rows.append(
            {
                "timestamp": iso(t),
                "cpu_percent": f"{cpu:.2f}",
                "memory_gb": f"{memory:.2f}",
                "latency_ms": f"{latency:.1f}",
                "error_rate": f"{error_rate:.4f}",
                "throughput_rps": f"{throughput:.2f}",
            }
        )

    with (out_dir / "metrics.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # The "deploy" here is a config push, not a code change
    deploys = [
        {
            "timestamp": iso(config_change_time),
            "commit_sha": "f4e8a91",
            "author": "frank@payco.network",
            "message": "Disable circuit breaker on product->rec calls (temp)",
            "files_changed": ["config/resilience.yaml"],
            "diff_summary": (
                "circuit_breaker.product_to_rec: enabled=false. "
                "Temporary while debugging unrelated rec-svc latency."
            ),
        },
        {
            "timestamp": iso(incident_window_start - timedelta(hours=4)),
            "commit_sha": "2a9c5d3",
            "author": "grace@payco.network",
            "message": "Add /products/featured endpoint",
            "files_changed": ["src/com/payco/product/FeaturedHandler.java"],
            "diff_summary": "New endpoint with its own dedicated thread pool. Isolated.",
        },
    ]
    (out_dir / "deploys.json").write_text(json.dumps(deploys, indent=2))
    print(
        f"  scenario_c_cascade: {len(lines)} log lines, "
        f"{len(rows)} metric points, {len(deploys)} deploys"
    )


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    print("Generating scenarios into", OUT_ROOT)
    generate_scenario_a()
    generate_scenario_b()
    generate_scenario_c()
    print("Done.")


if __name__ == "__main__":
    main()
