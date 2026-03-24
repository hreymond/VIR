#!/bin/sh
# Simple installation of kube-prometheus stack
# https://github.com/prometheus-community/helm-charts/blob/main/charts/kube-prometheus-stack/README.md
# helm show values --> Pour récupérer les valeurs 
#
# Récupérer le mot de passe : admin de graphana
# kubectl get secrets prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo
# 
# ouvrir le port de graphana
# export POD_NAME=$(kubectl --namespace default get pod -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=prometheus" -oname)
# kubectl --namespace default port-forward $POD_NAME 3000


helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack -f /home/user/prometheus-simple.yaml

#kubectl port-forward prometheus-prometheus-kube-prometheus-prometheus-0 9090:9090

