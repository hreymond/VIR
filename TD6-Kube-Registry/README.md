# TD6 - Kubernetes registry

Objectif du TD :
- :dart: Comprendre les dépôts locaux
- :dart: Déployer une application multi-pods avec Kubernetes

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

# Partie 2 : Déployer notre application

Désormais, nous avons tout les outils nécessaires au déploiement de notre site web "minecraft".
Par rapport au déploiement mis en place au TD3 à l'aide de docker-compose, le déploiement d'aujourd'hui :
- Contiendra deux réplicats de notre site web, et un load balancer pour équilibrer la charge entre les deux réplicats.
- Sera surveillé en permanence par Kube, qui veillera au bon fonctionnement de nos pods (Self-Healing)
- Permettra, lors de prochains TDs, d'héberger les réplicats sur des noeuds différents, et donc d'offrir une redondance multi-site
- Permettra d'augmenter très simplement le nombre de réplicats, à l'aide de la commande `kubectl scale`

À vous de jouer ! Créez les objets Kubernetes (Deployments, Services, HttpRoute) nécessaires à l'hébergement du site `website:v3` et de sa base de donnée.

Si vous souhaitez être guidé dans cette tâche, nous avons détaillé les grandes étapes à suivre ci-dessous. Vous pouvez aussi, si vous le sentez, vous passer de cette aide. Aussi, n'hésitez pas à demander de l'aide à vos chargés de TD.

## Déploiements

### Website:v3

Créer un déploiement pour héberger deux réplicats de notre site :

- Si nécessaire, reconstruire l'image `website:v3`
- Tagger l'image, et la pousser dans le registry créée précédemment
- Créer le déploiement correspondant à notre site (image website:v3, deux réplicats)

Tester le déploiement :
- Vérifier que les pods sont bien créés, et leur état. Si nécessaire, inspecter les logs du pod à l'aide de `kubectl logs <POD_ID>`.
- Vérifier qu'il est possible d'accéder au site à l'aide de l'IP du pod : `curl <POD_IP>:5000`

### Postgres

Créer un déploiement pour héberger la base de donnée postgres (image postgres, un réplicat). La base de donnée écoute par défaut sur le port 5432.

Comme précédement, il faudra définir la variable d'environnement `POSTGRES_PASSWORD` à `admin`. Pour cela, on utilisera la syntaxe suivante :

```yaml
containers:
  - name: bdd
    env:
      - name: ENV_VAR_NAME
        value: ENV_VAR_VALUE
    ...
```

Tester le déploiement :
- Vérifier que le pod est bien créé, et son état. Si nécessaire, inspecter les logs du pod à l'aide de `kubectl logs <POD_ID>`.
- Tester, depuis l'hôte, la connection à la base de donnée `pg_isready -h <host_name>`, en utilisant l'adresse IP du pod comme hostname.  L'installation de l'outil `pg_isready` est détaillée en fin de TD [Lien](#installation-de-pg_isready).

Pour le moment, il n'est pas possible pour les pods `website` de se connecter à la base de donnée. Pour permettre cela, il est nécessaire de définir un service pour postgres.

## Services

> [!NOTE]
> 
> Dans notre cas d'usage, nous allons créer deux services, avec des usages différents :
> - Postgres : Ce service, à usage interne, permettra d'offrir une ip stable et un nom de domaine pour que le site puisse se connecter à la base de donnée.
> - Website : Ce service aura pour rôle l'équilibrage de charge entre les deux réplicats de `website`, et de fournir un point d'entrée unique, stable, pour que l'on puisse y connecter une HTTPRoute.
>

### Postgres

Créer un service pour notre base de donnée, nommé `postgres`. Pour rappel, notre base de donnée écoute sur le port `5432`, et notre site tentera de se connecter sur ce même port.

Tester le service :
- Vérifier que le service est bien créé et son état.
- Vérifier que votre service est bien lié à vos pods. Indice: combien d'endpoints sont visibles lors d'un `kubectl describe` de votre service ?
- Tester, depuis l'hôte, la connection à la base de donnée, en utilisant l'IP du service comme hostname (à l'aide de `pg_isready`) .
- Tester le même chose depuis un des conteneurs `website`.
- Tester, depuis un des conteneurs `website`, la connection à la base de donnée, en utilisant le nom de domaine `postgres` comme hostname.

### Website

Créer un service pour notre site web.

Tester le service :
- Vérifier que le service est bien créé et son état.
- Vérifier que votre service est bien lié à vos pods. Indice: combien d'endpoints sont visibles lors d'un `kubectl describe` de votre service ?
- Tester, depuis l'hôte, à l'aide de `curl`, la connection au service. Rappel, la syntaxe est la suivante : `curl <IP>:<PORT>`
- Tester depuis un navigateur, que le site est accessible via l'IP du service, et qu'il fonctionne.

## HTTPRoute

Pour l'instant, notre site n'est pas accessible depuis l'extérieur du cluster.
En vous appuyant sur le dernier TD, créez une route qui permette d'accéder à votre site web.

:tada: Vous savez désormais déployer une application à l'aide de Kubernetes ! 

# Aller plus loin

- Volumes : ajouter un volume au pod `bdd`, pour que les données soient persistées. La gestion des volumes est par nature plus complexe avec Kubernetes, car deux pods qui partagent un volume ne sont pas forcément sur la même machine physique. On pourra regarder du côté des [Volumes Locaux](https://kubernetes.io/fr/docs/concepts/storage/volumes/#local) et des [HostPaths (équivalents de bind mounts dans docker)](https://kubernetes.io/fr/docs/concepts/storage/volumes/#hostpath)
- CronJob : Mettre en place la sauvegarde de la base de données, comme vous avez pu le faire avec `db-utils` dans le TD3. Pour cela, on utilisera des [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/), qui permettent de créer un pod à usage unique, qui exécutera une tâche et se stoppera. Pour aller plus loin, on pourra creuser du côté des [CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/), qui permettent de prévoir le lancement de Jobs à des dates/périodes prédéfinies.

## Comment nettoyer k3s 
Si vous voulez repartir d'une configuration propre de k3s, vous pouvez suivre les étapes suivantes.

Arrêter k3s en faisant un CTRL-C dans la fenêtre. 

Nettoyez votre installation de k3s avec les commandes suivantes :
```sh
k3s-killall.sh
\rm -rf /var/lib/rancher
\rm -rf /var/lib/kubelet
```

# Installation de pg_isready

## Installation

- `apt update`
- `apt install -y postgresql-client`

## Utilisation

Tester si une base de donnée postgres écoute sur un hôte `hostname` :

`pg_isready -h <host_name>`

En cas de succès, pg_isready indique : `<IP>:5432 - accepting connections`

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
