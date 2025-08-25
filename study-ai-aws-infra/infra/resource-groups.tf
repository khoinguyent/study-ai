# AWS Resource Groups for Studium-app Project
# This file creates tag-based resource groups for easy project management

# Main project resource group - all resources
resource "aws_resourcegroups_group" "studium_app" {
  name        = "${var.project_short}-${var.env}-resources"
  description = "Tag-based group for ${var.project} ${var.env}"
  
  resource_query {
    query = jsonencode({
      ResourceTypeFilters = ["AWS::AllSupported"]
      TagFilters = [
        {
          Key    = "Project"
          Values = [var.project]
        },
        {
          Key    = "Environment"
          Values = [var.env]
        }
      ]
    })
    type = "TAG_FILTERS_1_0"
  }

  tags = local.common_tags
}

# Security-focused resource group
resource "aws_resourcegroups_group" "security" {
  name        = "${var.project_short}-${var.env}-security"
  description = "Security resources for ${var.project} ${var.env}"
  
  resource_query {
    query = jsonencode({
      ResourceTypeFilters = ["AWS::AllSupported"]
      TagFilters = [
        {
          Key    = "Project"
          Values = [var.project]
        },
        {
          Key    = "Environment"
          Values = [var.env]
        },
        {
          Key    = "ResourceType"
          Values = ["IAMRole", "IAMPolicy", "IAMInstanceProfile", "SecurityGroup", "KMSKey"]
        }
      ]
    })
    type = "TAG_FILTERS_1_0"
  }

  tags = local.common_tags
}

# Monitoring and observability resource group
resource "aws_resourcegroups_group" "monitoring" {
  name        = "${var.project_short}-${var.env}-monitoring"
  description = "Monitoring resources for ${var.project} ${var.env}"
  
  resource_query {
    query = jsonencode({
      ResourceTypeFilters = ["AWS::AllSupported"]
      TagFilters = [
        {
          Key    = "Project"
          Values = [var.project]
        },
        {
          Key    = "Environment"
          Values = [var.env]
        },
        {
          Key    = "ResourceType"
          Values = ["CloudWatchLogGroup", "CloudWatchDashboard", "CloudWatchAlarm"]
        }
      ]
    })
    type = "TAG_FILTERS_1_0"
  }

  tags = local.common_tags
}
