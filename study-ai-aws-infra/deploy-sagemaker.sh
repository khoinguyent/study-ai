#!/bin/bash
# Deploy SageMaker infrastructure for Ollama models

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/infra"
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check Terraform version
    TF_VERSION=$(terraform version -json | jq -r '.terraform_version')
    print_status "Terraform version: $TF_VERSION"
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials are not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_warning "jq is not installed. Some features may not work properly."
    fi
    
    print_status "Prerequisites check passed!"
}

# Navigate to infrastructure directory
navigate_to_infra() {
    print_status "Navigating to infrastructure directory..."
    cd "$INFRA_DIR"
    
    if [ ! -f "main.tf" ]; then
        print_error "Infrastructure directory not found or main.tf missing"
        exit 1
    fi
    
    print_status "Current directory: $(pwd)"
}

# Initialize Terraform
init_terraform() {
    print_status "Initializing Terraform..."
    terraform init
    print_status "Terraform initialized successfully"
}

# Plan Terraform deployment
plan_deployment() {
    print_status "Planning Terraform deployment..."
    
    # Create plan file
    terraform plan -var="enable_sagemaker=true" -var="env=$ENVIRONMENT" -out=tfplan
    
    print_status "Terraform plan created successfully"
    print_warning "Review the plan above before proceeding"
    
    read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled by user"
        exit 0
    fi
}

# Apply Terraform deployment
apply_deployment() {
    print_status "Applying Terraform deployment..."
    
    # Apply the plan
    terraform apply tfplan
    
    print_status "Terraform deployment completed successfully"
}

# Display deployment information
display_deployment_info() {
    print_header "Deployment Information"
    
    print_status "Getting deployment outputs..."
    
    # Get SageMaker domain URL
    DOMAIN_URL=$(terraform output -raw sagemaker_domain_url 2>/dev/null || echo "Not available")
    print_status "SageMaker Domain URL: $DOMAIN_URL"
    
    # Get SageMaker endpoint name
    ENDPOINT_NAME=$(terraform output -raw sagemaker_endpoint_name 2>/dev/null || echo "Not available")
    print_status "SageMaker Endpoint Name: $ENDPOINT_NAME"
    
    # Get SageMaker endpoint URL
    ENDPOINT_URL=$(terraform output -raw sagemaker_endpoint_url 2>/dev/null || echo "Not available")
    print_status "SageMaker Endpoint URL: $ENDPOINT_URL"
    
    # Get S3 bucket information
    S3_BUCKET=$(terraform output -raw sagemaker_s3_bucket_name 2>/dev/null || echo "Not available")
    print_status "SageMaker S3 Bucket: $S3_BUCKET"
    
    # Get IAM role information
    IAM_ROLE=$(terraform output -raw sagemaker_role_arn 2>/dev/null || echo "Not available")
    print_status "SageMaker IAM Role: $IAM_ROLE"
    
    echo ""
    print_status "Next steps:"
    echo "1. Access SageMaker Studio at: $DOMAIN_URL"
    echo "2. Use the endpoint for inference: $ENDPOINT_URL"
    echo "3. Upload models to S3 bucket: $S3_BUCKET"
    echo "4. Ensure your application uses the IAM role: $IAM_ROLE"
}

# Test SageMaker endpoint
test_endpoint() {
    print_header "Testing SageMaker Endpoint"
    
    ENDPOINT_NAME=$(terraform output -raw sagemaker_endpoint_name 2>/dev/null)
    
    if [ -z "$ENDPOINT_NAME" ] || [ "$ENDPOINT_NAME" = "Not available" ]; then
        print_warning "Cannot test endpoint - endpoint name not available"
        return
    fi
    
    print_status "Testing endpoint: $ENDPOINT_NAME"
    
    # Wait for endpoint to be in service
    print_status "Waiting for endpoint to be in service..."
    aws sagemaker wait endpoint-in-service --endpoint-name "$ENDPOINT_NAME" --region "$AWS_REGION"
    
    if [ $? -eq 0 ]; then
        print_status "Endpoint is in service"
        
        # Test with a simple prompt
        print_status "Testing endpoint with sample prompt..."
        
        # Create test payload
        cat > test_payload.json << EOF
{
    "prompt": "Hello, how are you?",
    "temperature": 0.7,
    "max_tokens": 100
}
EOF
        
        # Invoke endpoint
        aws sagemaker-runtime invoke-endpoint \
            --endpoint-name "$ENDPOINT_NAME" \
            --content-type application/json \
            --input file://test_payload.json \
            --output response.json \
            --region "$AWS_REGION"
        
        if [ $? -eq 0 ]; then
            print_status "Endpoint test successful!"
            print_status "Response:"
            cat response.json | jq '.' 2>/dev/null || cat response.json
            
            # Clean up test files
            rm -f test_payload.json response.json
        else
            print_error "Endpoint test failed"
        fi
    else
        print_error "Endpoint failed to come into service"
    fi
}

# Clean up
cleanup() {
    print_status "Cleaning up..."
    
    # Remove plan file
    if [ -f "tfplan" ]; then
        rm -f tfplan
        print_status "Removed tfplan file"
    fi
    
    # Remove test files
    rm -f test_payload.json response.json 2>/dev/null || true
}

# Main function
main() {
    print_header "SageMaker Ollama Deployment"
    
    # Check prerequisites
    check_prerequisites
    
    # Navigate to infrastructure directory
    navigate_to_infra
    
    # Initialize Terraform
    init_terraform
    
    # Plan deployment
    plan_deployment
    
    # Apply deployment
    apply_deployment
    
    # Display deployment information
    display_deployment_info
    
    # Test endpoint
    test_endpoint
    
    # Cleanup
    cleanup
    
    print_header "Deployment Complete!"
    print_status "Your SageMaker infrastructure is now ready for Ollama models."
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"
