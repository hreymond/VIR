# TD9 - Intégration continue, livraison continue et déploiement continu

Objectif du TD :
- :dart: Avoir une vision de processus de déploiement : comment passe-t-on du code source à une application déployée ?
- :dart: Savoir mettre en place un pipeline gitlab pour automatiser ce processus

Ce TD assume que vous savez déjà créer et interagir avec un dépôt git

Dans les TDs précédents, nous avons vu comment passer du code source d'une application au déploiement de cette application : 

| Étape     | TD        | Application en TD                                                              |
| --------- | --------- | ------------------------------------------------------------------------------ |
| Build     | TD2       | Concevoir une image docker pour exécuter notre application                     |
| Test      | TD3       | Tester le fonctionnement de notre image en local avec docker et docker-compose |
| Livraison | TD6       | Rendre disponible notre application dans une registry locale                   |
| Deploy    | TD4 à TD6 | Déployer notre application sur un cluster Kubernetes avec Helm                 |

Dans ce TD, nous allons voir comment automatiser ces étapes.

Bien qu'il soit possible d'automatiser ces tâches en local, il est commun d'effectuer ses opérations dans un gestionnaire de version distant comme Github ou Gitlab.

Dans notre cas, nous utiliserons Gitlab pour mettre en place cette automatisation. L'objectif est le suivant: chaque nouveau commit poussé vers le dépôt gitlab entraine l'exécution d'une *pipeline*. Une pipeline est une ensemble de tâches - *jobs* en anglais - qui vont entrainer la compilation, le test, voir le déploiement du code modifié. 

Ces tâches sont regroupées en étapes - *stages* en anglais -. Les étapes par défaut dans Gitlab sont `build`, `test` et `deploy`, mais il est possible de définir des étapes personnalisées. Les tâches au sein d'une même étape s'exécutent en parallèle. Les étapes s'exécutent les unes après les autres : les tâches de `test` ne s'exécuteront qu'une fois les tâches de `build` terminées. Si notre programme C ne compile pas (étape `build`),  alors on ne va pas le tester (étape `test`).

La figure suivante présente la visualisation d'une *pipeline* gitlab avec deux *stages* : `build` et `test`. Le stage `build` contient une seule tâche - *job* en anglais-, tandis que le stage `test` en contient deux. 

![Pipeline Menu](/figures/ci-status.png)

Dans notre cas, les tâches sont dans trois status différents :
- JobA a été complété (status `success`)
- JobB est en cours d'exécution (status `running`)
- JobC est en attente d'exécution (status `pending`)

Dans la suite du TD, nous détaillons comment mettre en place un pipeline avec Gitlab CI/CD. Les concepts évoqués seront transposables à d'autres outils de CI/CD (Github Actions, Jenkins, CircleCI), même si leur implémentation varie.

# Partie 1 : Bases de la CI/CD

## Pipelines Gitlab

Dans la suite de cette partie, nous allons prendre l'exemple de ce dépôt : 
- https://gitlab.insa-lyon.fr/hreymond/cicd_example

La mise en place d'un pipeline Gitlab ce fait via un fichier déposé à la racine du dépôt : `.gitlab-ci.yml`. Ce fichier décrit les étapes et les tâches à exécuter au format `yaml`. Le `.gitlab-ci.yml` correspondant à la pipeline visible au dessus est le suivant :

```yaml
# Fichier .gitlab-ci.yml
jobA:
  stage: build
  image: python:3.14
  script:
    - echo "Hi $GITLAB_USER_LOGIN!, running JobA"
  
jobB:
  stage: test
  script:
    - echo "Testing something..."
    - ping -c 2 8.8.8.8

jobC:
  stage: test
  script:
    - echo "Testing nothing"
    - cat README.md
```

Chaque job exécute une suite de commandes (paramètre `script`), dans un conteneur docker. Ce conteneur, doit l'image peut être spécifiée par le paramètre `image`, s'exécute sur un serveur distant, qu'on appelle *runner*. 

## Exécution d'un pipeline

Sur la page gitlab du dépôt, vous devriez observer un commit, avec un petit badge vert :

![Commit avec badge CI/CD](/figures/ci-cd_badge.png)

Ce badge indique la réussite de la pipeline associée au commit. 
En cliquant sur ce badge, vous retrouvez le détail du pipeline et l'état des tâches.

