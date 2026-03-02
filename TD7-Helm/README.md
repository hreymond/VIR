# TD7 - Packaging with Helm

Objectifs : 
- :dart: Prendre en main l'outil Helm
- :dart: Packager une application Kubernetes sous la forme d'un Chart Helm

# Partie 0 - Installation préliminaire
La nouvelle version de k3s, est installé sans le support de traefik par défaut. Nous vous suggérons de passer root et de lancer l'installation avec la commande suivante.
```bash
sudo su -
/home/user/startTraefik.sh
```
L'installation met à disposition le dashboard qui devient alors accessible sur via `http://dashboard.localhost/dashboard/`.

N'hésitez-pas à regarder ce que fait la commande.

:pushpin: Si vous souhaitez connaitre ce que contient un fichier sans l'ouvrir / le type de fichier vous pouvez utiliser la commande `file <fichier>`.

# Partie 1 - Helm : Un gestionnaire de paquet comme les autres ?

Lorsque l'on souhaite installer des applications et leur dépendances de manière automatique sur nos machines personnelles, on se repose souvent sur des gestionnaires de paquets comme APT (debian) ou PIP (python). 

Dans l'écosystème *Kubernetes*, l'outil de référence pour packager et partager des configurations se nomme *Helm*. Par exemple, une seule commande `helm install` permet d'installer sur un cluster des utilitaires comme Traefik (cf TD5), ou des applications comme nextcloud (clone ouvert de google docs).

Nous allons l'utiliser pour packager notre site, et le partager.

## Helm - Concepts importants

Dans le langage Helm, un paquet est appelé un *Chart*. Un *Chart* est un ensemble de fichiers qui décrivent des ressources Kubernetes.

Cependant, par rapport aux gestionnaires de paquet classiques, Helm permet :
- de paramétrer l'installation d'un paquet (Chart), en modifiant sa *configuration*
- d'installer plusieurs instance d'un même paquet (Chart), avec des configurations différentes. Chaque installation d'un Chart donne lieue à la création d'une *Release*

---

Exemple de Release 
- Version de développement : `helm install dev ./my-chart`
- Version de production : `helm install prod ./my-chart --set debug=false`

Deux *Releases*, `dev` et `prod`,  même chart `my-chart`, configuration différente 

![Concepts Helm](/figures/helm-concepts.png)

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


Déployons les ressources déclarées dans le dossier `templates`, en installant le Chart.

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

Lorsque l'on installe un Chart, la configuration par défaut (définie dans `values.yaml`) est utilisée. Il est courant de vouloir personaliser la configuration d'une Release.  

Pour ça, il existe deux options :

- Passer les paramètres en ligne de commande : `helm install <name> <chart> --set key1=val1,key2=val2`
- Fournir un fichier de valeur, qui fusionnera avec le fichier `values.yaml` : `helm install <name> <chart> --values config.yaml`

Installez une seconde release de notre application, appelée `toto2`, qui possèdera deux réplicas de notre pod, via la ligne de commande.
Via un fichier de valeurs, installer une troisième release appelée `toto3`, avec trois réplicas.

## Mise à jour d'un Chart

Il est courant d'avoir à mettre à jour une Release, pour changer la configuration des ressources Kubernetes (image d'un pod, nombre de réplicas).

Une solution naïve consiste à réinstaller la Release :
- Désinstallez la release `toto` : `helm uninstall toto`
- Installation à nouveau la release, avec 4 réplicas: `helm install toto --set replicaCount=4`

Cette méthode est assez brutale : on supprime toutes les ressources Kubernetes (pods, services, ...), et notre site devient indisponible, jusqu'à ce que la nouvelle release soit créée. De plus, en cas d'erreur, le retour en arrière peut être complexe.

*Helm* fournit aussi la commande `upgrade`, qui permet de mettre à jour les ressources Kubernetes. En passant de 1 à 4 réplicats, Kube créera seulement 3 pods.

`helm upgrade <release> <chart>` 

Mettre à jour le nombre de réplicas de la release `toto` à 2 en utilisant la commande `helm upgrade`. 
Vous observerez que la REVISION de la release est passée de 1 à 2. 
Mettre à jour le tag de l'image nginx pour un tag invalide, comme `fauxlabel` (image.tag dans `values.yaml`)
La REVISION de la release passe de 2 à 3. :question:  À l'aide de `kubectl/k9s`, comment pouvez-vous diagnostiquer que l'image est invalide ?

D'autres commandes/outils permettent de diagnostiquer l'état d'une release. Nous ne les verrons pas dans ce cours,  mais ils sont présentés en [annexe](#outils-de-diagnostic-helm). 

Pour revenir à un état précédent de notre release, il existe commande `helm rollback <RELEASE> [REVISION]`.

