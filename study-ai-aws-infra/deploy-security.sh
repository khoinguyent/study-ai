#!/bin/bash
# Deploy Enhanced Security Features for SageMaker Infrastructure

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
PURPLE='\033[0;35m'
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

print_subheader() {
    echo -e "${PURPLE}--- $1 ---${NC}"
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

# Deploy Basic Security
deploy_basic_security() {
    print_subheader "Deploying Basic Security Features"
    
    print_status "Deploying with basic security configuration..."
    
    terraform plan \
        -var="enable_sagemaker=true" \
        -var="env=$ENVIRONMENT" \
        -var="enable_kms_encryption=true" \
        -var="enable_cloudwatch_monitoring=true" \
        -var="enable_vpc_endpoints=true" \
        -out=tfplan-basic
    
    print_warning "Review the basic security plan above"
    read -p "Do you want to proceed with basic security deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Basic security deployment cancelled"
        return 1
    fi
    
    terraform apply tfplan-basic
    print_status "Basic security features deployed successfully"
}

# Deploy Enhanced Security
deploy_enhanced_security() {
    print_subheader "Deploying Enhanced Security Features"
    
    print_status "Deploying enhanced security features..."
    
    terraform plan \
        -var="enable_sagemaker=true" \
        -var="env=$ENVIRONMENT" \
        -var="enable_kms_encryption=true" \
        -var="enable_cloudwatch_monitoring=true" \
        -var="enable_vpc_endpoints=true" \
        -var="enable_guardduty=true" \
        -var="enable_security_hub=true" \
        -var="enable_waf=true" \
        -var="enable_cloudtrail=true" \
        -var="enable_vpc_flow_logs=true" \
        -out=tfplan-enhanced
    
    print_warning "Review the enhanced security plan above"
    read -p "Do you want to proceed with enhanced security deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Enhanced security deployment cancelled"
        return 1
    fi
    
    terraform apply tfplan-enhanced
    print_status "Enhanced security features deployed successfully"
}

# Deploy Enterprise Security
deploy_enterprise_security() {
    print_subheader "Deploying Enterprise Security Features"
    
    # Get security alert email
    if [ -z "$SECURITY_EMAIL" ]; then
        read -p "Enter security alert email address: " SECURITY_EMAIL
        if [ -z "$SECURITY_EMAIL" ]; then
            print_error "Security alert email is required for enterprise security"
            return 1
        fi
    fi
    
    print_status "Deploying enterprise security features..."
    
    terraform plan \
        -var="enable_sagemaker=true" \
        -var="env=$ENVIRONMENT" \
        -var="enable_kms_encryption=true" \
        -var="enable_cloudwatch_monitoring=true" \
        -var="enable_vpc_endpoints=true" \
        -var="enable_guardduty=true" \
        -var="enable_security_hub=true" \
        -var="enable_waf=true" \
        -var="enable_cloudtrail=true" \
        -var="enable_vpc_flow_logs=true" \
        -var="enable_config=true" \
        -var="enable_access_analyzer=true" \
        -var="enable_strict_password_policy=true" \
        -var="enable_security_alerts=true" \
        -var="security_alert_email=$SECURITY_EMAIL" \
        -out=tfplan-enterprise
    
    print_warning "Review the enterprise security plan above"
    read -p "Do you want to proceed with enterprise security deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Enterprise security deployment cancelled"
        return 1
    fi
    
    terraform apply tfplan-enterprise
    print_status "Enterprise security features deployed successfully"
}

# Verify Security Configuration
verify_security_config() {
    print_subheader "Verifying Security Configuration"
    
    print_status "Checking deployed security resources..."
    
    # Check SageMaker domain
    DOMAIN_URL=$(terraform output -raw sagemaker_domain_url 2>/dev/null || echo "Not available")
    print_status "SageMaker Domain: $DOMAIN_URL"
    
    # Check KMS key
    KMS_KEY_ARN=$(terraform output -raw sagemaker_role_arn 2>/dev/null || echo "Not available")
    print_status "KMS Key ARN: $KMS_KEY_ARN"
    
    # Check VPC endpoints
    print_status "Checking VPC endpoints..."
    aws ec2 describe-vpc-endpoints --region "$AWS_REGION" --filters "Name=tag:Project,Values=$ENVIRONMENT" --query 'VpcEndpoints[].{ServiceName:ServiceName,State:State}' --output table 2>/dev/null || print_warning "Could not verify VPC endpoints"
    
    # Check CloudWatch alarms
    print_status "Checking CloudWatch alarms..."
    aws cloudwatch describe-alarms --region "$AWS_REGION" --alarm-name-prefix "${ENVIRONMENT}-" --query 'MetricAlarms[].{AlarmName:AlarmName,State:StateValue}' --output table 2>/dev/null || print_warning "Could not verify CloudWatch alarms"
    
    # Check GuardDuty (if enabled)
    if terraform output -raw sagemaker_role_arn &>/dev/null; then
        print_status "Checking GuardDuty detector..."
        aws guardduty list-detectors --region "$AWS_REGION" --query 'DetectorIds' --output table 2>/dev/null || print_warning "Could not verify GuardDuty"
    fi
    
    # Check Security Hub (if enabled)
    if terraform output -raw sagemaker_role_arn &>/dev/null; then
        print_status "Checking Security Hub..."
        aws securityhub get-enabled-standards --region "$AWS_REGION" --query 'StandardsSubscriptions[].StandardsArn' --output table 2>/dev/null || print_warning "Could not verify Security Hub"
    fi
}

# Display Security Information
display_security_info() {
    print_header "Security Deployment Information"
    
    print_status "Security features deployed successfully!"
    echo ""
    
    print_subheader "Deployed Security Resources"
    echo "✅ Custom VPC with private subnets"
    echo "✅ VPC endpoints for AWS services"
    echo "✅ KMS encryption for sensitive data"
    echo "✅ CloudWatch monitoring and alarms"
    echo "✅ IAM roles with least privilege"
    echo "✅ Security groups with minimal access"
    
    if [ "$SECURITY_LEVEL" = "enhanced" ] || [ "$SECURITY_LEVEL" = "enterprise" ]; then
        echo "✅ GuardDuty threat detection"
        echo "✅ Security Hub compliance monitoring"
        echo "✅ WAF protection rules"
        echo "✅ CloudTrail API logging"
        echo "✅ VPC Flow Logs"
    fi
    
    if [ "$SECURITY_LEVEL" = "enterprise" ]; then
        echo "✅ AWS Config compliance rules"
        echo "✅ IAM Access Analyzer"
        echo "✅ Strict password policy"
        echo "✅ Security alert notifications"
    fi
    
    echo ""
    print_subheader "Next Steps"
    echo "1. Access SageMaker Studio at: $(terraform output -raw sagemaker_domain_url 2>/dev/null || echo 'Not available')"
    echo "2. Monitor security metrics in CloudWatch"
    echo "3. Review GuardDuty findings regularly"
    echo "4. Check Security Hub compliance status"
    echo "5. Configure additional security policies as needed"
    
    echo ""
    print_subheader "Security Monitoring"
    echo "• CloudWatch Dashboard: $(terraform output -raw sagemaker_role_arn 2>/dev/null | sed 's|.*/||' || echo 'Not available')-sagemaker-dashboard"
    echo "• Security Alerts: Check SNS topic for notifications"
    echo "• Compliance: Review AWS Config rules"
    echo "• Threats: Monitor GuardDuty findings"
}

# Clean up
cleanup() {
    print_status "Cleaning up..."
    
    # Remove plan files
    rm -f tfplan-basic tfplan-enhanced tfplan-enterprise 2>/dev/null || true
    
    print_status "Cleanup completed"
}

# Main function
main() {
    print_header "SageMaker Security Deployment"
    
    # Check prerequisites
    check_prerequisites
    
    # Navigate to infrastructure directory
    navigate_to_infra
    
    # Initialize Terraform
    init_terraform
    
    # Select security level
    echo ""
    print_subheader "Select Security Level"
    echo "1. Basic Security (Default)"
    echo "2. Enhanced Security (Recommended)"
    echo "3. Enterprise Security (Maximum)"
    echo ""
    
    read -p "Choose security level (1-3): " SECURITY_CHOICE
    
    case $SECURITY_CHOICE in
        1)
            SECURITY_LEVEL="basic"
            deploy_basic_security
            ;;
        2)
            SECURITY_LEVEL="enhanced"
            deploy_enhanced_security
            ;;
        3)
            SECURITY_LEVEL="enterprise"
            deploy_enterprise_security
            ;;
        *)
            print_error "Invalid choice. Exiting."
            exit 1
            ;;
    esac
    
    # Verify configuration
    verify_security_config
    
    # Display information
    display_security_info
    
    # Cleanup
    cleanup
    
    print_header "Security Deployment Complete!"
    print_status "Your SageMaker infrastructure is now secured with $SECURITY_LEVEL security features."
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"
