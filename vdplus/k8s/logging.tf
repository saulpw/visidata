data "local_file" "logging_setup" {
  filename = "${path.module}/yaml/logging-setup.yaml"
}

data "helm_repository" "banzaicloud" {
  name = "banzaicloud-stable"
  url  = "https://kubernetes-charts.banzaicloud.com"
}

resource "helm_release" "logging-operator" {
  name      = "logging-operator"
  namespace = "logging"
  repository = data.helm_repository.banzaicloud.metadata.0.name
  chart     = "banzaicloud-stable/logging-operator"
  version = "2.7.1"
}

data "helm_repository" "loki" {
  name = "loki"
  url  = "https://grafana.github.io/loki/charts"
}

resource "helm_release" "loki" {
  name      = "loki"
  namespace = "logging"
  repository = data.helm_repository.loki.metadata.0.name
  chart     = "loki/loki"
  version = "0.21.0"
}

resource "null_resource" "logging-setup" {
  depends_on = [digitalocean_kubernetes_cluster.vd]

  triggers = {
    manifest_sha1 = sha1(data.local_file.logging_setup.content)
  }

  provisioner "local-exec" {
    command = <<EOC
echo "Applying custom YAML for logging operator"

kubectl apply -f ${data.local_file.logging_setup.filename}

echo "Custom logging operator YAML applied"
EOC
  }
}
