output "bucket_name" { value = aws_s3_bucket.uploads.bucket }
output "ec2_public_ip" { value = aws_instance.app.public_ip }
output "ec2_ssh_key" {
  value     = local_file.ssh_key.filename
  sensitive = true
}
