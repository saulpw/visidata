resource "helm_release" "nfs-server" {
  name = "nfs-server"
  namespace = "nfs"
  chart = "stable/nfs-server-provisioner"
  version = "0.3.2"

  set {
    name = "image.repository"
    #value = "quay.io/kubernetes_incubator/nfs-provisioner"
    value = "localhost:31500/vdwww/nfs-server"
  }

  set {
    name = "image.tag"
    #value = "v2.2.1-k8s1.12"
    value = "latest"
  }

  set {
    name = "image.pullPolicy"
    value = "Always"
  }

  set {
    name = "persistence.enabled"
    value = true
  }

  set {
    name = "persistence.size"
    value = "50Gi"
  }
}

resource "kubernetes_persistent_volume_claim" "do-spaces-vdata" {
  metadata {
    name = "do-spaces-vdata"

    annotations = {
      "volume.beta.kubernetes.io/storage-class" = "nfs"
    }
  }

  spec {
    access_modes = ["ReadOnlyMany"]

    resources {
      requests = {
        storage = "10Gi"
      }
    }
  }
}

