# AWS Security Configuration Guide for SageMaker Infrastructure

This guide provides comprehensive information about the security features implemented in your AWS SageMaker infrastructure for Ollama models.

## 🛡️ Security Overview

The infrastructure implements a **defense-in-depth** security approach with multiple layers of protection:

1. **Network Security** - VPC isolation, security groups, VPC endpoints
2. **Data Security** - KMS encryption, S3 bucket policies, IAM roles
3. **Monitoring & Alerting** - CloudWatch, CloudTrail, Security Hub
4. **Compliance** - AWS Config rules, GuardDuty, access controls
5. **Threat Protection** - WAF, VPC Flow Logs, security groups

## 🏗️ Network Security Architecture

### VPC Configuration

```
┌─────────────────────────────────────────────────────────────┐
│                    Custom VPC (10.0.0.0/16)                │
├─────────────────────────────────────────────────────────────┤
│  Public Subnets (NAT Gateway)                              │
│  ├─ ap-southeast-1a: 10.0.0.0/24                          │
│  └─ ap-southeast-1b: 10.0.1.0/24                          │
├─────────────────────────────────────────────────────────────┤
│  Private Subnets (SageMaker)                               │
│  ├─ ap-southeast-1a: 10.0.10.0/24                         │
│  └─ ap-southeast-1b: 10.0.11.0/24                         │
├─────────────────────────────────────────────────────────────┤
│  VPC Endpoints (AWS Services)                              │
│  ├─ SageMaker API                                          │
│  ├─ SageMaker Runtime                                      │
│  ├─ S3 Gateway                                             │
│  ├─ ECR                                                    │
│  └─ CloudWatch Logs                                        │
└─────────────────────────────────────────────────────────────┘
```

### Security Groups

#### SageMaker Security Group
- **Inbound**: No inbound rules (private subnets)
- **Outbound**: 
  - HTTPS (443) to SageMaker API
  - HTTP (80) for model downloads
  - All outbound for SageMaker operations

#### VPC Endpoints Security Group
- **Inbound**: HTTPS (443) from SageMaker security group only
- **Outbound**: No outbound rules needed

#### EC2 Security Group
- **Inbound**: SSH (22), HTTP (80), HTTPS (443)
- **Outbound**: All traffic allowed

## 🔐 Data Security

### KMS Encryption

**Custom KMS Key**: `alias/studyai-dev-sagemaker`

- **Key Rotation**: Enabled (automatic)
- **Deletion Window**: 7 days
- **Usage**: SageMaker endpoints, S3 buckets, CloudWatch logs

**KMS Policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Enable IAM User Permissions",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::ACCOUNT:root"},
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "Allow SageMaker to use the key",
      "Effect": "Allow",
      "Principal": {"Service": "sagemaker.amazonaws.com"},
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:Encrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": "sagemaker.ap-southeast-1.amazonaws.com"
        }
      }
    }
  ]
}
```

### S3 Bucket Security

**Uploads Bucket**:
- Server-side encryption (AES256)
- Versioning enabled
- Public access blocked
- CORS configured for web app

**SageMaker Bucket**:
- Server-side encryption (KMS)
- Versioning enabled
- Public access blocked
- Lifecycle policies (configurable)

## 👥 Identity and Access Management (IAM)

### SageMaker Execution Role

**Role**: `studyai-dev-sagemaker-role`

**Permissions**:
- S3 access to SageMaker bucket
- ECR access for container images
- CloudWatch Logs access
- KMS encryption/decryption

**Trust Policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "sagemaker.amazonaws.com"
      }
    }
  ]
}
```

### EC2 Instance Role

**Role**: `studyai-dev-ec2-role`

**Permissions**:
- S3 read/write access to uploads bucket
- CloudWatch Logs access

### Password Policy (Optional)

When enabled:
- Minimum length: 12 characters
- Require: lowercase, uppercase, numbers, symbols
- Maximum age: 90 days
- Reuse prevention: 24 passwords

## 📊 Monitoring and Logging

### CloudWatch Monitoring

**Dashboard**: `studyai-dev-sagemaker-dashboard`

**Metrics**:
- SageMaker endpoint invocations
- Error rates (4XX, 5XX)
- Model latency
- Instance utilization

**Alarms**:
- High error rates (>5 5XX errors)
- High latency (>10 seconds)
- Unauthorized API calls
- Root account usage

### CloudTrail Logging (Optional)

**Trail**: `studyai-dev-sagemaker-trail`

**Features**:
- Multi-region logging
- S3 storage with encryption
- Management event logging
- Excludes KMS events for security

### VPC Flow Logs (Optional)

**Log Group**: `/aws/vpc/flow-logs/studyai-dev`

**Information**:
- Source/destination IP addresses
- Ports and protocols
- Packet counts and bytes
- Timestamps and actions

## 🚨 Threat Detection and Response

### GuardDuty (Optional)

**Detector**: Account-wide threat detection

**Capabilities**:
- Unusual API calls
- Suspicious IP addresses
- Compromised credentials
- Instance compromise

### Security Hub (Optional)

**Standards**:
- CIS AWS Foundations Benchmark
- PCI DSS v3.2.1

**Findings**:
- Security best practices
- Compliance violations
- Risk assessments

### WAF Protection (Optional)

