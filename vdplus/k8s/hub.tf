resource "kubernetes_deployment" "hub" {
  metadata {
    name = "hub"
  }
  spec {
    selector {
      match_labels = {
        app = "hub"
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
          app = "hub"
        }
      }
      spec {
        // A service account token allows the containers to access the central k8s API
        automount_service_account_token = true
        container {
          name  = "app"
          image = "localhost:31500/vdwww/vdhub:latest"
          image_pull_policy = "Always"

          volume_mount {
            name = "data"
            mount_path = "/app/data"
            read_only = true
          }

          # Temp whilst testing bundled vd
          env {
            name = "TERM"
            value = "xterm"
          }

          # These settings dictate the status of the container for deciding whether the
          # service is ready to replace the old version during deployment.
          #readiness_probe {
            #http_get {
              #path   = "/"
              #port   = "8000"
              #scheme = "HTTP"
            #}
            #initial_delay_seconds = 1
            #timeout_seconds   = 5
            #period_seconds    = 5
            #success_threshold = 1
            #failure_threshold = 3
          #}

          port {
            container_port = 8000
          }
        }
        volume {
          name = "data"
          persistent_volume_claim {
            claim_name = "do-spaces-vdata"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "hub" {
  metadata {
    name = "hub"
  }

  spec {
    selector = {
      app = "hub"
    }

    port {
      name = "hub"
      port = 80
      target_port = 8000
    }
  }
}

resource "kubernetes_ingress" "hub-ingress" {
  metadata {
    name = "hub-ingress"
    annotations = {
      "kubernetes.io/ingress.class" = "nginx"
      "cert-manager.io/cluster-issuer": "letsencrypt-prod"
      "cert-manager.io/acme-challenge-type": "http01"
    }
  }
  spec {
    tls {
      hosts = [
        "staging.k8s.visidata.org",
      ]
      secret_name = "hub-tls"
    }
    backend {
      service_name = "hub"
      service_port = 80
    }
    rule {
      host = "staging.k8s.visidata.org"
      http {
        path {
          path = "/*"
          backend {
            service_name = "hub"
            service_port = 80
          }
        }
      }
    }
  }
}

