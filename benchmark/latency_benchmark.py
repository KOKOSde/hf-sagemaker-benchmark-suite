from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from benchmark.common import SageMakerRuntimeClient, now_ms, summarize_latencies, write_results


def _payload_bytes(payload_json: str) -> bytes:
    # validate JSON
    json.loads(payload_json)
    return payload_json.encode("utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description="Measure SageMaker endpoint latency (p50/p95/p99).")
    p.add_argument("--endpoint-name", required=True)
    p.add_argument("--region", required=True)
    p.add_argument("--payload-json", required=True, help="JSON string sent to the endpoint Body")
    p.add_argument("--content-type", default="application/json")
    p.add_argument("--accept", default="application/json")
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--concurrency", type=int, default=4)
    p.add_argument("--warmup", type=int, default=20)
    p.add_argument("--output", default="results/benchmark_results.json")
    args = p.parse_args()

    client = SageMakerRuntimeClient(region=args.region)
    payload = _payload_bytes(args.payload_json)

    # Warmup
    for _ in range(max(args.warmup, 0)):
        try:
            client.invoke(args.endpoint_name, payload, content_type=args.content_type, accept=args.accept)
        except Exception:
            pass

    latencies: list[float] = []
    errors = 0

    def one() -> float:
        t0 = now_ms()
        client.invoke(args.endpoint_name, payload, content_type=args.content_type, accept=args.accept)
        return now_ms() - t0

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = [ex.submit(one) for _ in range(args.n)]
        for f in as_completed(futures):
            try:
                latencies.append(f.result())
            except Exception:
                errors += 1

    summary = summarize_latencies(latencies, concurrency=args.concurrency, error_count=errors)
    record: dict[str, Any] = {
        "kind": "latency",
        "endpoint_name": args.endpoint_name,
        "region": args.region,
        "summary": summary.__dict__,
    }
    write_results(args.output, record)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()