**Web ACL**: `studyai-dev-sagemaker-waf`

**Rules**:
- Rate limiting (2000 requests/IP)
- AWS managed rules (common threats)
- SQL injection protection
- Suspicious IP blocking

## 🔍 Compliance and Auditing

### AWS Config Rules (Optional)

**SageMaker Encryption Check**:
- Ensures endpoints use KMS encryption
- Non-compliant resources flagged

**S3 Encryption Check**:
- Ensures S3 buckets have encryption
- Compliance reporting available

### Access Analyzer (Optional)

**Analyzer**: `studyai-dev-sagemaker-analyzer`

**Capabilities**:
- Unused IAM permissions
- Public resource identification
- Cross-account access analysis

## 🚀 Security Best Practices Implementation

### 1. Least Privilege Access

- IAM roles with minimal required permissions
- Security groups with specific port access
- VPC endpoints for service communication

### 2. Data Encryption

- KMS encryption for all sensitive data
- TLS 1.2+ for data in transit
- S3 bucket encryption at rest

### 3. Network Isolation

- Private subnets for SageMaker resources
- VPC endpoints for AWS service communication
- No direct internet access for private resources

### 4. Monitoring and Alerting

- Real-time CloudWatch metrics
- Automated alarms for security events
- SNS notifications for critical alerts

### 5. Compliance Monitoring

- AWS Config rules for resource compliance
- Security Hub for industry standards
- Regular security assessments

## ⚙️ Configuration Options

### Basic Security (Default)
```hcl
enable_sagemaker = true
enable_kms_encryption = true
enable_cloudwatch_monitoring = true
enable_vpc_endpoints = true
```

### Enhanced Security
```hcl
enable_sagemaker = true
enable_kms_encryption = true
enable_cloudwatch_monitoring = true
enable_vpc_endpoints = true
enable_guardduty = true
enable_security_hub = true
enable_waf = true
enable_cloudtrail = true
enable_vpc_flow_logs = true
```

### Enterprise Security
```hcl
enable_sagemaker = true
enable_kms_encryption = true
enable_cloudwatch_monitoring = true
enable_vpc_endpoints = true
enable_guardduty = true
enable_security_hub = true
enable_waf = true
enable_cloudtrail = true
enable_vpc_flow_logs = true
enable_config = true
enable_access_analyzer = true
enable_strict_password_policy = true
enable_security_alerts = true
security_alert_email = "security@yourcompany.com"
```

## 🔧 Security Hardening Steps

### 1. Enable Advanced Security Features

```bash
# Update terraform.tfvars
enable_guardduty = true
enable_security_hub = true
enable_waf = true
enable_cloudtrail = true
enable_vpc_flow_logs = true
```

### 2. Configure Security Alerts

```bash
# Set your email for security notifications
security_alert_email = "your-email@domain.com"
enable_security_alerts = true
```

### 3. Enable Compliance Monitoring

```bash
enable_config = true
enable_access_analyzer = true
```

### 4. Apply Security Updates

```bash
cd infra
terraform plan -var="enable_sagemaker=true" -var="enable_guardduty=true"
terraform apply -var="enable_sagemaker=true" -var="enable_guardduty=true"
```

## 📋 Security Checklist

### Network Security
- [ ] Custom VPC with private subnets
- [ ] VPC endpoints for AWS services
- [ ] Security groups with minimal access
- [ ] NAT Gateway for outbound internet

### Data Security
- [ ] KMS encryption enabled
- [ ] S3 bucket encryption
- [ ] TLS for data in transit
- [ ] IAM roles with least privilege

### Monitoring
- [ ] CloudWatch metrics and alarms
- [ ] CloudTrail logging enabled
- [ ] VPC Flow Logs configured
- [ ] Security alerts configured

### Threat Detection
- [ ] GuardDuty enabled
- [ ] Security Hub configured
- [ ] WAF rules configured
- [ ] Compliance monitoring active

### Access Control
- [ ] Strong password policy
- [ ] Access Analyzer enabled
- [ ] Regular access reviews
- [ ] Multi-factor authentication

## 🚨 Incident Response

### Security Event Response

1. **Immediate Actions**:
   - Check CloudWatch alarms
   - Review CloudTrail logs
   - Investigate GuardDuty findings

2. **Containment**:
   - Update security groups if needed
   - Revoke compromised credentials
   - Isolate affected resources

3. **Recovery**:
   - Restore from backups
   - Update security configurations
   - Document lessons learned

### Contact Information

- **Security Team**: [Your Security Email]
- **AWS Support**: [Your Support Plan]
- **Emergency**: [Your Emergency Contact]

## 📚 Additional Resources

- [AWS Security Best Practices](https://aws.amazon.com/security/security-learning/)
- [SageMaker Security](https://docs.aws.amazon.com/sagemaker/latest/dg/security.html)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services/)

## 🔄 Regular Security Reviews

### Monthly
- Review CloudWatch metrics
- Check GuardDuty findings
- Review IAM access logs

### Quarterly
- Security Hub compliance review
- Access Analyzer findings review
- Security group rule review

### Annually
- Penetration testing
- Security architecture review
- Compliance audit
- Security training updates

---

**Note**: This security configuration follows AWS security best practices and industry standards. Regular reviews and updates are recommended to maintain security posture.
