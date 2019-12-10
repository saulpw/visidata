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
    }
  }
  spec {
    backend {
      service_name = "visidata"
      service_port = 80
    }
    rule {
      host = "vdwww.tombh.co.uk"
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
