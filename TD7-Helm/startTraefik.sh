#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "Ce script (/home/user/startTraefik) doit être exécuté en tant que root (sudo su -)"
  exit
fi

echo "Installation de traefik"
helm repo add traefik https://traefik.github.io/charts
helm repo update

helm install traefik traefik/traefik --wait \
  --set ingressRoute.dashboard.enabled=true \
  --set ingressRoute.dashboard.matchRule='Host(`dashboard.localhost`)' \
  --set ingressRoute.dashboard.entryPoints={web} \
  --set providers.kubernetesGateway.enabled=true \
  --set gateway.listeners.web.namespacePolicy.from=All


echo "Traefik installé."
echo "Vous pouvez tester le dashboard : curl dashboard.localhost/dashboard/"
