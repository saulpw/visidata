# ---
# Lets Encrypt for automated management of SSL certs
# ---

variable "cert_manager_version" {
  default = "0.12"
}

data "local_file" "cert_manager_setup" {
  filename = "${path.module}/yaml/cert-manager.yaml"
}

data "helm_repository" "jetstack" {
  name = "jetstack"
  url  = "https://charts.jetstack.io"
}

resource "helm_release" "cert-manager" {
  name      = "cert-manager"
  namespace = "cert-manager"
  repository = data.helm_repository.jetstack.metadata.0.name
  chart     = "jetstack/cert-manager"
  version = "v${var.cert_manager_version}.0"
}

# Cert Manager uses Custom Resource Definitions (CRDs) which aren't yet supported natively
# by Terraform, hence the following `local-exec` workarounds.
# Follow: https://github.com/terraform-providers/terraform-provider-kubernetes/issues/215

resource "null_resource" "cert-manager-crd" {
  depends_on = [digitalocean_kubernetes_cluster.vd]

  triggers = {
    version = var.cert_manager_version
  }

  provisioner "local-exec" {
    command = <<EOC
echo "Applying CRDs for Cert Manager"

kubectl apply -f https://raw.githubusercontent.com/jetstack/cert-manager/release-${var.cert_manager_version}/deploy/manifests/00-crds.yaml

echo "CRDs applied"
EOC
  }
}

resource "null_resource" "cert-manager-setup" {
  depends_on = [digitalocean_kubernetes_cluster.vd]

  triggers = {
    manifest_sha1 = sha1(data.local_file.cert_manager_setup.content)
  }

  provisioner "local-exec" {
    command = <<EOC
echo "Applying custom YAML for Cert Manager "

kubectl apply -f ${data.local_file.cert_manager_setup.filename}

echo "Custom Cert Manager YAML applied"
EOC
  }
}
