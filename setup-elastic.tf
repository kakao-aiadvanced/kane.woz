terraform {
  backend "kubernetes" {
    secret_suffix  = "state"
    namespace      = "default"
    config_path    = "~/.kube/config"
    config_context = "kane-large-context"
  }
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.31.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "2.14.0"
    }
  }
}


provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "kane-large-context"
}

provider "helm" {
  kubernetes {
    config_path    = "~/.kube/config"
    config_context = "kane-large-context"
  }
}


resource "helm_release" "eck-operator" {
  repository = "https://helm.elastic.co"
  chart      = "eck-operator"
  version    = "2.13.0"

  namespace        = "elastic-system"
  name             = "eck-operator"
  create_namespace = true

  values = [
    file("./values/eck-operator.yaml")
  ]
}


resource "kubernetes_manifest" "elasticsearch" {
  manifest = {
    apiVersion = "elasticsearch.k8s.elastic.co/v1"
    kind       = "Elasticsearch"
    metadata = {
      name      = "elasticsearch"
      namespace = "default"
    }
    spec = {
      version = "8.11.3"
      nodeSets = [
        {
          name  = "default"
          count = 1
          config = {
            "xpack.security.authc" = {
              anonymous = {
                username        = "anonymous"
                roles           = "superuser"
                authz_exception = false
              }
            }
            "node.store.allow_mmap" = false
          }
          volumeClaimTemplates = [
            {
              metadata = {
                name = "elasticsearch-data"
              }
              spec = {
                accessModes = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = "5Gi"
                  }
                }
                storageClassName = "cinder-tnt-csi-ay2dev"
              }
            }
          ]
        }
      ]
      http = {
        tls = {
          selfSignedCertificate = {
            disabled = true
          }
        }
      }
    }
  }
}

resource "kubernetes_manifest" "kibana" {
  manifest = {
    apiVersion = "kibana.k8s.elastic.co/v1"
    kind       = "Kibana"
    metadata = {
      name      = "kibana"
      namespace = "default"
    }
    spec = {
      version = "8.11.3"
      count   = 1
      elasticsearchRef = {
        name = kubernetes_manifest.elasticsearch.manifest.metadata.name
      }
    }
  }
}
