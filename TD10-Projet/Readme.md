# TD10 - Cluster et Affinités

Une des grandes forces de Kubernetes est de pouvoir répartir la charge de travail entre différents serveurs, localisés à différents endroits.
Jusqu'à présent, vous avez travaillé avec chacun votre propre cluster. Aujourd'hui, nous allons voir comment construire un cluster qui s'étend à travers plusieurs machines.

## Votre cluster

Organisez-vous par groupe de 6. 5 machines formeront le cluster, et la dernière servira à tester les performances de votre infrastructure

:warning: Utilisez impérativement la clé du département, et pas une VM pour éviter les problèmes de pare-feu. Si la clé ne fonctionne pas sur votre machine, vous prendrez le rôle de machine de test de charge.

> [!NOTE]
>
> Rôle d'un noeud : Agent vs Serveur
>
> **Noeud agent**
> Le noeud agent s'occupe uniquement de la gestion de pods. 
> Pour cela, il est composé de différents éléments :
> - Un démon nommé *kubelet*, qui est controllé par le serveur, et qui est en charge de créer et démarrer les pods 
> - Un moteur de conteneurs (*container engine*), dans notre cas `containerd`, utilisé par le *kubelet* pour créer des conteneurs. 
> - Un composant responsable de la mise en réseau de tous les pods à travers le cluster, le *kube-proxy*
> 
>
> **Noeud serveur**
> 
> Un noeud serveur contrôle et gère le cluster. 
> Il est composé des éléments suivants :
>   - L'ordonnanceur, ou *scheduler*, qui détermine sur quel machine un nouveau pod s'exécutera,
>   - La base de données (etcd), qui stocke l'état souhaité de notre cluster,
>   - Les controlleurs (*controllers*), qui vérifient constamment si le cluster correspond aux descriptions yaml stockées en BDD.
> Ce noeud est aussi un point d'entrée de l'API Kube (kubeapi, utilisée par kubectl). De plus, comme tout les noeuds k3s, gérer les pods. On détaille cet aspect dans la présentation du noeud agent. 
> 

Pour notre cluster, on utilisera 3 machines comme serveur et 2 machines comme agent.
La dernière machine sera utilisée pour tester la charge qui testera votre infrastructure.

## Mise en place du cluster

### Tester la connectivité entre les machines

Vérifiez tout d'abord s'il est possible pour chacune des machines de se pinguer.

### Lancer les serveurs

Commençons par lancer les serveur.

