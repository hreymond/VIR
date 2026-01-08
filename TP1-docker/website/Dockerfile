# Récupèrer une image de base
FROM python:3.14-slim

# Définir le repertoire /app comme repertoire courant
WORKDIR /app

# Copier le contenu du dossier courant (.) de l'hôte vers le dossier courant de l'image (ici /app)
COPY . .

# Installer les dépendances python
RUN pip install -r requirements.txt

# Définir la variable d'environnement FLASK_APP, nécessaire pour flask
ENV FLASK_APP=flask_minimal.py

# Définit la commande à lancer au lancement du conteneur
CMD ["flask", "run", "--host=0.0.0.0"]
