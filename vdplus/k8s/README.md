# Installation

## Prerequisties

All of these should be installable through your OS's standard package manager.

  * [`doctl`](https://github.com/digitalocean/doctl): Talking to the Digital Ocean API. 
  * [Terraform](https://learn.hashicorp.com/terraform/getting-started/install.html): Infrastructure As Code. Talking to the k8s API.
  * [Helm](https://v3.helm.sh/docs/intro/install/): Kubernetes package manager.

## Add `secrets.tf`

Terraform uses certain secret values such as API credentials and so on. These should not
be kept in Git's history. Once you have your own copy from a trusted source place it at
`k8s/secrets.tf`.

## Authenticate with Digital Ocean

You will need to provide the DO Access Token to both `doctl`'s config file and Terraform.

  * For `doctl` run `doctl auth init`
  * For Terraform ensure there is a 'do_vd_key' setting in `secrets.tf`

The DO token is not accessible from the DO website. The only copies should be in a secret
store or in the config of other developers working on VisiData's Kubernetes cluster. Usually
kept in `$HOME/.config/doctl/config.yaml`.

## Creating/updating the cluster

When running `terraform` for the first time on a new machine (whether the live cluster exists
or not) run `terraform init` to download the necessary third-party Terraform plugins.

To then either create a new cluster or update the existing one change path to the `k8s/` folder and run `terraform apply`.

When creating a cluster for the first time `terraform apply` may need to be run twice if
certain services didn't come up in the right order.

Finally save the cluster's config with `doctl kubernetes cluster kubeconfig save vdwww` so that
`kubectl` knows how to access the Kubernetes API.

## Creating the cluster for the first time

### Helm permission error
NB. December 2019, with a fresh install of all dependencies seems to also need this to get Helm
to work:

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


