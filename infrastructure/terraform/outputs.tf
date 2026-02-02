output "sagemaker_execution_role_arn" {
  value       = aws_iam_role.sagemaker_execution_role.arn
  description = "ARN of the SageMaker execution role"
}

