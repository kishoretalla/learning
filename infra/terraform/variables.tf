variable "app_name" {
  description = "Application name prefix for AWS resources."
  type        = string
  default     = "research-notebook"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region for deployment."
  type        = string
  default     = "us-east-1"
}

variable "desired_count" {
  description = "Number of tasks to run per ECS service."
  type        = number
  default     = 1
}

variable "frontend_container_port" {
  description = "Internal frontend container port exposed through nginx."
  type        = number
  default     = 8080
}

variable "backend_container_port" {
  description = "Internal backend container port."
  type        = number
  default     = 8000
}

variable "frontend_image_tag" {
  description = "Frontend image tag to deploy."
  type        = string
  default     = "latest"
}

variable "backend_image_tag" {
  description = "Backend image tag to deploy."
  type        = string
  default     = "latest"
}

variable "database_url" {
  description = "Database URL for the backend task. Replace the default with a managed database before production use."
  type        = string
  default     = "sqlite:///./research-notebook.db"
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Google Gemini API key used by the backend."
  type        = string
  default     = ""
  sensitive   = true
}

variable "github_token" {
  description = "Optional GitHub token used for Colab gist generation."
  type        = string
  default     = ""
  sensitive   = true
}