Remettez la release `toto` dans son état stable (avant l'ajout du faux label) à l'aide de l'outil `rollback`.

## Templating

Maintenant que vous maitrisez les commandes de base *Helm*, c'est à vous d'ajouter vos propres templates. Nous allons ajouter un template pour l'httpRoute du TD 4. 

Rappel, il faut avant installer traefik (en superutilisateur). Si vous ne l'avez pas fait au début de séance, il est encore temps de le faire. 


```yaml
# httproute.yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: helmroute
spec:
  parentRefs:
    - name: traefik-gateway
  hostnames:
    - "helm.localhost"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: {{ include "helm-app.fullname" . }}-service
          port: 80
```

- Rajouter cette route HTTP aux templates du Chart helm-app.
- Mettre à jour la release `toto` avec le Chart mis à jour. 
- Verifier que la route nommée `helmroute` est bien créée.

- Mettre à jour la release `toto2` avec le Chart mis à jour. 

:question: La mise à jour ne fonctionne pas, vous obtenez un message d'erreur. Que dit ce dernier ? Comment résoudre le problème ?

### Macros : générer des noms/labels adaptés pour chaque release

Pour permettre à deux Releases d'un même Chart de coexister sur un même cluster, il est nécessaire que les noms, ainsi que les labels des ressources Kubernetes soit différent d'une release à une autre.

Pour cela, on pourrait utiliser dans notre template la variable `.Release.name`, mais on passe généralement par des macros, définies dans le fichier `helpers.tpl`.

Pour utiliser une macro Helm, on utilise `{{ include "<nom macro>" . }}`. Un exemple d'utilisation est celui là :  

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "helm-app.fullname" . }}-service
```

:question: `helm-app.fullname` est une macro définie dans `_helpers.tpl`. Retrouvez la. De quoi est composé ce fullname ? Quel sera le nom de notre service ? Verifier-le via `kubectl`. 

- Modifier le nom de votre Route pour qu'elle dépende du nom de la release.
- Installer ou mettre à jour deux release `toto` et `toto2`. Vérifier que le conflit lié au nom de la route a disparu.

### Paramétrer un template

Maintenant que l'on est capable de générer des HTTPRoute propres à chaque release, paramétrons-les. 

La configuration dans `values.yaml` devra être la suivante :

```yaml
# Dans values.yaml
route:
  hostname: "monsupersite.localhost"
```

Modifiez le template `httproute.yaml` du chart helm-app pour paramétrer le nom d'hôte de notre site.


Mettre à jour vos release de `helm-app` pour utiliser des noms d'hôtes différents : `toto.localhost` et `totov2.localhost`.

# Partie 2 - Packager notre application

Dans le dossier `minecraft-app`, nous avons fourni la structure d'un chart Helm pour le site minecraft présenté dans les TDs précédents.

Ce chart est incomplet. Nous avons simplement fait en sorte de générer des labels/sélecteurs propre à chaque release. C'est à vous de: 
- Modifier les noms des déploiements, des services, de la httpRoute pour qu'il soient unique pour chaque release. Attention, il faudra modifier les références à ses noms, s'il en existe. En particulier, le site utilisait le nom de domaine "postgres" pour ce connecter à la base de donnée. Désormais, une variable d'environnement "DB_HOSTNAME" est définie dans le déploiement. Cette variable devra correspondre au nom d'hôte du service lié à la BDD.
- Ajouter les paramètres définis dans `values.yaml` aux templates Kubernetes.

Pour tester vos configurations, il existe la commande `helm template <release> <chart>`, qui permet de visualiser les descripteurs Yaml une fois les balises remplacées.

Pour éviter d'avoir à relancer une registry locale, vous pouvez utiliser une image publique du site : [https://hub.docker.com/r/hreymond/virwebsite](https://hub.docker.com/r/hreymond/virwebsite)

:question: Dans le cas de cette image, sauriez vous identifier son *registry*, son *namespace*, son nom et son tag ?

Comme d'habitude, n'hésitez pas à appeler votre chargé de TD si vous avez des questions.

# Liens

- [Documentation du templating Helm](https://helm.sh/docs/chart_template_guide/)

# Outils de diagnostic Helm

- `helm history <release>` permet de voir l'historique des révisions déployées
- `helm get values <release>` permet de voir les paramètres de la release fournis par l'utilisateur
- `helm get values <release> --all` permet de voir les paramètres de la release calculés (valeurs par défaut + valeurs données par l'utilisateur)
- `helm template 
- Le plugin `helm diff` permet de voir les différences de configuration entre deux releases
  - Installation : `helm plugin install https://github.com/databus23/helm-diff`
  - Documentation : [https://github.com/databus23/helm-diff](https://github.com/databus23/helm-diff)
- `helm status <release>` permet de retrouver le résumé de déploiement affiché après un `helm install` ou `helm upgrade`

# Commandes utiles

```bash
file <fichier>
helm repo add <nom> <url>
helm repo update

helm install <releaseName> ./<localfolder>
helm install <releasename> <repoName>/<chartName>
helm list

helm template --debug <releaseName> <chartRef>

kubectl get deployment
kubectl delete deployment <deploymentname>

kubectl apply -f <descripteur.yaml>
kubectl describe pod <podId>
kubectl get pods

kubectl get endpoints
kubectl get endpointslices

kubectl scale deployment <deploymentId> --replicas=<#>`
```
