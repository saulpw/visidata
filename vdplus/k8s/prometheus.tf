# Prometheus is currently the defacto monitoring solution for Kubernetes.
# This chart also installs Grafana for viewing the monitoring data in graphs
# and on dashboards.
# And there's also an alert manager here to generate various kinds of alerts.

# Both these versions should be changed at the same time
variable "prometheus_version" {
  default = "8.3.3"
}
variable "prometheus_commit" {
  default = "ab911e1919921acd73298b09648fa0eef4828896"
}

# Theoretically Helm should be installing these, but for some reason it doesn't
resource "null_resource" "prometheus-crd" {
  depends_on = [digitalocean_kubernetes_cluster.vd]

  triggers = {
    version = var.prometheus_version
  }

  provisioner "local-exec" {
    command = <<EOC
echo "Applying CRDs for Prometheus"

base=https://raw.githubusercontent.com/helm/charts/${var.prometheus_commit}/stable/prometheus-operator/crds/

kubectl apply -f $base/crd-alertmanager.yaml
kubectl apply -f $base/crd-podmonitor.yaml
kubectl apply -f $base/crd-prometheus.yaml
kubectl apply -f $base/crd-prometheusrules.yaml
kubectl apply -f $base/crd-servicemonitor.yaml

echo "CRDs applied"
EOC
  }
}

resource "helm_release" "prometheus-operator" {
  name = "prometheus-operator"
  namespace = "monitoring"
  chart = "stable/prometheus-operator"
  version = var.prometheus_version

  values = [
    file("yaml/prometheus.yaml")
  ]

  set {
    name = "prometheusOperator.createCustomResource"
    value = false
  }

  set {
    name = "grafana.adminPassword"
    value = var.grafana_password
  }
}

resource "kubernetes_service" "grafana" {
  metadata {
    name = "grafana"
  }

  spec {
    selector = {
      app = "visidata"
    }

    port {
      name = "grafana"
      port = 443
      target_port = 80
    }
  }
}

resource "kubernetes_ingress" "grafana-ingress" {
  metadata {
    name = "grafana-ingress"
    namespace = "monitoring"
    annotations = {
      "kubernetes.io/ingress.class" = "nginx"
      "cert-manager.io/cluster-issuer": "letsencrypt-prod"
      "cert-manager.io/acme-challenge-type": "http01"
    }
  }
  spec {
    tls {
      hosts = [
        "grafana.k8s.visidata.org",
      ]
      secret_name = "grafana-tls"
    }
    backend {
      service_name = "prometheus-operator-grafana"
      service_port = 80
    }
    rule {
      host = "grafana.k8s.visidata.org"
      http {
        path {
          path = "/*"
          backend {
            service_name = "prometheus-operator-grafana"
            service_port = 80
          }
        }
      }
    }
  }
}
