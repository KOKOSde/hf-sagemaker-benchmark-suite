from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Any, Optional

import boto3


@dataclass(frozen=True)
class DeployArgs:
    deployment_type: str
    model_id: str
    task: Optional[str]
    region: str
    role_arn: Optional[str]
    endpoint_name: str
    instance_type: str
    initial_instance_count: int
    hf_model_revision: Optional[str]
    hf_token_env: Optional[str]
    # TGI options
    tgi_version: str
    sm_num_gpus: Optional[int]
    hf_model_quantize: Optional[str]
    hf_model_trust_remote_code: bool
    # Misc
    dry_run: bool


def _default_endpoint_name(model_id: str) -> str:
    safe = model_id.replace("/", "-").replace(".", "-")
    return f"hf-bench-{safe}-{int(time.time())}"


def _get_sagemaker_role(role_arn: Optional[str], region: str) -> str:
    """
    Prefer explicit role ARN. If not provided, try to resolve a common role name.
    """
    if role_arn:
        return role_arn
    # Best-effort fallback: try a role named 'sagemaker_execution_role'
    iam = boto3.client("iam", region_name=region)
    return iam.get_role(RoleName="sagemaker_execution_role")["Role"]["Arn"]


def deploy_hf_inference(args: DeployArgs) -> str:
    """
    Deploy using the SageMaker Hugging Face Inference Toolkit container (classic Transformers pipelines).
    This is the closest thing to "any model" as long as you provide a compatible `--task`.
    """
    if not args.task:
        raise ValueError("--task is required for --deployment-type=hf-inference")

    import sagemaker
    from sagemaker.huggingface import HuggingFaceModel

    role = _get_sagemaker_role(args.role_arn, args.region)
    sess = sagemaker.Session(boto_session=boto3.Session(region_name=args.region))

    env: dict[str, str] = {
        "HF_MODEL_ID": args.model_id,
        "HF_TASK": args.task,
    }
    if args.hf_model_revision:
        env["HF_MODEL_REVISION"] = args.hf_model_revision
    if args.hf_token_env:
        token = os.environ.get(args.hf_token_env)
        if token:
            env["HF_TOKEN"] = token

    model = HuggingFaceModel(
        transformers_version="4.46.0",
        pytorch_version="2.4.0",
        py_version="py310",
        env=env,
        role=role,
        sagemaker_session=sess,
    )

    if args.dry_run:
        print(json.dumps({"mode": "hf-inference", "env": env, "role": role, "endpoint_name": args.endpoint_name}, indent=2))
        return args.endpoint_name

    predictor = model.deploy(
        initial_instance_count=args.initial_instance_count,
        instance_type=args.instance_type,
        endpoint_name=args.endpoint_name,
    )
    return predictor.endpoint_name


def deploy_tgi(args: DeployArgs) -> str:
    """
    Deploy using the official TGI image URI (best for LLM-style serving).
    """
    import sagemaker
    from sagemaker.huggingface import HuggingFaceModel, get_huggingface_llm_image_uri

    role = _get_sagemaker_role(args.role_arn, args.region)
    sess = sagemaker.Session(boto_session=boto3.Session(region_name=args.region))

    env: dict[str, str] = {"HF_MODEL_ID": args.model_id}
    if args.hf_model_revision:
        env["HF_MODEL_REVISION"] = args.hf_model_revision
    if args.sm_num_gpus is not None:
        # SageMaker expects this as JSON-encoded int
        env["SM_NUM_GPUS"] = json.dumps(args.sm_num_gpus)
    if args.hf_model_quantize:
        env["HF_MODEL_QUANTIZE"] = args.hf_model_quantize
    if args.hf_model_trust_remote_code:
        env["HF_MODEL_TRUST_REMOTE_CODE"] = "true"
    if args.hf_token_env:
        token = os.environ.get(args.hf_token_env)
        if token:
            env["HF_TOKEN"] = token

    image_uri = get_huggingface_llm_image_uri("huggingface", version=args.tgi_version)
    model = HuggingFaceModel(image_uri=image_uri, env=env, role=role, sagemaker_session=sess)

    if args.dry_run:
        print(json.dumps({"mode": "tgi", "image_uri": image_uri, "env": env, "role": role, "endpoint_name": args.endpoint_name}, indent=2))
        return args.endpoint_name

    predictor = model.deploy(
        initial_instance_count=args.initial_instance_count,
        instance_type=args.instance_type,
        endpoint_name=args.endpoint_name,
        container_startup_health_check_timeout=300,
    )
    return predictor.endpoint_name


def main() -> None:
    p = argparse.ArgumentParser(description="Deploy a Hugging Face model to SageMaker for benchmarking.")
    p.add_argument("--deployment-type", choices=["hf-inference", "tgi"], required=True)
    p.add_argument("--model-id", required=True, help="Hugging Face model ID (e.g. distilbert/distilbert-base-uncased)")
    p.add_argument("--task", default=None, help="Pipeline task for hf-inference (e.g. text-classification, question-answering)")
    p.add_argument("--region", default=os.environ.get("AWS_REGION") or "us-east-1")
    p.add_argument("--role-arn", default=None, help="IAM role ARN for SageMaker execution (optional)")
    p.add_argument("--endpoint-name", default=None, help="SageMaker endpoint name (optional)")
    p.add_argument("--instance-type", default="ml.m5.xlarge")
    p.add_argument("--initial-instance-count", type=int, default=1)
    p.add_argument("--hf-model-revision", default=None)
    p.add_argument(
        "--hf-token-env",
        default=None,
        help="Name of an environment variable that contains a HF token (e.g. HF_TOKEN).",
    )

    # TGI options
    p.add_argument("--tgi-version", default="3.3.5")
    p.add_argument("--sm-num-gpus", type=int, default=None)
    p.add_argument("--hf-model-quantize", default=None)
    p.add_argument("--hf-model-trust-remote-code", action="store_true")

    p.add_argument("--dry-run", action="store_true")

    ns = p.parse_args()
    endpoint_name = ns.endpoint_name or _default_endpoint_name(ns.model_id)
    args = DeployArgs(
        deployment_type=ns.deployment_type,
        model_id=ns.model_id,
        task=ns.task,
        region=ns.region,
        role_arn=ns.role_arn,
        endpoint_name=endpoint_name,
        instance_type=ns.instance_type,
        initial_instance_count=ns.initial_instance_count,
        hf_model_revision=ns.hf_model_revision,
        hf_token_env=ns.hf_token_env,
        tgi_version=ns.tgi_version,
        sm_num_gpus=ns.sm_num_gpus,
        hf_model_quantize=ns.hf_model_quantize,
        hf_model_trust_remote_code=ns.hf_model_trust_remote_code,
        dry_run=ns.dry_run,
    )

    print(json.dumps({"deploy_args": asdict(args)}, indent=2))

    if args.deployment_type == "hf-inference":
        endpoint = deploy_hf_inference(args)
    else:
        endpoint = deploy_tgi(args)

    print(json.dumps({"endpoint_name": endpoint}, indent=2))


if __name__ == "__main__":
    main()

