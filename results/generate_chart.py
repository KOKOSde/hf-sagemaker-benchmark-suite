from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Generate a simple comparison chart from benchmark_results.json.")
    p.add_argument("--input", default="results/benchmark_results.json")
    p.add_argument("--output", default="results/comparison_chart.png")
    args = p.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    results = data.get("results", [])

    # Lazy import so the repo stays usable without matplotlib unless charting is requested
    import matplotlib.pyplot as plt  # type: ignore

    if not results:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.axis("off")
        ax.text(0.5, 0.5, "No results yet. Run benchmarks to generate data.", ha="center", va="center")
        fig.tight_layout()
        fig.savefig(args.output, dpi=150)
        return

    # Plot p95 latency for the last latency run (if any)
    latency_runs = [r for r in results if r.get("kind") == "latency"]
    if not latency_runs:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.axis("off")
        ax.text(0.5, 0.5, "No latency results found.", ha="center", va="center")
        fig.tight_layout()
        fig.savefig(args.output, dpi=150)
        return

    last = latency_runs[-1]
    p50 = last["summary"]["p50_ms"]
    p95 = last["summary"]["p95_ms"]
    p99 = last["summary"]["p99_ms"]
    label = last.get("endpoint_name", "endpoint")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(["p50", "p95", "p99"], [p50, p95, p99])
    ax.set_ylabel("Latency (ms)")
    ax.set_title(f"Latency percentiles for {label}")
    fig.tight_layout()
    fig.savefig(args.output, dpi=150)


if __name__ == "__main__":
    main()