Cliquer sur le JobA pour voir ces logs. Chaque tâche exécutée suit le même processus :
- Tout d'abord, Gitlab cherche un serveur disponible pour exécuter la tâche. Ce serveur est appelé un `runner`.
- Un conteneur docker est créé à partir d'une image par défaut ou spécifiée avec le paramètre `image:`
- Le contenu du dépôt gitlab correspondant au commit qui a déclenché la pipeline est copié dans le conteneur.
- L'ensemble des commandes spécifiées dans le Job sont exécutées.

:question: Saurez-vous retrouver dans les logs :
- Le nom du runner utilisé pour exécuter la tâche ?
- Le nom de l'image docker utilisée pour exécuter la tâche ?
- Le hash du commit qui est utilisé par la tâche ?
- La commande exécutée ?


Nous allons modifier ce dépôt pour mettre en place une pipeline d'intégration continue (CI) et de livraison continue (CD) pour un logiciel simple : l'outil superDB vu au TD2.

Pour cela, effectuez un fork du dépôt original, à l'aide du bouton *Fork* : 

![Le bouton Fork](/figures/button-fork.png)

Suivez les étapes jusqu'à obtenir votre propre fork du dépôt `minimal-ci`.

Cloner le dépôt nouvellement créé :

- De préférence en SHH : `git clone git@gitlab.insa-lyon.fr:<USERNAME INSA>/minimal-ci.git`
- Si vous n'avez pas configuré votre clé SSH, vous pouvez aussi le cloner en http : `git clone https://gitlab.insa-lyon.fr/<USERNAME INSA>/minimal-ci.git`

## Intégration continue (CI)

Pour cette première partie, nous allons mettre en place une pipeline d'intégration continue (CI) pour le logiciel SuperDB.

L'objectif est que les modification du code source de SuperDB soient vérifiées à chaque commit.

Pour commencer, nous allons vérifier que SuperDB compile bien : l'étape de `build`.

### Build 

Supprimer les Jobs existants dans `.gitlab-ci.yml`, et créez un nouveau job nommé `build`. Ce job doit compiler `superDB.c` pour créer `superDBExe` à l'aide de la commande suivante : `gcc -o superDBExe superDB.c`

Attention, pour compiler superDB, il est nécessaire d'avoir les dépendances suivantes `gcc`, `libc6-dev`.

Pour cela, deux méthodes sont possibles :
- Prendre une image générique : `debian`, `alpine` et installer les dépendances `gcc libc6-dev`
- Prendre une image spécialisée : `gcc`

Une fois votre job créé, mettez à jour le dépôt gitlab :
- git add .
- git commit
- git push

:question: Est-ce que la compilation de SuperDB fonctionne ? (Normalement oui)

### Test

Maintenant que superDB compile, nous allons tester l'outil.

Copiez votre Job `build` pour créer le job `test`.
Étendez ce job pour appeler le script `testSuperDB.sh`. Ce script permet de tester le fonctionnement de la base de donnée SuperDB.

Mettre à jour le dépôt gitlab avec votre fichier `.gitlab-ci.yml`

:question: Est-ce que le test de SuperDB fonctionne ? (Normalement oui)

:question: Est-il nécessaire de recompiler superDB dans `test` ? Pourquoi ?

### Artefacts

Dans l'état actuel, on compile deux fois l'outil superDB. Comment fait-on pour que la tâche `test` utilise le binaire superDBExe compilé par la tâche `build` ? À l'aide des artefacts !

Les outils de CI/CD proposent des mécanismes pour partager des fichiers entre deux tâches d'une même pipeline.

Dans Gitlab, ce mécanismes est appelé artefact - *artifact* en anglais-, et sa syntaxe est la suivante :

```yaml
job:
  artifacts:
    paths:
      - <Chemin à partager entre les tâches>
```

Définir `superDBExe` comme artefact du job `build` rendra le binaire accessible aux jobs suivants, comme `test`. 

Ajoutez un artefact aux job `build` pour sauvegarder l'exécutable `superDBExe`. Mettez à jour le dépôt gitlab avec votre fichier `.gitlab-ci.yml`

Ces artefacts sont ensuite disponibles au téléchargement, lorsque vous ouvrez le job concerné :

![Menu des artefacts](/figures/artifacts.png)

