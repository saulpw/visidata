# Installation

## Prerequisties

All of these should be installable through your OS's standard package manager.

  * [`doctl`](https://github.com/digitalocean/doctl): Talking to the Digital Ocean API. 
  * [Terraform](https://learn.hashicorp.com/terraform/getting-started/install.html): Infrastructure As Code. Talking to the k8s API.
  * [Helm](https://v3.helm.sh/docs/intro/install/): Kubernetes package manager.

## Authenticate with Digital Ocean

The DO Access Token is present at `k8s/secrets.tf` as the variable named `do_vd_key`.
Setup the DO admin CLI tool with `doctl auth init` and paste the DO token when prompted.

## Creating/updating the cluster

All `terraform` commands need to be run within the `k8s/` folder.

When running `terraform` for the first time on a new machine (whether the live cluster exists
or not) run `terraform init` to download the necessary third-party Terraform plugins.

To then either create a new cluster or update the existing one run `terraform apply`.

When creating a cluster for the first time `terraform apply` may need to be run twice if
certain services didn't come up in the right order.

### Connecting `kubectl` to the cluster
Once the cluster exists save the cluster's config with
`doctl kubernetes cluster kubeconfig save vdwww` so that `kubectl` knows how to access the Kubernetes API.

## Creating the cluster for the first time

### Helm permission error
NB. December 2019, with a fresh install of all dependencies Helm seems to also need this to make
it happy:

```
kubectl patch deploy tiller-deploy \
  -p '{"spec":{"template":{"spec":{"serviceAccount":"tiller","serviceAccountName":"tiller"}}}}' \
  -n kube-system
```

It could be because of Helm v3.0.1, but I can't be certain.

### Load Balancer IP
A platform-specific load balancer will be created outside the Kubernetes cluster. On DO it
doesn't currently seem possible to associate a specific IP address. So you will need to look
at the DO UI under Networking->Load Balancers to find the new IP address and assign it as an
A record to the appropriate domain.

## Monitoring
The Grafana UI for the Prometheus monitoring stack can be accessed by forwarding the Grafana
web service to your local machine. The command is:

`kubectl port-forward -n monitoring svc/prometheus-operator-grafana 10080:80`

You can then visit localhost:10080 in your browser and login with the username 'admin' and the
password defined for 'grafana_password' in `secrets.tf`.

### App logs

A basic dashboard for the 'vdwww' app logs is availabale at http://localhost:10080/d/Ousb_eaZk/visidata-www-logs?orgId=1&refresh=5s
