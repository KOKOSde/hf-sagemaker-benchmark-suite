# Example Dockerfile for a SageMaker-compatible TGI container.
# This is useful if you want to push a custom image to ECR and deploy via SageMaker.
#
# For many users, using the official Hugging Face image URI (via sagemaker SDK) is simpler.

FROM ghcr.io/huggingface/text-generation-inference:3.3.5

COPY sagemaker-entrypoint.sh /usr/local/bin/sagemaker-entrypoint.sh
RUN chmod +x /usr/local/bin/sagemaker-entrypoint.sh

ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/sagemaker-entrypoint.sh"]