## Livraison continue (CD)

Maintenant que notre outil compile et a été testé, il est temps de le mettre à disposition dans une registry.

Gitlab met à disposition des registry de différents types :

- Générique (fichiers en tout genre)
- apt
- Docker 
- Helm

Il est possible d'interagir avec ces registry via une API, en utilisant un token auto-généré pour chaque job pour l'authentification. 

La syntaxe de l'API est documentée par Gitlab. Par exemple, la documentation pour publier un ficher dans le registre générique est disponible [ici](https://docs.gitlab.com/user/packages/generic_packages/?tab=With+a+Bash+script#publish-a-single-file). Un extrait de cette page est visible ici : 

> To publish a single file, use the following API endpoint:
>
> `PUT /projects/<id>/packages/generic/<package_name>/<package_version>/<file_name>`
>
> Replace the placeholders in the URL with your specific values:
>
> - id: Your project ID or URL-encoded path
> - package_name: Name of your package
> - package_version: Version of your package
> - file_name: Name of the file you’re uploading. See valid package filename format below.

Créer un job "publish", stage "deploy", qui exécute la commande suivante à partir d'une image `debian`:

```bash
curl -v -X PUT --header "JOB-TOKEN: ${CI_JOB_TOKEN}" --upload-file superDBExe https://gitlab.insa-lyon.fr/api/v4/projects/${CI_PROJECT_ID}/packages/generic/superDB/latest/superDBExe
```

:question: Quelle valeurs ont été choisies pour les paramètres *id*, *package_name*, *package_version* et *file_name* ?

:question: À quoi correspondent chacune des options de cette commande curl ?

Mettez à jour le dépôt gitlab avec votre fichier `.gitlab-ci.yml`

:question: Est-ce que la pipeline fonctionne ? Est-ce que le binaire est disponible dans la registry ? Pour vérifier : ouvrir le menu via le bouton en haut à gauche sur la page gitlab de votre dépôt, menu *Deploy* -> *Package registry*.

Dans cet exemple, la version du package est codée en dur (`latest`), ce qui n'est pas idéal. 

Pour éviter cela, plusieurs possibilités :
- Utiliser l'ID du commit comme version du package : `${CI_COMMIT_ID}`. Dans ce cas, on aura un package différent pour chaque nouveau commit
- Si un tag est associé au commit, l'utiliser comme version du package : `${CI_COMMIT_TAG}`. Dans ce cas, il faut déclencher le job `publish` uniquement si un tag est associé au commit.
- Déclencher la livraison manuellement, et entrez la version à la main

Nous allons voir ensemble comment mettre en place la dernière solution.

### Tâche à déclenchement manuel

Il est possible d'ajouter `when: manual` à un job pour qu'il faille le démarrer manuellement.

Modifiez le job `publish` pour qu'il devienne manuel. Poussez les modifications sur le dépôt.

Via l'interface Gitlab, il est désormais possible de lancer le job `publish` à l'aide du bouton suivant :

![Tâche à déclenchement manuel](/figures/manual-trigger.png)

Cliquez sur l'engrenage. Ce menu permet de lancer la tâche en indiquant des variables d'environnement supplémentaires au job. On utilisera ce menu pour indiquer la version du package.

Lancez le job manuellement sans indiquer de variable pour le moment.

Modifiez la tâche `publish` pour que la variable d'environnement `VERSION` soit utilisée comme version du package 

Poussez les modifications sur le dépôt, et lancer manuellement le job `publish` en précisant la variable d'environnement VERSION=1.0.0.
Vérifiez que votre registry gitlab contient bien un package avec la version 1.0.0.

# Partie 2 - CI/CD avec docker

Dans cette partie, nous allons mettre en place une pipeline pour construire et tester une image docker. Le cas de docker est un peu particulier, car pour construire une image docker, il nous faut un démon docker, capable de traiter les commandes `docker build`.
Touts les runners disposent d'un démon docker pour lancer les conteneurs nécessaires à l'exécution des jobs gitlab. Cependant, dans le cas du Gitlab Insa, les jobs ne peuvent pas communiquer directement avec ce démon docker pour des raison de sécurité. On devra donc utiliser un conteneur docker qui contient lui même un démon docker : ce qu'on appelle du docker in docker, ou dind. 

