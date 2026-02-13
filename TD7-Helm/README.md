# TD7 - Packaging with Helm

Maintenant que notre site peut être déployé sur Kubernetes, on souhaite le partager à notre communauté.

L'outil de référence pour packager et partager des configurations Kubernetes se nomme *Helm*. Nous allons l'utiliser aujourd'hui.

# Partie 1 - Helm

Description de Helm 
- Gestionnaire de Packet (comme pip, apt mais pour Kubernetes)
- Pourquoi on a besoin d'un gestionnaire de paquet ? En pratique, quand on héberge une application, on cherche quelque chose clé en main,  qu'on peut lancer en une commande. De plus, on cherche à pouvoir paramétrer assez simplement ces applications, sans avoir à examiner les objets Kubernetes décrits en Yaml.


## Installation

Installation :
- `export KUBECONFIG=/etc/rancher/k3s/k3s.yaml`
- Si clé K3S, rien à faire
- Sinon, regarder : https://helm.sh/docs/intro/install/

## Chart Helm

Pour packager un deploiement, Helm utilise des Charts. Un Chart est un ensemble de fichier qui décrivent des ressources Kubernetes. Un Chart peut aussi bien décrire un simple pod affichant "hello world", ou une application web complète avec serveur HTTP et base de donnée.

Le dossier helm-app représente un exemple simple d'un Chart. Comme tous les Charts Helm, sa structure est la suivante :
- helm-app/Chart.yaml : Les métadonnées du Chart. Ce fichier contient entre autre le nom et la version du Chart
- helm-app/values.yaml : Les paramètres par défaut du Chart. Ces paramètres seront utilisés dans les templates.
- helm-app/templates/ : Les templates de ressources kubernetes (pods, services, deploiements, ...).

Commençons par étudier le format d'un template, avec le début du fichier `deployment.yaml` :

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "helm-app.fullname" . }}
  labels:
    app: helm-demo
spec:
  replicas: {{ .Values.replicaCount }}
```

Ce template est une déclaration des deploiement Kubernetes classique, mais agrémenté d'élements de templating GO : `{{ PARAMETER }}`.

Par exemple, le nombre de réplicats du déploiement est remplacé par la valeur `{{ .Values.replicaCount }}`. 

:question:  `helm-app.fullname` est une macro définie dans `_helpers.tpl`. Retrouvez la. De quoi est composé le full-name ?

```yaml
# Utilisations des "valeurs"
    spec:
      containers:
      - name: web
        image: "{{ .Values.image.name }}:{{ .Values.image.tag }}"
        ports:
        - containerPort: 80
```

:question: Trouvez dans les fichiers de template à quoi correspondent les différentes options présentes dans le `values.yaml` ?

## Ajouter un template

Dans le TD précédent, nous avons vu comment définir une GatewayAPI pour accéder à une application depuis l'extérieur du cluster.

Reprenons la définition d'une HTTPRoute du TP précédent :

```yaml
# httproute.yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: whoami
spec:
  parentRefs:
    - name: traefik-gateway
  hostnames:
    - "whoami-gatewayapi.localhost"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: whoami
          port: 80
```

Modifiez cette définition pour en faire un template pour notre application nginx. 
Le paramétrage de ce template se fera de cette manière :

```yaml
# Dans values.yaml
route:
  hostname: "monsupersite.localhost"
  path: "/site"
```

# Partie 2 - Packager notre application

Dossier `minecraft-app`
-> Chart Helm incomplet
  -> Paramètres définis dans `values.yaml`
  -> Aucun templates, seulement le fichier `_helpers.tpl`, et les notes de déploiement