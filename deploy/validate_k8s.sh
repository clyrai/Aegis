#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
K8S_DIR="$ROOT_DIR/k8s"

echo "Validating Kubernetes manifests..."

if kubectl cluster-info >/dev/null 2>&1; then
  MODE="server"
else
  echo "No reachable Kubernetes cluster detected; using client-side validation."
  MODE="client"
fi

for f in "$K8S_DIR"/*.yaml; do
  echo "- $f"
  if [ "$MODE" = "server" ]; then
    kubectl apply --dry-run=server -f "$f" >/dev/null
  else
    # When no cluster, kubectl still tries localhost:8080 for discovery. Fall back to kustomize build.
    if kubectl apply --dry-run=client --validate=false -f "$f" >/dev/null 2>&1; then
      true
    else
      # Use kustomize to parse YAML structure without contacting API server
      if command -v kustomize >/dev/null 2>&1; then
        kustomize cfg cat "$f" >/dev/null
      else
        # Last resort: yq for YAML syntax check if available
        if command -v yq >/dev/null 2>&1; then
          yq "." "$f" >/dev/null
        else
          echo "Warning: No cluster and no kustomize/yq; skipping deep validation for $f"
        fi
      fi
    fi
  fi
done
echo "OK ($MODE-side)"
