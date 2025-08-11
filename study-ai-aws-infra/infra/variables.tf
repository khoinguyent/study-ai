variable "region" {
  type    = string
  default = "ap-southeast-1"
}

variable "project" {
  type    = string
  default = "studyai"
}

variable "env" {
  type    = string
  default = "dev"
}

# Choose CPU architecture for EC2 (x86_64 or ARM/Graviton)
variable "use_arm" {
  type    = bool
  default = true # true = t4g (ARM), false = t3 (x86)
}

variable "ec2_instance_type_arm" {
  type    = string
  default = "t4g.micro"  # Free Tier eligible
}

variable "ec2_instance_type_x86" {
  type    = string
  default = "t3.micro"   # Free Tier eligible
}

variable "allow_ssh_cidr" {
  description = "Your public IP/CIDR for SSH (e.g., 203.0.113.10/32). CHANGE THIS."
  type        = string
  default     = "0.0.0.0/0"
}

variable "enable_sagemaker" {
  type    = bool
  default = false
}

variable "tags" {
  type    = map(string)
  default = { Project = "StudyAI", Environment = "dev" }
}
