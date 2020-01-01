#!/usr/bin/env bash
set -e

KEY_FILE=/tmp/gitcrypt.key
DOCKER_REGISTRY=docker.k8s.visidata.org
VDWWW_IMAGE=$DOCKER_REGISTRY/vdwww/vdwww:latest
VDHUB_IMAGE=$DOCKER_REGISTRY/vdwww/vdhub:latest

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

# Push the images so k8s can pull them for the deploy
docker login $DOCKER_REGISTRY --username $registry_user --password $registry_password
docker tag vdwww $VDWWW_IMAGE
docker push $VDWWW_IMAGE
docker tag vdhub $VDHUB_IMAGE
docker push $VDHUB_IMAGE

config="--kubeconfig k8s/ci_user.k8s_config --context ci"

# Clean up all image revisions. We only want currently tagged images in the registry in
# order to save space.
pod=$(kubectl $config get pods -n docker-registry -o custom-columns=:metadata.name | xargs)
gc="registry garbage-collect --delete-untagged=true /etc/docker/registry/config.yml"
echo $gc | kubectl $config \
  exec -it \
  $pod -n docker-registry \
  sh

# Deploy
kubectl $config rollout restart deployment/visidata
kubectl $config rollout restart deployment/hub
