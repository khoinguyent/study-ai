TF=terraform
INFRA=infra

init:
	cd $(INFRA) && $(TF) init

plan:
	cd $(INFRA) && $(TF) plan

apply:
	cd $(INFRA) && $(TF) apply -auto-approve

apply-secure:
	cd $(INFRA) && $(TF) apply -auto-approve -var="allow_ssh_cidr=$$(curl -s https://ifconfig.me)/32"

destroy:
	cd $(INFRA) && $(TF) destroy -auto-approve

out:
	cd $(INFRA) && $(TF) output

ssh:
	cd $(INFRA) && ssh -i ./studyai_key ubuntu@$$($(TF) output -raw ec2_public_ip)
