resource "kubernetes_deployment" "visidata" {
  metadata {
    name = "visidata"
  }
  spec {
    selector {
      match_labels = {
        app = "visidata"
      }
    }
    replicas = 1
    strategy {
      type = "RollingUpdate"
      rolling_update {
        max_unavailable = 0
        max_surge = 1
      }
    }
    template {
      metadata {
        labels = {
          app = "visidata"
        }
      }
      spec {
        // A service account token allows the containers to access the central k8s API
        automount_service_account_token = true
        image_pull_secrets {
          name = "github-registry-creds"
        }
        container {
          name  = "app"
          image = "docker.pkg.github.com/saulpw/vdwww/vdwww:latest"
          image_pull_policy = "Always"

          # These settings dictate the status of the container for deciding whether the
          # service is ready to replace the old version during deployment.
          readiness_probe {
            http_get {
              path   = "/"
              port   = "9000"
              scheme = "HTTP"
            }
            initial_delay_seconds = 1
            timeout_seconds   = 5
            period_seconds    = 5
            success_threshold = 1
            failure_threshold = 3
          }

          port {
            container_port = 9000
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "visidata" {
  metadata {
    name = "visidata"
  }

  spec {
    selector = {
      app = "visidata"
    }

    port {
      name = "visidata"
      port = 80
      target_port = 9000
    }
  }
}

resource "kubernetes_ingress" "vdwww-ingress" {
  metadata {
    name = "vdwww-ingress"
    annotations = {
      "kubernetes.io/ingress.class" = "nginx"
      "cert-manager.io/cluster-issuer": "letsencrypt-prod"
      "cert-manager.io/acme-challenge-type": "http01"
    }
  }
  spec {
    tls {
      hosts = [
        "demo.visidata.org",
      ]
      secret_name = "vdwww-tls"
    }
    backend {
      service_name = "visidata"
      service_port = 80
    }
    rule {
      host = "demo.visidata.org"
      http {
        path {
          path = "/*"
          backend {
            service_name = "visidata"
            service_port = 80
          }
        }
      }
    }
  }
}
