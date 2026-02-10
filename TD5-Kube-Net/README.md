# TD5 - Kubernetes net

Objectif du TD :
- :dart: Comprendre la partie réseau de kube

## Partie 1 : Déploiement local et jouons avec les pods

Nous allons repartir d'un déploiement initial simple. 
Vérifiez que votre système kube n'a pas de déployement en cours d'exécution (`kubectl get deployment`, `kubectl delete deployment <name>`
), puis déployez le descripteur suivant (`kubectl apply -f <descripteur.yaml>).

```yaml
# Simple application with service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: steph-1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: prf
  template:
    metadata:
      labels:
        app: prf
    spec:
      containers:
      - name: web
        image: nginx:stable
```

Définissez un second descripteur `steph-2` avec un seul réplicat de label app = `elp`. Deployez le second descripteur. 
Votre système doit contenir :    
 - 1 noeud : `kubectl get nodes`   
 - 3 pods : `kubectl get pods`    
 - 2 replicatSet : `kubectl get rs`    
 
:question: A quoi correspond un replicatset ?   

A l'aide de la commande `kubectl describe pods <podId>` identifiez les adresses ip internes du cluster qui permet de joindre les différents pods.    
A l'aide de la commande `curl`, testez ces différentes adresses et vérifiez que le serveur nginx répond bien.    
A l'aide de la commande `crictl` modifiez le serveur du service `elp` afin que sa page web réponde "Bonjour ELP". La page html servie par nginx est stockée dans le répertoire `/usr/share/nginx/html/`.


La notion de service permet de fournir une adresse unique sur un replicatSet. En effet, un pods n'a aucune garantie de durée de vie. Les évolutions font que les pods sont remplacés à n'importe quel moment (pour différentes raisons).

:warning: Attention, veillez à ne pas redéployer votre pod `elp`.
En partant de la définition de service de la dernière séance, définissez un service d'accès aux pods `prout`.
:question: comment savoir qu'un service ne trouve pas de pods ?

Corrigez votre service afin qu'il trouve le service `elp`.
En utilisant la commande `curl`, vérifiez que vous obtenez bien "Bonjour ELP" sur l'adresse unique.


Augmentez le nombre de replicats avec la commande suivante : 
`kubectl scale deployment steph-2 --replicas=3`   

En utilisant la commande `curl`, observez ce qu'il se passe.   
:question: Est-ce conforme à vos attentes ?    

Passez à 0 replicas, vérifiez que cela colle bien,    
puis revenez à 1 replicas. testez.  
Enfin remettez 6 replicas et vérifiez que votre description de service colle bien à votre spécification.   

Listez les endpoints.

## Partie 2 : Accès distant
 
Afin de mettre à disposition une application il faut passer par un gestionnaire de trafic. K3s repose sur [traefik](https://doc.traefik.io/traefik/).

Elle semble avoir quelques soucis et nous suggérons de ne pas l'installer par défaut en utilisant l'option `--disable=traefik` puis d'installer la dernière version après démarrage.

- Arrêter k3s
- Modifier le script `startk3sServer.sh` pour ajouter l'option `--disable=traefik` au lancement de k3s.
- Relancer k3s, avec le script `startk3sServer.sh`

### Installation de traefik

Pour utiliser traefik nous allons suivre le [tutoriel standard](https://doc.traefik.io/traefik/getting-started/kubernetes/) en passant par helm. C'est un gestionnaire de déploiement pour Kube.   
Les commandes pour installer la dernière version de traefik sont les suivantes : 

```sh
sudo su -
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml # Cette instruction indique à helm la configuration pour dialoguer avec kubernetes
helm repo add traefik https://traefik.github.io/charts # Cette instruction indique les repository helm utilisés. C'est la même technique que pour les repo apt
helm repo update
```

Pour installer traefik, nous allons lui préciser un environnement spécifique. L'environnement peut être indiqué par des options de lancement, ou dans un fichier de description yaml.   
Le fichier suivant contient les paramètres de démarrage de traefik. 

```yaml
# values.yaml
ingressRoute:
  dashboard:
    enabled: true
    matchRule: Host(`dashboard.localhost`)
    entryPoints:
      - web
providers:
  kubernetesGateway:
    enabled: true
gateway:
  listeners:
    web:
      namespacePolicy:
        from: All
```

Ce fichier indique que traefik présente un dashboard accessible via une `ingressRoute` et que l'utilisation des accès via `GatewayAPI` sera également possible. 

Installez traefik avec la commande suivante : `helm install traefik traefik/traefik -f values.yaml --wait`  
Verifiez rapidement l'installation avec la commande `kubectl describe GatewayClass traefik`    

:warning: Attention il faut réfléchir 2s.   
Enfin assurez-vous d'accèder au dashboard [http://dashboard.localhost/dashboard/](http://dashboard.localhost/dashboard/).

Si vous accèdez à un dashboard, vous pouvez aller vers la suite.

### Mise à disposition de service

Si traefik est installé et que la GatewayClass est active, vous pouvez déclarer de nouveau accès à des services.

Nous vous proposons d'utiliser deux services pour tester deux techniques d'accès. Les IngressRoute et la GatewayAPI. 

Définir un service. Pour rappel un service est un point d'accès unique interne (via une IP fixe) sur un `replicas set` de conteneurs. (Méditez bien cette phrase).    


Pour mettre un service à disposition, il faut décrire le déploiement du conteneur répliqué ainsi que le service qui 'stabilise' le replicas set.

Définissez le déploiement et le service dont le conteneur `traefik/whoami` à la description suivante :  

```yaml
- name: whoami
  image: traefik/whoami
  ports:
    - containerPort: 80 
```

Lorsqu'il est invoqué ce conteneur répond de la manière suivante : 
```sh
curl xx.xx.xx.xxx

Hostname: whoami-712342182-8tv2h
IP: 127.0.0.1
IP: ::1
...

```
Si le déploiement fonctionne, vous pouvez maintenant définir un service `whomami` permettant d'y accéder via une IP unique. Notez que pour l'instant le nom sert juste à identifier les objets dans l'infra kube.

Gardez une copie de vos fichiers de déploiement et de service...

### Route d'accès
Lorsque vous ête sur k3s, il existe au moins 3 manières pour définir des routes d'accès au services. Les Ingress, les IngressRoute et la GatewayAPI.    
- Les Ingress sont définis par Kubernetes, mais ne sont plus limité et conservés pour des raisons historiques.    
- Les IngressRoute sont spécifiqus à Traefik. Elles reposent sur les Objets Kube Ingress et sont utilisés par exemple pour le dashboard que vous venez d'utiliser. 
- La GatewayApi répond aux nouveaux besoins et à la spécification poussée par Kubernetes. Nous passerons donc par la GatewayAPI pour consulter à distance notre service whoami. 


Le fichier de configuration type est le suivant : 
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

Créez ce fichier et installez le sur votre serveur. Si tout se passse bien vous devriez voir votre dashboard se mettre à jour d'une nouvelle configuration.


Vous pouvez tester l'accès à votre application de votre machine. Mais surtout vous pouvez tester l'application à partir d'une autre machine. 

Jusqu'à présent nous avons utilisé `curl` pour tester l'accès à un site directement via son IP. Cependant, Traefik route le trafic en fonction du nom de domaine indiqué dans la requête, il est donc nécessaire de l'indiquer à `curl`

:question: Quel est le nom de domaine attaché à notre route ?

Depuis votre machine, accédez au site whoami à l'aide de la commande `curl`

Pour tester l'application du voisin, il est nécessaire de fournir à `curl` deux informations :

- Le nom de domaine de l'application
- L'adresse IP du voisin, car aucun enregistrement DNS ne lie le nom de domaine à cette IP.

Pour cela, on utilisera l'option `-H` de `curl`, qui permet de spécifier le contenu du header HTTP.

`curl -H "Host: <Nom de domaine de whoami>" <IP serveur>`

Utilisez l'outil `ab` pour tester la machine du voisin. 

# Liste des commandes utiles
```
kubectl get deployment
kubectl delete deployment <deploymentname>

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
