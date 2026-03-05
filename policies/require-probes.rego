package agenticdeploy

default deny = false

# Example: require readinessProbe
deny {
  input.kind == "Deployment"
  some c
  not input.spec.template.spec.containers[c].readinessProbe
}