On commencera par un premier serveur, et les autres serveurs viendront s'y connecter
Pour les étudiants qui auront le rôle de serveur, modifiez le script `startk3sServer.sh` pour ajouter trois arguments à k3s :
- l'argument `--node-name <Nom du noeud>` pour nommer votre noeud.
- l'argument `--tls-san <IP SERVEUR>` pour permettre la connection de kubectl depuis l'extérieur (Par défaut, le certificat HTTPS qui sécurise la connexion au cluster n'est valide que pour `localhost`)
- pour le noeud serveur 1, l'argument `--cluster-init`, qui permet d'avoir plusieurs noeuds serveur
- pour les noeuds serveurs 2 et 3, l'argument `--server https://<IP du serveur 1>:6443` pour rejoindre le cluster existant.
Ensuite lancez le serveur `k3s` et partagez votre IP aux autres membres du groupe.

Une fois les serveurs démarrés, les autres membres du groupe vérifient que le port 6443, utilisé par l'API Kube, est bien accessible : `curl -k https://<IP SERVER>:6443` 

Curl doit vous renvoyer un JSON de ce type, ce qui signifie que l'API Kubernetes est bien fonctionnelle, mais que vous n'êtes pas autorisé à y accéder. Nous verrons plus tard comment récupérer les identifiants de connection : 

```json
{
  "kind": "Status",
  "apiVersion": "v1",
  "metadata": {},
  "status": "Failure",
  "message": "Unauthorized",
  "reason": "Unauthorized",
  "code": 401
}
```

Pour les serveurs, vous pouvez observer l'état du cluster avec `sudo kubectl get nodes`. Pour les agents, nous verrons cela plus tard.

Vous devriez obtenir un résultat similaire à :
```
NAME   STATUS   ROLES                AGE   VERSION
server3   Ready    control-plane,etcd   17m   v1.34.3+k3s1
server2   Ready    control-plane,etcd   18m   v1.34.3+k3s1
server1   Ready    control-plane,etcd   39m   v1.34.5+k3s1
```

### Lancer les agents

Pour les étudiants qui auront le rôle d'agent, modifier le script `startk3sagent.sh` pour ajouter l'argument `--node-name <Nom du noeud>` qui nommera votre noeud.

:question: Quelle variable d'environnement est utilisée par le script pour définir l'IP du server ? Définissez-la (`export VAR=value`)


### Vérifier le bon état du cluster

Maintenant que notre cluster est totalement démarré, sur les noeuds serveurs, vérifiez que la commande `sudo kubectl get nodes` retourne un résultat similaire à :

```
NAME   STATUS   ROLES                AGE   VERSION
agent1   Ready    <none>                 1m   v1.34.3+k3s1
agent2   Ready    <none>                 2m   v1.34.3+k3s1
server1   Ready    control-plane,etcd   39m   v1.34.5+k3s1
server2   Ready    control-plane,etcd   18m   v1.34.3+k3s1
server3   Ready    control-plane,etcd   17m   v1.34.3+k3s1
```

Sur les agents, si vous lancez la même commande, échec : kubectl cherche à joindre l'API Kube en local (127.0.0.1:6443), mais c'est uniquement les noeuds serveurs qui sont en mesure de traiter les appels API Kube.

Pour que tout le monde dans le groupe puisse utiliser kubectl, nous allons partager la configuration de k3S entre les agents et la machine de test 

- Sur un des serveur : `sudo cat /etc/rancher/k3s/k3s.yaml`, partager le contenu du fichier avec les autres étudiants et notez l'adresse IP du serveur
- Sur les agents, on va récupérer la configuration de k3s et la copier dans le fichier `/home/user/.kube/config.yaml` : 
  Dans votre dossier `home`
  - `mkdir .kube`
  - `vim .kube/config.yaml` : copiez la configuration du serveur, et remplacez `127.0.0.1` par l'IP du serveur
  - `export KUBECONFIG=/home/user/.kube/config.yaml`

## Test du cluster

### Mise en place de l'environnement de test

Répartissez vous le travail pour : 

- Installer Prometheus
- Installer Traefik
- Déployer website avec 
  - 4 pods website
  - 1 pod postgres

Pour générer de la charge, la machine de test pourra utiliser :
- `ab`, utilisé dans le TD supervision
  - `ab -n 10000 -c 10 -s 50000 -H "Host: minecraft.localhost" "http://<monPoteIp>/display_skin?username=toto"`
- `hey`, un générateur de charge similaire à ab. Contrairement à ab, `hey` supporte les requêtes qui timeout
  - `sudo apt update; sudo apt install hey`
  - `hey -c 20 -t 2 -z 1h -host minecraft.localhost "http://<CLUSTER-IP>/display_skin?username=Aypierre"`
- `locust`, un générateur de pic de charge réaliste : [Documentation](https://docs.locust.io/en/stable/what-is-locust.html)

Pour visualiser l'état du cluster en temps réel, vous pouvez utiliser `k9s` : `sudo k9s -r 0.2 --kubeconfig <fichier config k3s.yaml>` (rafraichissement tout les 200ms)

### Évaluation du cluster

Évaluez votre cluster selon les critères présentés ci dessous :

1. Analyse de la performance de `website`
   - Combien de requêtes par seconde peut traiter website ?
   - Quelle est la latence moyenne pour le traitement d'une requête dans différentes conditions (charge faible, charge importante)
2. Analyse de l'impact de la perte d'un noeud agent k3S
   - Comment simuler la perte d'un agent k3s ?
   - Que ce passe-t-il lorsqu'un agent k3s tombe ? Combien de temps met le cluster à réaliser la perte de l'agent ?
   - Que fait le cluster une fois qu'il réalise que l'agent n'est plus joignable
   - Observe-t-on des interruptions de service si un des noeuds qui héberge uniquement des pods website tombe ?
   - Observe-t-on des interruptions de service si le noeud qui héberge le pod postgres tombe ?


## En cas de problème :

- Reset la base de donnée d'un noeud : `sudo rm -rf /var/lib/rancher/k3s/server/db/`
- Nettoyer tout : `sudo rm -rf /var/lib/rancher/k3s/`

