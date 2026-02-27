# TD7 - Packaging with Helm

Maintenant que notre site peut être déployé sur Kubernetes, on souhaite le partager à notre communauté.



# Partie 1 - Helm : Un gestionnaire de paquet comme les autres ?

Lorsque l'on souhaite installer des applications et leur dépendances de manière automatique sur nos machines personnelles, on se repose souvent sur des gestionnaires de paquets comme APT (debian), PIP (python). Dans l'écosystème *Kubernetes*, l'outil de référence pour packager et partager des configurations Kubernetes se nomme *Helm*. Par exemple, une seule commande `helm install` permet d'installer sur un cluster des utilitaires comme Traefik (cf TD5), ou des applications comme nextcloud (clone ouvert de google docs).

Nous allons l'utiliser pour partager notre site.


## Helm - Concepts importants

Dans le langage Helm, un paquet est appelé un *Chart*. Un *Chart* est un ensemble de fichiers qui décrivent des ressources Kubernetes.
Cependant, par rapport aux gestionnaires de paquet actuels, Helm permet :
- de paramétrer l'installation d'un Chart, en modifiant sa *configuration*
- d'installer plusieurs instance d'un même Chart, avec des configurations différentes. Chaque installation d'un Chart donne lieue à la création d'une *Release*

---

Exemple de Release 
- Version de développement : `helm install dev ./my-chart`
- Version de production : `helm install prod ./my-chart --set debug=false`

Deux *Releases*, `dev` et `prod`,  même chart `my-chart`, configuration différente 

![Concepts Helm](helm-concepts.png)

## Chart Helm

Le dossier `helm-app` représente un exemple simple d'un Chart. Comme tous les Charts Helm, sa structure est la suivante :
- helm-app/Chart.yaml : Les métadonnées du Chart. Ce fichier contient entre autre le nom et la version du Chart
- helm-app/values.yaml : La configuration par défaut du Chart. Les paramètres définis dans ce fichier seront utilisés dans les templates.
- helm-app/templates/ : Les templates de ressources kubernetes (pods, services, deploiements, ...).

Commençons par étudier le format d'un template, avec le début du fichier `deployment.yaml` :

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: "{{ .Chart.Name  }}-{{ .Release.Name  }}"
  labels:
    app: helm-demo
spec:
  replicas: {{ .Values.replicaCount }}
  ...
```

Ce template est une déclaration de deploiement Kubernetes classique, mais agrémenté de balise de templating GO : `{{ PARAMETER }}`.
Toutes les balises vont être remplacées par des valeurs définies dans le Chart, ou générées. Pour cela, Helm fourni trois variables `Chart`, `Release` et `Values` :
- `.Chart` : fait référence au contenu du fichier `chart.yaml`. :question: Par quoi va être remplacé la balise `{{ .Chart.Name }}` ?
- `.Release` : permet d'accéder aux informations sur la Release courante (`Name`, `Namespace`, ...).
- `.Values` : fait référence aux éléments de configuration définis dans le fichier `values.yaml`. :question: Par quoi va être remplacé la balise `{{ .Values.replicaCount }}` ?


Essayons maintenant de déployer les ressources déclarées dans le dossier `templates`, en installant le Chart.

Si vous utilisez la clé K3S fournie par le département, helm y est déjà installé. Sinon, les instructions sont disponibles [ici](https://helm.sh/docs/intro/install/).

Helm doit se lancer en super utilisateur, et a besoin de connaitre la configuration k3s : 

```bash
sudo su -
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml # Cette instruction indique à helm la configuration pour dialoguer avec kubernetes
helm list # Pour vérifier l'installation, listez les release installées. Si une erreur apparait, appelez le chargé de TD.
```

Nous pouvons maintenant installer notre Chart, et nous nommerons notre release `toto`.

:question: Quel sera le nom complet du déploiement présenté plus tôt avec cette release ?

Dans le dossier TD7-Helm, en superuser : `helm install toto ./helm-app`

Vérifier que votre release a bien été déployée avec `helm list`

Vérifiez via `kubectl` qu'il existe un déploiement correspondant à ce que vous attendiez :
- Le nom du déploiement correspond à celui attendu
- Le nombre de réplicas correspond à celui attendu

## Paramétrage d'un Chart

On a utilisé la config par défaut, définie par values.yaml

En général, on veut personnaliser le chart.

Pour ça, deux options : passer les paramètres en liste de commande, ou fournir un fichier values, qui fusionnera avec le fichier par défaut.

- En ligne de commande : `helm install <name> <chart> --set key1=val1,key2=val2`
- Via un fichier de valeurs : `helm install <name> <chart> --values config.yaml`

Installer une seconde release de notre application, appelée `toto2`, qui possèdera deux réplicas de notre pod, via la ligne de commande.
Via un fichier de valeurs, installer une troisième release appelée `toto3`, avec trois réplicas.


## Mise à jour d'un Chart

Mise à jour chart, solution la plus basique :
- Désinstallation : `helm uninstall`
- Installation : `helm install`

Problème ! 


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


## Déploiement 


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

1. Modifier les manifests Helm du précédent TD pour pouvoir paramétrer les valeurs suivantes, définies dans `values.yaml` :

Lancer : est-ce que ça marche ?

Upgrade + Override les valeurs par défaut, hostname à "steve.localhost" -> Plus simple que d'aller fouiller dans les manifests ! 

2. Lancer une deuxième release 

Conflits ! "service postgres already exists !" 
Une limite supplémentaire de gérer les manifests à la main : Besoin de copier les manifests et de paramétrer à chaque fois que l'on veut une instances différente de notre site.

Heureusement, Helm fourni des helpers pour générer des noms à partir du nom de la release

# Liens

- [Documentation du templating Helm](https://helm.sh/docs/chart_template_guide/)

# Commandes utiles

```bash
kubectl get deployment
kubectl delete deployment <deploymentname>

kubectl apply -f <descripteur.yaml>
kubectl describe pod <podId>
kubectl get pods

kubectl get endpoints
kubectl get endpointslices

kubectl scale deployment <deploymentId> --replicas=<#>`
```