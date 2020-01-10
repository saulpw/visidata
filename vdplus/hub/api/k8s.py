import os
import time
import logging

import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from models.user import User

NAMESPACE = 'default'
TOKEN_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/token'
CERT_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
ACCOUNTS_SUB_PATH = "accounts"

if os.getenv("VD_ENV") == "dev":
    # Dear developers:
    # This file isn't even relevant unless you have USE_REMOTE_K8S=true set.
    # And even then we still can't reach the sub-network of the created cotainer.
    # But it's still useful because it tests all the other code here.
    config.load_kube_config()
    api = client.CoreV1Api()
elif os.getenv("CI") != "true":
    logging.debug("Setting up production k8s API")
    with open(TOKEN_PATH) as f:
        token = f.read().rstrip()
    config = client.Configuration()
    config.api_key['authorization'] = token
    config.api_key_prefix['authorization'] = 'Bearer'
    config.host = 'https://' + os.getenv("KUBERNETES_SERVICE_HOST")
    config.ssl_ca_cert = CERT_PATH
    api = client.CoreV1Api(client.ApiClient(config))
    logging.debug("Production k8s API client ready")

def k8s_api_request(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except ApiException as e:
            logging.error("Kubernetes API exception: %s\n" % e)
            return False
    return wrapper

@k8s_api_request
def k8s_create_pod(user: User):
    name = str(user.id)
    user_id = str(user.id)
    logging.debug("Creating dedicated VD pod for user: " + name)
    pod_yaml = generate_pod_yaml(name, user_id, user.is_guest)
    response = api.create_namespaced_pod(NAMESPACE, pod_yaml)
    ip = None
    while ip == None:
        response = api.read_namespaced_pod(name, NAMESPACE)
        ip = response.status.pod_ip
        time.sleep(0.1)
    return ip

def generate_pod_yaml(name, user_id, is_guest):
    with open('pod.yaml') as file:
        pod = yaml.safe_load(file)
    pod['metadata']['name'] = name
    if is_guest:
        pod = guest_pod(pod)
    else:
        pod = account_pod(pod, user_id)
    return pod

def guest_pod(pod):
    pod['spec']['containers'][0]['volumeMounts'][0]['mountPath'] = '/app/data'
    del pod['spec']['containers'][0]['volumeMounts'][1]
    del pod['spec']['containers'][1]
    del pod['spec']['volumes'][1]
    return pod

def account_pod(pod, user_id):
    pod['spec']['containers'][0]['volumeMounts'][0]['mountPath'] = '/app/data/samples'
    pod['spec']['containers'][1]['env'] = [
        {
            'name': 'DO_SPACES_API_ID',
            'value': os.getenv('DO_SPACES_API_ID'),
        },
        {
            'name': 'DO_SPACES_API_SECRET',
            'value': os.getenv('DO_SPACES_API_SECRET')
        },
        {
            'name': 'USER_ID',
            'value': user_id
        }
    ]
    return pod

@k8s_api_request
def k8s_delete_pod(user: User):
    name = str(user.id)
    logging.debug("Attempting to delete container: " + name)
    api.delete_namespaced_pod(name, NAMESPACE)
