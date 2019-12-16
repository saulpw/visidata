resource "helm_release" "nfs-server" {
  name = "nfs-server"
  namespace = "nfs"
  chart = "stable/nfs-server-provisioner"
  version = "0.3.2"
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

