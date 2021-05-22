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
        service_account_name = "hub"
        init_container {
          name = "db-setup"
          image = "localhost:31500/vdwww/vdhub:latest"
          command = [
            "sh",
            "-c",
            ". $HOME/.poetry/env && cd /app/api && poetry run pw_migrate migrate"
          ]
          env {
            name = "POSTGRES_HOST"
            value = "postgres-postgresql.postgres"
          }

          env {
            name = "POSTGRES_USER"
            value = "postgres"
          }

          env {
            name = "POSTGRES_PASSWORD"
            value = var.postgres_password
          }
        }
        container {
          name  = "app"
          image = "localhost:31500/vdwww/vdhub:latest"
          image_pull_policy = "Always"

          env {
            name = "POSTGRES_HOST"
            value = "postgres-postgresql.postgres"
          }

          env {
            name = "POSTGRES_USER"
            value = "postgres"
          }

          env {
            name = "POSTGRES_PASSWORD"
            value = var.postgres_password
          }

          env {
            name = "MAILGUN_API_KEY"
            value = var.mailgun_api_key
          }

          env {
            name = "DO_SPACES_API_ID"
            value = var.do_vdata_key
          }

          env {
            name = "DO_SPACES_API_SECRET"
            value = var.do_vdata_secret
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
        "demo.visidata.org",
        "embed.visidata.org",
        "static.visidata.org",
      ]
      secret_name = "hub-tls"
    }
    backend {
      service_name = "hub"
      service_port = 80
    }
    rule {
      host = "*.visidata.org"
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

resource "kubernetes_service_account" "hub" {
  metadata {
    name = "hub"
  }
}

resource "kubernetes_role" "hub_user_role" {
  metadata {
    name = "hub_role"
  }

  rule {
    verbs      = ["get", "list", "create", "watch", "delete"]
    api_groups = [""]
    resources  = ["pods"]
  }

}
resource "kubernetes_role_binding" "hub_user_binding" {
  metadata {
    name = "hub_role_binding"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = "hub_role"
  }

  subject {
    api_group = ""
    kind = "ServiceAccount"
    name = "hub"
  }

}

