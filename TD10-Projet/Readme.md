# TD10 - Cluster et Affinités

Une des grandes forces de Kubernetes est de pouvoir répartir la charge de travail entre différents serveurs, localisés à différents endroits.
Jusqu'à présent, vous avez travaillé avec chacun votre propre cluster. Aujourd'hui, nous allons voir comment construire un cluster qui s'étends à travers plusieurs machines.

## Votre cluster

Organisez-vous par groupe de 6. 5 machines formeront le cluster, et la dernière servira à tester les performances de votre infrastructure

> ![NOTE]
>
> Agent vs Serveur
>
> ??
>


![IMAGE DU CLUSTER FINAL]()

5 machines serviront le cluster, 
3 machines comme serveur
et 2 machines comme agent

La dernière machine sert de machine de stress. 

L'objectif est de monter un benchmark, permettant de tester votre infrastructure. 

## Mise en place du cluster

### Avant de lancer les 

### Tester la connectivité entre les machines

-> On commence par ping ?

-> On enchaîne avec un curl sur les différentes interfaces ? 


Protocol	Port	Source	Destination	Description
TCP	6443	Agents	Servers	K3s supervisor and Kubernetes API Server
UDP	8472	All nodes	All nodes	Required only for Flannel VXLAN
TCP	10250	All nodes	All nodes	Kubelet metrics and API

### Lancer les serveurs

Commencer par lancer les serveur.

Pour les étudiants qui auront le rôle de serveur, modifiez le script `startk3sServer.sh` pour ajouter l'argument `--node-name <Nom du noeud>` qui nommera votre noeud.

Ensuite lancez le serveur `k3s` et partagez votre IP aux autres membres du groupe.

Une fois les serveurs démarrés, les autres membres du groupe vérifient que le port 6443, utilisé par l'API Kube, est bien accessible : `curl -k <IP SERVER>:6443` 

Curl doit vous renvoyer un JSON de ce type,  e qui signifie que l'API Kubernetes est bien fonctionnelle, mais que vous n'êtes pas autorisé à y accéder. Nous verrons plus tard comment récupérer les identifiants de connection : 

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

### Lancer les agents


Pour les étudiants qui auront le rôle de server, modifier le script `startk3sagent.sh` pour deux arguments à k3s :
- l'argument `--node-name <Nom du noeud>` pour nommer votre noeud.
- l'argument `--tls-san <IP SERVEUR>` pour permettre la connection de kubectl depuis l'extérieur (Par défaut, le certificat HTTPS qui sécurise la connexion au cluster n'est valide que pour `localhost`)

:question: Quelle variable d'environnement est utilisée par le script pour définir l'IP du server ? Définissez à la (`export VAR=value`)

### 

Sur l'instance du serveur :

# Check all nodes

sudo k3s kubectl get nodes
> Expected output:
> NAME STATUS ROLES AGE VERSION
> server-node Ready control-plane,master 1h v1.x.x
> student2-node Ready <none> 2m v1.x.x
> student3-node Ready <none> 1m v1.x.x


Sur les agents, si vous lancez la même commande, échec : kubectl cherche à joindre l'API Kube en local (127.0.0.1:6443), mais c'est uniquement le serveur qui est en mesure de traiter les appels API Kube.

Partagez entre les étudiants ca

- Sur le serveur : `sudo cat /etc/rancher/k3s/k3s.yaml`, partager le contenu du fichier avec les autres étudiants
- Sur les agents, on va récupérer la configuration de k3s et la copier dans le fichier `/home/user/.kube/config.yaml` : 
  Dans votre dossier `home`
  - `mkdir .kube`
  - `vim .kube/config.yaml` : copiez la configuration du serveur, et remplacez `127.0.0.1` par l'IP du serveur
  - `export KUBECONFIG=/home/user/.kube/config.yaml`