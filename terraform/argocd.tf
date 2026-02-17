resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  namespace        = "argocd"
  create_namespace = true
  version          = "5.51.6"

  depends_on = [module.eks]

  set {
    name  = "server.service.type"
    value = "LoadBalancer"
  }
  
  set {
    name  = "server.extraArgs"
    value = "{--insecure}"
  }

  values = [
    yamlencode({
      server = {
        extraObjects = [
          {
            apiVersion = "argoproj.io/v1alpha1"
            kind       = "Application"
            metadata = {
              name      = "opsguardian"
              namespace = "argocd"
            }
            spec = {
              project = "default"
              source = {
                repoURL        = "https://github.com/${var.github_repo}.git"
                targetRevision = "main"
                path           = "charts/opsguardian"

                helm = {
                  parameters = [
                    {
                      name = "slack.webhookUrl"
                      value = var.slack_webhook_url
                    }
                  ]
                }
              }
              destination = {
                server    = "https://kubernetes.default.svc"
                namespace = "default"
              }
              syncPolicy = {
                automated = {
                  prune    = true
                  selfHeal = true
                }
                syncOptions = ["CreateNamespace=true"]
              }
            }
          }
        ]
      }
    })
  ]
}