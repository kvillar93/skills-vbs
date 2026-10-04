#!/usr/bin/env bash
# Clona una EC2 de Odoo, la detiene y la vuelve a encender,
# asigna una IP elastica y crea el registro A en vbsolutions.app.
# La llave por defecto es vbsolutions. No crea una llave nueva.
set -euo pipefail

SOURCE_INSTANCE_ID="${SOURCE_INSTANCE_ID:?falta SOURCE_INSTANCE_ID}"
SUBDOMAIN="${SUBDOMAIN:?falta SUBDOMAIN}"
DNS_FQDN="${DNS_FQDN:-${SUBDOMAIN}.vbsolutions.app}"
HOSTED_ZONE_ID="${HOSTED_ZONE_ID:-Z02024091P790V5KUMWZ6}"
REGION="${REGION:-us-east-1}"
KEY_NAME="${KEY_NAME:-vbsolutions}"

export AWS_DEFAULT_REGION="$REGION"

echo "Clonando ${SOURCE_INSTANCE_ID} hacia ${DNS_FQDN} con la llave ${KEY_NAME}"

AMI_ID=$(aws ec2 create-image \
  --instance-id "$SOURCE_INSTANCE_ID" \
  --name "clone-${SUBDOMAIN}-$(date +%s)" \
  --no-reboot \
  --output text)
echo "AMI: ${AMI_ID}. Esperando disponibilidad."
aws ec2 wait image-available --image-ids "$AMI_ID"

read -r INSTANCE_TYPE SUBNET_ID SG_IDS IAM_PROFILE <<<"$(aws ec2 describe-instances \
  --instance-ids "$SOURCE_INSTANCE_ID" \
  --query "Reservations[0].Instances[0].[InstanceType,SubnetId,join(',',SecurityGroups[].GroupId),IamInstanceProfile.Arn]" \
  --output text)"

run_args=(
  --image-id "$AMI_ID"
  --instance-type "$INSTANCE_TYPE"
  --key-name "$KEY_NAME"
  --subnet-id "$SUBNET_ID"
  --security-group-ids ${SG_IDS//,/ }
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${SUBDOMAIN}}]"
)
if [[ "$IAM_PROFILE" != "None" && -n "$IAM_PROFILE" ]]; then
  run_args+=(--iam-instance-profile "Arn=${IAM_PROFILE}")
fi

NEW_INSTANCE_ID=$(aws ec2 run-instances "${run_args[@]}" \
  --query "Instances[0].InstanceId" --output text)
echo "Nueva instancia: ${NEW_INSTANCE_ID}. Esperando running."
aws ec2 wait instance-running --instance-ids "$NEW_INSTANCE_ID"

echo "Deteniendo ${NEW_INSTANCE_ID} para un arranque limpio."
aws ec2 stop-instances --instance-ids "$NEW_INSTANCE_ID" >/dev/null
aws ec2 wait instance-stopped --instance-ids "$NEW_INSTANCE_ID"
aws ec2 start-instances --instance-ids "$NEW_INSTANCE_ID" >/dev/null
aws ec2 wait instance-running --instance-ids "$NEW_INSTANCE_ID"
aws ec2 wait instance-status-ok --instance-ids "$NEW_INSTANCE_ID"

ALLOC_ID=$(aws ec2 allocate-address --domain vpc --query AllocationId --output text)
PUBLIC_IP=$(aws ec2 describe-addresses --allocation-ids "$ALLOC_ID" \
  --query "Addresses[0].PublicIp" --output text)
aws ec2 associate-address --instance-id "$NEW_INSTANCE_ID" --allocation-id "$ALLOC_ID" >/dev/null
echo "IP elastica ${PUBLIC_IP} asociada."

cat > /tmp/rr-clon.json <<EOF
{
  "Comment": "Registro A para ${DNS_FQDN}",
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "${DNS_FQDN}.",
      "Type": "A",
      "TTL": 300,
      "ResourceRecords": [{ "Value": "${PUBLIC_IP}" }]
    }
  }]
}
EOF
aws route53 change-resource-record-sets \
  --hosted-zone-id "$HOSTED_ZONE_ID" \
  --change-batch file:///tmp/rr-clon.json >/dev/null
rm -f /tmp/rr-clon.json
echo "DNS ${DNS_FQDN} -> ${PUBLIC_IP}"

echo "LISTO instance_id=${NEW_INSTANCE_ID} public_ip=${PUBLIC_IP} dns=${DNS_FQDN} ami=${AMI_ID} allocation_id=${ALLOC_ID} key=${KEY_NAME}"
