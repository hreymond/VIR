# TD6 - Kubernetes registry

Objectif du TD :
- :dart: Comprendre les dépôts locaux

# Partie 1 : Registry
Une image docker, podman, kubernetes (containerd) est stockée dans un repository. 
Par exemple lorsque vous récupérez l'image `traefik/whoami`, de la session précédente, celle-ci est puisée sur dans un dépot de référence comme docker.io
`https://hub.docker.com/r/traefik/whoami`.

Si vous souhaitez télécharger cette image vous pouvez passer la commande `podman pull <image>` comme indiqué sur le site.
:collision: Pullez l'image `traefik/whoami` (:question: Quel tag est récupéré ?)
Vous allez fabriquer vos propres images, il va être nécessaire d'exécuter votre propre registry. Voici les étapes

### Lancer et tester une registry locale

La registry est une application contenerisée. 
Vous pouvez lancer l'image `registry:2` dans une fenêtre avec la commande `podman run`.
La registry tourne sur le port conteneur `5000`. Vous pouvez décider de la lancer sur un autre port. 

Vous pouvez vérifier qu'elle s'est bien lancé avec la commandes  
`curl http://localhost:<portHost>/v2/_catalog`

Vous pouvez maintenant déposer une image dessus. 

Une solution simple est de marquer (`tag`) une image existante à votre nom et la déposer dans la registry. Une image docker doit avoir un nom complet selon la syntaxe suivante : <registry>/<namespace>/<imagename>:<tag>. Déposez l'image dans la registry `localhost:5010`, de namespace `tc`, ayant pour nom `whoami` et de tag `sfr`.   
`podman tag traefik/whoami <registryurl>/<ns>/<image>:<tag>`

Lorsque vous allez pousser l'image dans la registry vous allez avoir une erreur https vs http. Il faut modifier votre configuration podman afin de pouvoir déposer des images sans utiliser de protocole sécurisé. Pour cela vous devez modifier votre fichier `/etc/containers/registries.conf` pour y déclarer l'accès non sécurisé à votre registry. Il est inutile de relancer la registry

```
#/etc/containers/registries.conf
[[registry]]
location = "localhost:5010"
insecure = true
```

Vous pouvez pousser votre image
`podman push <url>/<ns>/<image>:<tag>`

Et vérifier que l'image est dans votre registry

`curl <url>/v2/_catalog`
`curl <url>/v2/<ns>/<image>/tags/list`

## Utiliser cette registry dans Kubernetes
Définissez un service `testwho` et un déploiement reposant sur l'image que vous venez de pousser. 
Dans votre yaml, doit apparaitre une spécification de la forme :
````
...
containers: 
- name: whoami
  image: <url>/<image>
```

Déployez les pods et le service / testez avec la commande suivante : 
`curl `kubectl describe service testwho | grep 'IP:'| cut -d ':' -f 2``

La réponse doit être du style :
```
Hostname: 127.0.0.1
IP: ::1
IP: xx.xx.xx.xx
...
````


## Utilisation d'une registry commune
Kubernetes est une infrastructure de simplification du run. Dans l'exemple précédent, la mise à disposition de l'image se fait sur une registry que vous identifiez de manière unique et précise par son IP ou son nom comme localhost. Mais les images sont indépendantes de vos registry. Vous pouvez stocker une image postgres ou whoami sur votre infrastructure. 

Dans cet exercice, nous modifions le descripteur de déploiement afin d'utiliser l'image `maboite.hj/tc/whoami:sfr`. C'est-à-dire votre image précédente mais que vous stockeriez sur une autre registry.

```yaml
# whoami.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whoami
spec:
  replicas: 2
  selector:
    matchLabels:
      app: whoami
  template:
    metadata:
      labels:
        app: whoami
    spec:
      containers:
        - name: whoami
          image: maboite.hj/tc/whoami:sfr
          ports:
            - containerPort: 80
```

Déployez cette image et vérifiez que cela ne fonctionne pas. Pour corriger cela, vous devez indiquer dans un fichier de configuration de k3s, comment résoudre vos registry d'image. 
Le fichier à définir est le fichier `/etc/rancher/k3s/registries.yaml`. Dont la syntaxe est décrite [ici](https://docs.k3s.io/installation/private-registry).

# Partie 2 - Helm

Description de Helm 
- Gestionnaire de Packet
- En pratique, quand on héberge une application, on ne va pas modifier les descripteurs yaml

## Chart Helm

- Examinger les deployment et service 

```yaml
# Templating
# Macro de base, définies dans `_helpers.tpl`
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "helm-app.fullname" . }}
```

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

# Partie 3 - Packager notre application

Dossier `minecraft-app`
-> Chart Helm incomplet
  -> Paramètres définis dans `values.yaml`
  -> Aucun templates, seulement le fichier `_helpers.tpl`, et les notes de déploiement

## Comment nettoyer k3s 
Si vous voulez repartir d'une configuration propre de k3s, vous pouvez suivre les étapes suivantes.

Arrêter k3s en faisant un CTRL-C dans la fenêtre. 

Nettoyez votre installation de k3s avec les commandes suivantes :
```sh
k3s-killall.sh
\rm -rf /var/lib/rancher
\rm -rf /var/lib/kubelet
```


# Liste des commandes utiles
```
podman pull <image:tag>  ---> podman pull docker.io/traefik/whoami
podman run -p <portHote:portGuest> <nomImage> --> podman run -p 5010:5000 registry:2 


kubectl get deployement
kubectl delete deployement <deploymentname>

kubectl apply -f <descripteur.yaml>
kubectl describe pod <podId>
kubectl get pods

kubectl get endpoints
kubectl get endpointslices

kubectl scale deployment <deploymentId> --replicas=<#>`

crictl ps
crictl exec -it <contenerId> /bin/bash

echo "xxx" > /usr/share/nginx/html/index.html

helm repo update
helm uninstall <xxx>
helm install <xxx>
curl -H "Host: whoami-gatewayapi2.toto" 10.56.171.180 
```
