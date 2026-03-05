package agenticdeploy

default deny = false

# Example: deny privileged containers
deny {
  input.kind == "Deployment"
  some c
  input.spec.template.spec.containers[c].securityContext.privileged == true
}
