# The `digitalocean` provider is a third-party Terraform plugin. It needs an
# API key to talk to the Digital Ocean platform
provider "digitalocean" {
  token = var.do_vd_key
}

# The main definition of the Kubernetes cluster
# !! Changing some of these can delete and recreate the entire cluster without warning !!
resource "digitalocean_kubernetes_cluster" "vd" {
  name    = "vdwww"
  region  = "sfo2"
  version = "1.16.2-do.0"

  # Node pools are just a way of grouping VMs
  node_pool {
    name       = "vdwww-pool"
    size       = "s-2vcpu-4gb"
    node_count = 3 // changing this doesn't delete the cluster
  }
}

# Once the cluster is created, all other Terraform commands will reference the cluster
# by its ID.
output "cluster-id" {
  value = digitalocean_kubernetes_cluster.vd.id
}

# The `kubernetes` provider is a third-party Terraform plugin. It knows nothing about
# the company that provides the underlying compute resources. It talks only to a k8s API.
provider "kubernetes" {
  host = digitalocean_kubernetes_cluster.vd.endpoint
  token = digitalocean_kubernetes_cluster.vd.kube_config[0].token
}

