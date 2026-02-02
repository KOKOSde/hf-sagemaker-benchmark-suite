# hf-sagemaker-benchmark-suite

Deploy Hugging Face models to **AWS SageMaker** and run repeatable **latency/throughput/cost** benchmarks.

> Important: this repository includes scripts to **generate** benchmark results. It does **not** ship fabricated numbers.
> To produce real numbers, you must run the benchmarks against your own AWS account and endpoint.

## Quickstart: deploy any model to SageMaker in ~5 minutes

1) Create a Python environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

2) Deploy a model (example: `distilbert-base-uncased`, task = `text-classification`):

```bash
python deploy/deploy_any_model.py \
  --deployment-type hf-inference \
  --model-id distilbert/distilbert-base-uncased-finetuned-sst-2-english \
  --task text-classification \
  --instance-type ml.m5.xlarge \
  --region us-east-1 \
  --endpoint-name hf-bench-distilbert-sst2
```

3) Run latency and throughput benchmarks:

```bash
python benchmark/latency_benchmark.py \
  --endpoint-name hf-bench-distilbert-sst2 \
  --region us-east-1 \
  --payload-json '{\"inputs\": \"I love this library.\"}' \
  --n 200 --concurrency 4 --warmup 20 \
  --output results/benchmark_results.json

python benchmark/throughput_benchmark.py \
  --endpoint-name hf-bench-distilbert-sst2 \
  --region us-east-1 \
  --payload-json '{\"inputs\": \"I love this library.\"}' \
  --duration-seconds 60 --concurrency 8 --warmup 20 \
  --output results/benchmark_results.json
```

4) Generate a chart from your results:

```bash
python results/generate_chart.py --input results/benchmark_results.json --output results/comparison_chart.png
```

## Contents

- `deploy/`
  - `deploy_any_model.py`: deploy either:
    - **HF Inference Toolkit** (good for classic Transformers pipelines), or
    - **TGI** image (better for LLM serving, optional)
- `benchmark/`
  - `latency_benchmark.py`: p50/p95/p99 latency
  - `throughput_benchmark.py`: requests/sec, error rate
  - `cost_calculator.py`: monthly cost estimate
- `infrastructure/`
  - `terraform/`: minimal IAM role scaffolding for SageMaker
  - `Dockerfile`: example “bring-your-own-container” Dockerfile for SageMaker using TGI base image
- `results/`
  - `benchmark_results.json`: output file written by benchmarks (starts empty)
  - `comparison_chart.png`: generated chart (starts as a placeholder)

## Cost comparison table

Use:

```bash
python benchmark/cost_calculator.py --hourly-usd 1.0 --hours-per-month 730
```

Then compare:
- SageMaker instance hourly cost
- EC2 instance hourly cost
- Optional: storage + data transfer (not included by default)

## My Hugging Face contributions

- Transformers PR (merged): `https://github.com/huggingface/transformers/pull/43610`
- Datasets PR (open): `https://github.com/huggingface/datasets/pull/7973`
- TGI PR (open): `https://github.com/huggingface/text-generation-inference/pull/3352`

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

