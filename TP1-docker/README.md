
# TP1 - Docker

Objectif du TP :
- :dart: Prendre en main les commandes usuelles de Docker
- :dart: Être capable de concevoir une image Docker

## Partie I : Conteneurs

Vous êtes en charge du déploiement d'un site web.
Ce site assez simple demande à l'utilisateur d'entrer le pseudonyme d'un joueur Minecraft. 

![Main page](figures/index.png)

Le site affiche ensuite la tête du joueur en question, et enregistre la requête dans un fichier json : `queried_names.json`. Par défaut, le site écoute sur le port 5000.

![Display skin page](figures/display_skin.png)

Le dossier `website` contient le code du site web (`flask_minimal.py`), la liste des dépendances du site (`requirements.txt`), ainsi qu'un Dockerfile.

Ce fichier `Dockerfile` permet la construction de l'image Docker qui servira de modèle pour la création de conteneurs. Nous reviendrons plus tard sur le contenu de ce fichier.

> [!NOTE] 
>
> **Docker, images et conteneurs**
>
>  Docker permet l'exécution de processus de manière isolée dans des **conteneurs**. Ces conteneurs sont dits _self-contained_, c'est à dire qu'ils contiennent toutes les dépendances nécessaire à l'exécution du processus.
>
> Une **image** Docker est un ensemble de fichiers, bibliothèques, binaires et de configurations qui sert de modèle pour la création d'un conteneur.
>
> Dans le cas de notre application web, notre image contiendra toutes les dépendances (python, paquets pythons, code de l'application). Notre conteneur utilisera cette image pour exécuter un processus : notre serveur web.

### Construire une image et lancer un conteneur

Dans le répertoire `website`

- Lancer `docker build . -t website` pour construire une image nommée `website` à partir du `Dockerfile`.
- Avec `docker image list`, vérifier que l'image existe bien.
- Lancer `docker run website`, pour créer un conteneur à partir de l'image `website`. Le serveur devrait se lancer et écouter sur le port 5000 (`running on http://<ip>:5000`).

> [!NOTE] 
>
>  **Redirection de ports**
>
> Si vous essayez d'accéder au site web depuis votre ordinateur, cela ne fonctionnera pas. Le serveur web écoute bien sur le port 5000, mais il est uniquement accessible au sein du réseau docker, et pas depuis votre machine hôte (pour vous en convaincre, vous pouvez regarder les ports actifs sur votre machine avec `netstat -tln`).
>
> Pour rendre le serveur accessible depuis l'extérieur du conteneur, il est nécessaire faire une redirection de port (_port-forwarding_ en anglais). L'objectif est que le réseau trafic entrant sur le port 5000 de notre machine soit redirigé vers le port 5000 du conteneur. Pour cela, on doit relancer notre conteneur.

- Arrêter le conteneur Ctrl-c
- Relancer le conteneur en arrière plan (option `-d`), en ajoutant la redirection de port :  `docker run -d -p 5000:5000 website`.

### Inspecter les conteneurs

- Dans un autre terminal, lancer `docker container list -a`, vérifier
  que votre conteneur est présent, et à l'état "UP". Noter le nom de votre conteneur.
  Vous remarquerez que votre précédent conteneur n'a pas été supprimé (status Exited).

- Vérifiez que le serveur s'est bien lancé : `docker logs <nom du conteneur>`
- Vérifiez que le port 5000 est bien ouvert sur votre machine : `netstat -tln`

Vous pouvez alors accéder à votre site depuis un navigateur (adresse `http://localhost:5000`).
- Tester le site avec plusieurs pseudos (le votre si vous en avez, sinon `Aypierre` par exemple).

Le site enregistre les statistiques des requêtes effectués dans un fichier nommé `queried_names.json`. Nous allons vérifier que le fichier est bien créé à l'aide de la commande `docker exec`, qui permet d'exécuter une commande au sein d'un conteneur.

- Executer `docker exec -it <nom du conteneur> bash`, pour obtenir un terminal bash au sein de votre conteneur. Verifiez que le fichier `queried_names.json` existe, ainsi que son contenu.
- Arrêter et supprimer le conteneur (`docker stop`, `docker rm`)

### Persistance des données

- Démarrer un nouveau conteneur : `docker run -d -p 5000:5000 website`. Est-ce que le fichier `queried_names.json` est toujours présent dans le conteneur ?

> [!NOTE]
>
> **Stockage persistent : les volumes**
>
> Par défaut, chaque conteneur docker a son propre système de fichier, qui est supprimé en même temps que le conteneur. C'est une limitation dans plusieurs cas :
> - Lorsque l'on souhaite sauvegarder des données entre deux exécutions d'un conteneur, comme dans notre cas avec le fichier `queried_names.json`
> - Lorsque l'on souhaite partager des données entre plusieurs conteneurs.
>
> Pour résoudre ces problèmes, on utilise des _volumes_.
  Les volumes sont des stockages persistants, gérés par docker. Par défaut, le contenu d'un volume est stocké sous la forme dans un dossier sur votre machine (usuellement `~/.local/share/containers/storage/volumes`), mais il peut aussi être hebergé ailleurs (NFS, Amazon S3,...).
>
> Pour monter un volume avec docker, on utilise le paramètre `--volume <v-name>:<mount-path>` avec `v-name` le nom souhaité pour le volume, et `mount-path` le chemin auquel le volume sera rattaché à l'intérieur du conteneur.
>
> Plus d'informations sur les #link("https://docs.docker.com/engine/storage/volumes/", "volumes ici"). Il est aussi possible de partager un dossier avec un conteneur via des #link("https://docs.docker.com/engine/storage/bind-mounts/")[_bind mounts_]

- Lancer un conteneur avec un volume nommé `app_data` qui stockera le
  contenu du dossier `/app` (qui contient le fichier
  `queried_names.json`)
- Rechercher quelques nom d'utilisateurs, pour ajouter des statistiques à
  `queried_names.json`
- Supprimer le conteneur `docker rm -f <nom conteneur>` (`-f` permet de forcer
  l'arrêt du conteneur)
- Lancer un nouveau conteneur, toujours avec le même volume. Est-ce que le fichier `queried_names.json` est toujours présent dans le conteneur ?

:white_check_mark: Le site web est déployé, et ses données persistées !

## Partie II : Création d'images

L'équipe de développement s'est rendu compte des limitations d'utiliser un fichier json comme base de donnée. 
Il ont donc sorti une nouvelle version du site web, qui utilise une base de donnée maison :"SuperDB".
Cette fois ci, c'est à vous de créer l'image Docker.

Let's decypher the current Dockerfile step by step, understanding each component:

```dockerfile
# Start with a base image
FROM python:3.14-slim
```

This line selects our foundation. Think of it as choosing the operating system and core tools. We use python:3.14-slim because it:
- Includes Python 3.14 pre-installed
- Contains essential Linux tools
- Maintains a relatively small size

```dockerfile
# Set up our working directory
WORKDIR /app

# Copy the application content COPY <src> <dst>
COPY . .

# Install the Python packages we need
RUN pip install -r requirements.txt
```

We first copy the content of the current folder (Readme.md, flask_minimal.py, ...) into the app/ folder in the image. 

Then, we install the dependancies for our python app, listed in the `requirements.txt` file.

```dockerfile
# Tell Flask which application to run
ENV FLASK_APP=flask_minimal.py

# Specify the command to start our application
CMD ["flask", "run", "--host=0.0.0.0"]
```

This sets up:
- Environment variables Flask needs
- The command to start our application
- Network access from outside the container

# À vous de jouer !

La nouvelle version du site web est dans le répertoire `website-v2`.

Les source du logiciel "SuperDB" sont dans le répertoire CustomDB.
En vous aidant du Readme.md de CustomDB modifier le Dockerfile pour :
- Installer les dépendances pour compiler CustomDB
- Compiler le CustomDB.c pour produire l'exécutable CustomDB
- Tagger avec la version : `docker build . -t website:v2`