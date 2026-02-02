variable "aws_region" {
  type        = string
  description = "AWS region"
  default     = "us-east-1"
}

variable "sagemaker_role_name" {
  type        = string
  description = "Name of the SageMaker execution role"
  default     = "sagemaker_execution_role"
}

