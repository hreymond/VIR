#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "Ce script (/home/user/startTraefik) doit être exécuté en tant que root (sudo su -)"
  exit
fi

#echo "Installation du CRD servicemonitoring de prometheus"
#kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml

echo "Installation de traefik"
helm repo add traefik https://traefik.github.io/charts
helm repo update

helm install traefik traefik/traefik --wait \
  --set ingressRoute.dashboard.enabled=true \
  --set ingressRoute.dashboard.matchRule='Host(`dashboard.localhost`)' \
  --set ingressRoute.dashboard.entryPoints={web} \
  --set metrics.prometheus.enabled=true \
  --set metrics.prometheus.service.enabled=true \
  --set metrics.prometheus.serviceMonitor.enabled=true \
  --set metrics.prometheus.addEntryPointsLabels=true \
  --set metrics.prometheus.addServiceLabels=true \
  --set metrics.prometheus.addRoutersLabels=true \
  --set providers.kubernetesGateway.enabled=true \
  --set gateway.listeners.web.namespacePolicy.from=All

echo "Patch du service monitor de traefik pour qu'il soit identifié dans prometheus"
kubectl label servicemonitor traefik release=prometheus

echo "Traefik installé."
echo "Vous pouvez tester le dashboard : curl dashboard.localhost/dashboard/"
#echo "Pour tester les metriques : kubectl port-forward deployments/traefik 9100:9100"
echo "Pour tester les metriques : kubectl get services"
echo "curl <ipduservicetraefik>:9100/metrics"
echo "Il faut vérifier que des metriques 'traefikxxx' existent"

echo "Si elles existent, vous pouvez vérifier si elles sont collectées par prometheus"