Pour cela, on utilise un *service*. Dans le jargon Gitlab, un service est une image docker additionnelle qui est lancée, à côté de l'image dans laquelle la tâche s'exécutera.
Un exemple de service est la base de donnée `postgres` [Service Postgresql](https://docs.gitlab.com/ci/services/postgres/).

On partira du dépôt suivant : [https://gitlab.insa-lyon.fr/vir/docker-ci](https://gitlab.insa-lyon.fr/vir/docker-ci)

Comme précédemment, faites un fork du dépôt, et clonez le fork en local

## Build docker 

Compléter le Job `build` dont le template est fourni ci-dessous. Ce Job doit concevoir l'image docker à partir du `Dockerfile` présent dans le dossier `website`. Tagger cette image `website:v3` (cf [TD2](/TD2-docker/)). 

```yaml
build:
  # L'image choisie pour exécuter les commandes de notre Job
  image: docker:24.0.5-cli 
  # Cette ligne permet d'avoir accès au moteur de conteneur docker
  services:
  - docker:24.0.5-dind
  # Les commandes à éxécuter pour concevoir notre image
  script:
  - echo "Building website image !"
  - ...
```

Cette étape nous permet de vérifier que notre image docker se construit bien.

git add, commit, push : verifiez que votre Job est bien exécuté, et que l'image se construit sans problème.

## Registry docker

Pour partager l'image docker construite dans le job `build` avec le job `test`, on stockera l'image dans la registry du gitlab insa lyon.

Pour cela, il faudra tout d'abord s'authentifier auprès de la registry à l'aide de la commande `docker login`, puis tagger et pousser l'image comme dans le TD6.
Le format attendu pour l'image est `gitlab.insa-lyon.fr:5050/<USERNAME>/<REPOSITORY_NAME>/<IMAGE_NAME>:<IMAGE_TAG>`

Copiez et compléter les commandes suivantes dans votre job `build` :
```yaml
  - echo "$CI_REGISTRY_PASSWORD" | docker login gitlab.insa-lyon.fr:5050 -u $CI_REGISTRY_USER --password-stdin
  - docker tag ...
  - docker push gitlab.insa-lyon.fr:5050/...
```
[Documentation Gitlab CI/CD](https://docs.gitlab.com/user/packages/container_registry/build_and_push_images/#container-registry-examples-with-gitlab-cicd)

## Test

Maintenant que notre image est bien construite, on veut tester les fonctionnalités de notre site. Pour des raisons de simplicité, on teste pour le moment uniquement la page d'acceuil, qui n'a pas besoin de la base de donnée Postgres.

Créez un job `test` qui : 
- Se connecte à la registry gitlab.insa-lyon.fr:5050 
- Pull l'image website:v3 correspondant à votre projet
- lance un conteneur à partir de l'image `website:v3`, en mode démon (`-d`) que vous appelerez `website`
- attends 5 seconde que le serveur se lance (commande `sleep`)
- exécute la commande `python test_website.py` à l'intérieur du conteneur `website`, avec `docker exec`. Ce petit script python va vérifier que le serveur réponde au requêtes HTTP.

Poussez le `.gitlab-ci.yml` modifié. Vérifiez que votre Job est bien exécuté, et que l'image est testée sans problème.

Pour vérifier que l'on détecte bien lorsque une modification de code casse le fonctionnement du site,  changez le Dockerfile du site web pour que la commande lancée au démarrage ne soit plus `flask run --host=0.0.0.0` mais `echo coucou`. Poussez les modifications.

:question: Votre pipeline de test permet-elle de repérer la perte de fonctionnement de votre conteneur ?

# Partie 3 - Déploiement continu

## Faire en sorte que la registry gitlab soit accessible depuis votre PC

La registry gitlab est configurée sur le port `5050`, qui est bloqué par défaut sur `eduroam`

Dans un nouveau terminal, activez le vpn de l'insa :

`sudo openconnect sslvpn.cisr.fr -u <USERNAME>@insa-lyon.fr --authgroup=INSA`

Vérifiez qu'il est possible de récupérer une image docker à partir de la registry

`podman login gitlab.insa-lyon.fr:5050`

`podman pull gitlab.insa-lyon.fr:5050/<USERNAME>/docker-ci/website:v3`

## Déploiement continu avec Kubernetes

Nous allons maintenant automatiser le déploiement de notre image docker sur un cluster Kubernetes. Si ce n'est pas fait, relancez votre cluster k3s.

Maintenant, nous allons créer un pod qui utilise une image issue de la registry gitlab :

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: website
spec:
  replica: 1
  selector:
    matchLabels:
      app: website
  template:
    metadata:
      labels:
        app: website
    spec:
      containers:
      - name: website
        image: gitlab.insa-lyon.fr:5050/<USERNAME>/docker-ci/website:v3
        ports:
        - containerPort: 5000
        imagePullPolicy: Always # Force Kubernetes à récupérer l'image la plus à jour
```

Remplacez votre nom d"utilisateur et appliquez ce manifest avec `kubectl apply`.

:question: Est-ce que le pod réussit à ce lancer ? (La réponse est non) Inspectez le pod pour comprendre d'où vient le problème. Une fois que vous avez une idée, continuez le TD

## Gestion des secrets dans Kubernetes

Vous l'aurez deviné, pour accéder à la registry gitlab, il est d'abord nécessaire de s'authentifier. Nous l'avons fait avec `podman` avant le `podman pull`, mais `containerd`, le moteur de conteneurisation de K3S, ne permet pas de s'authentifier globalement. 

De plus, on ne veut surtout pas que nos identifiants soit stockés en clair sur le cluster pour être utilisés à chaque `pull`

## Génération de Token 

Create a personal access token

To authenticate with the Flux CLI, create a personal access token with
the read_registry scope:

In the upper-right corner, select your avatar.
Select Edit profile.
Select Personal access tokens.
Enter a name and optional expiry date for the token.
Select the read_registry scope.
Select Create personal access token.

Vérifiez que votre token est valide en l'utilisant pour récupérer une image dans le dépôt :

`podman pull --creds "<USERNAME>:<TOKEN>" gitlab.insa-lyon.fr:5050/<USERNAME>/docker-ci/website:v3`

## Authentification et gestion des mots de passe dans Kubernetes

Il faut que kubernetes s'authentifie à chaque fois qu'il essaie de récupérer une image dans la registry. Pour cela, on va stocker le nom d'utilisateur et le token gitlab dans un *secret* Kubernetes ([Documentation des secrets](https://kubernetes.io/fr/docs/concepts/configuration/secret/)). 

Parmi les différents types de secrets disponibles, il existe le type `docker-registry`, qui permettent de s'authentifier auprès d'une registry

Créez le secret `gitlab-registry` à partir de cette ligne de commande (attention à bien remplacer <USERNAME> et <TOKEN> !) :

```bash
kubectl create secret docker-registry gitlab-registry \
--docker-server="gitlab.insa-lyon.fr:5050" \
--docker-password="<TOKEN>" \
--docker-username="<USERNAME>"
```

Vérifiez que votre secret est bien créé.

Maintenant, il faut indiquer au pod `website` qu'il peut utiliser le secret `gitlab-registry` nouvellement créé pour chercher l'image de son conteneur.

Ajoutez à la spécification du pod (paramètre `spec.template.spec`):

```yaml
imagePullSecrets: # Définit les identifiants à utiliser pour récupérer l'image
- name: gitlab-registry
```

Puis, créez à nouveau le pod `website`, à partir du manifest mis à jour.

:question: Est-ce que le pod réussit à ce lancer ? (Normalement, la réponse est oui) 

Récupérez l'IP du pod, et vérifiez que le site est accessible (rappel, le site tourne sur le port 5000).

Dans votre fork du dépôt `docker-ci`, modifiez la page d'acceuil du site minecraft pour afficher "Bonjour TC !" (fichier `flask_minimal.py`, ligne 45).

Poussez les modifications et vérifiez : 
- Une nouvelle version de l'image `website:v3` est construite et poussée dans la registry gitlab
- En faisant `docker pull` en local, est-ce que l'image est bien mise à jour ?
- Redémarrez votre déploiement avec `kubectl rollout restart deployment website` : Est-ce que Kubernetes va chercher la nouvelle version de l'image ? (cette information est visible avec `kubectl describe pod`) 
- Vérifiez avec `curl` que la page d'acceuil du site est bien modifiée

Maintenant que notre image est disponible pour Kubernetes, la dernière étape consiste à déclencher le `kubectl rollout` dans la pipeline gitlab.

## Interagir avec le cluster Kubernetes depuis la pipeline gitlab

Cette partie du TD est en chantier. Si vous êtes arrivé jusqu'ici, c'est surement que vous êtes débrouillard·e. 

Vous retrouverez les informations pour interagir ci dessous, et dans la [documentation officielle](https://gitlab.insa-lyon.fr/help/user/clusters/agent/getting_started.md)


1. Installer glab (utilitaire gitlab) et [flux](https://fluxcd.io/) (utilitaire pour le déploiement continu) :

```bash
sudo apt update && sudo apt install -y glab
curl -s https://fluxcd.io/install.sh | sudo bash
```

2. Créez un token d'accès personnel avec le scope `api` et `write_repository`

Create a personal access token

To authenticate with the Flux CLI, create a personal access token with
the api and write_repository scope:

In the upper-right corner, select your avatar.
Select Edit profile.
Select Personal access tokens.
Enter a name and optional expiry date for the token.
Select the api and write_repository scope.
Select Create personal access token.

3. Sur votre cluster, déployez `flux` et `glab`

```bash
# Bootstrap flux 
flux bootstrap gitlab \
--hostname=gitlab.insa-lyon.fr \
--owner=<USERNAME> \
--repository=docker-ci \
--branch=main \
--path=clusters/testing \
--deploy-token-auth


# Bootstrap Glab
glab version
glab auth login -h gitlab.insa-lyon.fr

glab cluster agent bootstrap --manifest-path clusters/toto toto
```

4. Créez un job `deploy`, qui met à jour le déploiement website (référence : [documentation Gitlab](https://gitlab.insa-lyon.fr/help/user/clusters/agent/getting_started_deployments.md)) :

```yaml
deploy:
  stage: deploy
  image: "portainer/kubectl-shell:latest"
  variables:
    AGENT_KUBECONTEXT: <USERNAME>/docker-ci:toto
  script:
    - kubectl config use-context $AGENT_KUBECONTEXT
    - kubectl get nodes
    - kubectl rollout restart deployment website
```

5. Modifiez le site pour qu'il affiche "Vive la KFET !"
6. Poussez les modifications : votre cluster est-il mis à jour automatiquement ?

Pour continuer plus loin, vous pouvez mettre en place la livraison automatique et le déploiement automatique du Chart Helm du TD7 ! 

# Liens utiles

- [Formation CI/CD](https://blog.stephane-robert.info/docs/pipeline-cicd/gitlab/)

Pour référence, une liste de tout les états possibles est disponible [ici](https://docs.gitlab.com/ci/jobs/#available-job-statuses)

## Extensions

## Règles

Restreindre la CI CD à la branche main, ou au commits qui commencent par COUCOU

### Code coverage

Code coverage c'est quoi ? 

Test, et on vérifie que l'on a testé toutes les branches possibles de notre programme.

Créez un copie de votre job `build`, appelé `coverage`. 

On re-compilera l'appli dans la tâche `coverage` car il faut compiler l'appli avec des arguments particuliers.
Modifier la compilation de super db et ajouter les arguments suivants `--coverage -g -O0`

De cette manière, la compilation de SuperDB va génerer un fichier `.gcno`. Quand on va exécuter nos tests de SuperDB, ça va générer un fichier `.gcda`

On va utiliser `covr`, un outil pour analyser ces traces pour langage C.
Modifier le job pour installer le paquet apt `covr` (attention à bien faire un `apt update` avant d'installer `covr`)

covr -> Normalement on a le pourcentage

Ga; Gc; Gp

vérifier qu'il est bien visible dans les logs
-> Cool, mais personne ne va aller le voir
->Fail si pas assez de coverage

Ajouter l'option `--fail-under-line=90` à la commande `gcovr`

Maintenant, chaque ajout de fonctionnalité devra venir avec un test pour que la couverture de code soit au dessus de 90%. 

Ga; Gc; Gp

On observe que le test fail car pas assez de coverage. Cependant, on ne peut pas voir quelles sont les lignes qui ne sont pas empruntées. Ajouter l'option `--html-details coverage.html` permet de générer un rapport au format html indiquant les lignes de code non couvertes par les tests.

Problème : comment récupérer ce rapport ? 

On voudrait un moyen d'accéder aux fichiers HTML et CSS générés.
