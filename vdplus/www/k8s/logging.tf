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

resource "kubernetes_service" "loki" {
  metadata {
    name = "loki"
  }

  spec {
    selector = {
      app = "visidata"
    }

    port {
      name = "loki"
      port = 443
      target_port = 3100
    }
  }
}

resource "kubernetes_ingress" "loki-ingress" {
  metadata {
    name = "loki-ingress"
    namespace = "logging"
    annotations = {
      "kubernetes.io/ingress.class" = "nginx"
      "cert-manager.io/cluster-issuer": "letsencrypt-prod"
      "cert-manager.io/acme-challenge-type": "http01"
    }
  }
  spec {
    tls {
      hosts = [
        "loki.k8s.visidata.org",
      ]
      secret_name = "loki-tls"
    }
    backend {
      service_name = "loki"
      service_port = 3100
    }
    rule {
      host = "loki.k8s.visidata.org"
      http {
        path {
          path = "/*"
          backend {
            service_name = "loki"
            service_port = 3100
          }
        }
      }
    }
  }
}
