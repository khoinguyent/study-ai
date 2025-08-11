# Study AI AWS Infrastructure

This repository contains Terraform configuration for deploying AWS infrastructure to support Study AI applications.

## Project Structure

```
study-ai-aws-infra/
├─ README.md
├─ .gitignore
├─ Makefile
├─ infra/
│  ├─ main.tf
│  ├─ variables.tf
│  ├─ outputs.tf
│  ├─ user_data.sh
│  └─ terraform.tfvars
```

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- Make (optional, for using the Makefile)

## Quick Start

1. **Navigate to the infrastructure directory:**
   ```bash
   cd infra
   ```

2. **Initialize Terraform:**
   ```bash
   terraform init
   ```

3. **Review the plan:**
   ```bash
   terraform plan
   ```

4. **Apply the configuration:**
   ```bash
   terraform apply
   ```

## Using the Makefile

The project includes a Makefile for common operations:

- `make init` - Initialize Terraform
- `make plan` - Show Terraform plan
- `make apply` - Apply Terraform configuration
- `make destroy` - Destroy infrastructure
- `make clean` - Clean up local files

## Infrastructure Components

The Terraform configuration creates:

- VPC with public and private subnets
- EC2 instances for application servers
- Security groups for network access control
- Load balancer for traffic distribution
- Auto Scaling Group for high availability

## Configuration

Edit `infra/terraform.tfvars` to customize:
- AWS region
- Instance types
- Subnet CIDR blocks
- Environment-specific variables

## Security Notes

- Never commit sensitive information like AWS access keys
- Use IAM roles and policies with least privilege
- Regularly rotate credentials and review access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `terraform plan`
5. Submit a pull request

## License

This project is licensed under the MIT License.
