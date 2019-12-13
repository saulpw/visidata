#!/usr/bin/env bash
set -e

KEY_FILE=/tmp/gitcrypt.key
DOCKER_REGISTRY=docker.pkg.github.com
DOCKER_IMAGE=$DOCKER_REGISTRY/saulpw/vdwww/vdwww:latest

sudo apt-get install git-crypt kubectl

# Setup git-crypt to provide access to secure credentials
echo "Unlocking secure credentials with git-crypt..."
echo $GITCRYPT_KEY | base64 -d > $KEY_FILE
git-crypt unlock $KEY_FILE

# Parse the Docker Registry credentials from the k8s setup
json=$(
  cat k8s/secrets.tf |
  grep $DOCKER_REGISTRY |
  sed 's/default =//' |
  sed 's/\\//g' |
  sed 's/"//' |
  sed 's/"$//g'
)
registry_user=$(echo $json | jq ".auths[\"$DOCKER_REGISTRY\"].username" | sed 's/"//g')
registry_password=$(echo $json | jq ".auths[\"$DOCKER_REGISTRY\"].password" | sed 's/"//g')

# Build the Docker image
docker build -t vdwww .

# Quick test
docker run --rm -d -p 9000:9000 vdwww
sleep 1
[ $(curl -LI localhost:9000 -o /dev/null -w '%{http_code}\n' -s) == "200" ]

# Push the image so k8s can pull it for the deploy
docker login $DOCKER_REGISTRY --username $registry_user --password $registry_password
docker tag vdwww $DOCKER_IMAGE
docker push $DOCKER_IMAGE

# Deploy
config="--kubeconfig k8s/ci_user.k8s_config --context ci"
kubectl $config rollout restart deployment/visidata
