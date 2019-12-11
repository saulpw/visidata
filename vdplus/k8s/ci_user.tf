# A dedicated user for deploying the app from CI

resource "kubernetes_service_account" "ci" {
  metadata {
    name = "ci"
  }
}

resource "kubernetes_role" "ci_user_role" {
  metadata {
    name = "ci_user_role"
  }

  rule {
    verbs      = ["get", "update", "list", "patch"]
    api_groups = ["apps"]
    resources  = ["deployments"]
  }
}

resource "kubernetes_role_binding" "ci_user_binding" {
  metadata {
    name = "ci_user_binding"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = "ci_user_role"
  }

  subject {
    api_group = ""
    kind = "ServiceAccount"
    name = "ci"
  }

}
