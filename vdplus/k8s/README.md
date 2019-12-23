# Installation

## Prerequisties

All of these should be installable through your OS's standard package manager (Snaps, PPAs).
However, most of these also have oneliner `curl` commands to install simple static binaries.

  * [`doctl`](https://github.com/digitalocean/doctl): Talking to the Digital Ocean API. 
  * [`kubectl`](https://kubernetes.io/docs/tasks/tools/install-kubectl/): Talking to the Kubernetes API. 
  * [Terraform](https://learn.hashicorp.com/terraform/getting-started/install.html): Infrastructure As Code. Talking to the k8s API.
  * [Helm](https://v3.helm.sh/docs/intro/install/) (v2.5.1): Kubernetes package manager.

## Authenticate with Digital Ocean

The VisiData DO Access Token is present at `k8s/secrets.tf` as the variable named `do_vd_key`.
Setup the DO admin CLI tool with `doctl auth init` and paste the DO token when prompted.

If the cluster is already created you can skip to 'Connecting `kubectl` to the cluster'.

## Creating/updating the cluster

Terraform provides what's known as [Infrastructure as Code](https://en.wikipedia.org/wiki/Infrastructure_as_code). This is the practice of maintaining the exact and reproducible state of the compute resources and cluster in source code. It is possible to manually issue `doctl` (to create VMs) and `kubectl` (to create k8s apps) commands, but that quickly becomes unweildly. Instead it is possible to create a suite of `.tf` files that declaritvely define the infrastructure and then a `terraform apply` should always be able ensure that the state of the locally described infrastructure in code matches the state of the real resources in the wild.

All `terraform` commands need to be run within the `k8s/` folder.

When running `terraform` for the first time on a new machine (whether the live cluster exists
or not) run `terraform init` to download the necessary third-party Terraform plugins.

To then either create a new cluster or update the existing one run `terraform apply`.

When creating a cluster for the first time `terraform apply` will need to be run at least twice. Partly because some services don't come up in the right order, but also because some services
rely on the cluster-internal Docker registry. So after the first run the following images will need to be pushed:

  * `docker push docker.k8s.visidata.org/vdwww/nfs-server:latest`. See `k8s/nfs-server`
  * `docker push docker.k8s.visidata.org/vdwww/vdwww:latest`. See `vd/Dockerfile`
  * `docker push docker.k8s.visidata.org/vdhub/vdwww:latest`. See `hub/Dockerfile`
  * TODO: Terraform/k8s can actually automate this.

### Connecting `kubectl` to the cluster
Once the cluster exists, save the cluster's config with
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

It could be because I used Helm v3.0.1, instead of v2.5.1, but we can't be certain until someone
rebuilds the cluster themselves from scratch.

### Load Balancer IP
A platform-specific load balancer will be created outside the Kubernetes cluster. On DO it
doesn't currently seem possible to associate a specific IP address. So you will need to look
at the DO UI under Networking->Load Balancers to find the new IP address and assign it as an
A record to the appropriate domain.

## Monitoring
The Grafana UI for the Prometheus monitoring stack can be accessed at: https://grafana.k8s.visidata.org

Username 'admin' and the password is in `secrets.tf` under 'grafana_password'.

### App logs

A basic dashboard for the 'vdwww' app logs is availabale at https://grafana.k8s.visidata.org/d/Ousb_eaZk/visidata-www-logs?orgId=1&refresh=5s

## Private Docker Registry
The cluster includes a private Docker registry at: https://docker.k8s.visidata.org

Auth can be found in `secrets.tf` and the avaiable disk space can be increased at `k8s/docker-registry.tf`. Note that resizing the volume may not guarantee the data is retained.

