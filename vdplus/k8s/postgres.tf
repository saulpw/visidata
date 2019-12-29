resource "helm_release" "postgres" {
  name = "postgres"
  namespace = "postgres"
  chart = "stable/postgresql"

  values = [
    file("yaml/postgres.yaml")
  ]

  set {
    name = "postgresqlDatabase"
    value = "vdwww"
  }
  set {
    name = "postgresqlPassword"
    value = var.postgres_password
  }
}

