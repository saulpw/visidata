# Nginx Ingress is the internal load balancer.
# Not to be confused with DO's external load balancer.
resource "helm_release" "nginx-ingress" {
  name      = "nginx-ingress"
  namespace = "nginx-ingress"
  repository = data.helm_repository.stable.metadata.0.name
  chart     = "stable/nginx-ingress"
  version = "v1.26.2"

  set {
    name = "controller.service.type"
    value = "LoadBalancer"
  }
}

