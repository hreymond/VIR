# TD8 - Supervision

Nous allons installer une infrastructure de supervision minimale. Elle surveille l'application Web minecraft que vous avez précédemment développé.
Dans votre souvenir, elle passe par traefik pour l'accès externe et nous avons mis à disposition sur la clé le chart elm permettant de l'installer directement.

L'application Web s'accède selon deux routes : 
````
 / --> Demande la saisie d'un nom d'avatar   
 /display_skin?username=toto --> Requête une API externe, récupère l'avatar et met à jour un compteur dans un microservice de base de données.    
````

Nous testerons principalement la seconde route d'accès.   

L'infrastructure minimale standard de supervision repose sur les composants et l'architecture suivante.  

- **Traefik** est le gestionnaire d'accès de type API Gateway. C'est le composant que nous voulons surveiller. 
  - Il expose des métriques via la route `localhost:9100/metrics`
- Cette route est régulièrement interrogée par le gestionnaire de sonde **Prometheus**.
  - Il peut être accédé via une route `localhost:9090`
- Les valeur collectées et aggrégées par prometheus peuvent être visualisées graphiquement par **graphana** 
  - La visualisation peut être accédée par la route `localhost:3000`

![Pipeline de supervision](/figures/metrics_pipeline.png)

metrics --> prometheus --> graphana, sont les éléments les plus traditionnels des infrastructures de supervision de système. Le nom des composants peuvent changer, mais les trois rôles clés : data -> aggregation -> visualisation existent toujours. 
Nous vous proposons la mise en place de cette infrastructure, puis la vérification via l'usage de l'application web minecraft.

**Prometheus** n'est pas lié à Kubernetes, c'est un outil de collecte et de stockage de métriques dans des bases de données temporelles. Sont rôle est d'absorber des grandes charges de données, les indexer, les normaliser et permettre leur interrogations selon n'importe quel critère souhaité. Les outils comme `elasticsearch / ELK`, `opentelemetry` ou `prometheus` servent le même but : collecter et mettre à disposition des centre d'administration des sondes et des alarmes de surveillance d'infrastructures cloud.

Il existe un chart elm prometheus chargé de la supervision d'infrastructure kube. Ce chart `prometheus-community/kube-prometheus` est installé via le script `startPrometheus.sh`. La version que nous avons configuré n'installe pas, volontairement, les sous-charts `kubeStateMetrics` et `nodeExporter` qui permettent de remonter toutes les metriques d'état du cluster et d'état des noeuds. Nous réduisons ces données afin que vous vous focalisiez sur les métriques de `traefik`. 

Pour l'installation, nous vous suggérons de lancer une console `k9s` dans une fenêtre afin d'observer la progression de l'installation. 

`./startPrometheus.sh`

Vous pouvez vérifier que le service fonctionne en demandant les métriques actuellement scrappées. Récupérez l'IP du service `prometheus-kube-prometheus-prometheus`, et ouvrez dans firefox : `http://<IP>:9090/api/v1/label/__name__/values`. 
Normalement vous ne voyez pas de métrique liée à Traefik.

:question: Prometheus est-il disponible sur `localhost:9090` ? Testez.

Rendez Prometheus disponible sur `localhost:9090` à l'aide de la commande `kubectl port-forward`. Testez que vous pouvez accéder à : `http://localhost:9090/api/v1/label/__name__/values`

:question: Pouvez-vous accéder à ce port-forward d'une autre machine de la salle ? Tester avec le navigateur de votre voisin. (ps : la réponse est oui)

Prometheus est bien installé. Il vient accompagné de `graphana` que nous lançons plus tard, et des `servicesmonitor` pour découvrir les sondes et métriques accessibles.

# Installation de Traefik

Les métriques sont accessible sur les noeuds par la route `<ip:9100>/metrics` Traefik n'échappe pas à la règle. Il peut participer à l'émission de métriques pour prometheus. Nous avons modifiée le lancement de traefik sur la clé `./startPrometheusTraefik.sh`. Cette nouvelle version se charge de valider 3 choses :   
```
  --set metrics.prometheus.enabled=true --> Autorise la récolte des metrics par prometheus  
  --set metrics.prometheus.service.enabled=true --> Crée un service http annoncant la route /metrics
  --set metrics.prometheus.serviceMonitor.enabled=true --> Permet à prometheus de découvrir le moniteur de traefik.
```

Toutefois le moniteur de traefik n'est pas découvert, il faut une positionner un label spécifique dans la description. (Il s'agit certainement d'un bug d'install).
La ligne du script `kubectl label servicemonitor traefik release=prometheus` se charge de cela.


Vous pouvez maintenant tester votre installation  : 
- Mise à disposition de la route par traefik : `kubectl get services`, puis `curl <xxx.yyy>:9100/metrics`
- Intégration du service monitor de traefik dans prometheus (en gros collecte de la route metrics) : `curl http://<www.zzz>:9090/api/v1/label/__name__/values |jq|grep traefik`
  
La commande `jq` formate le json de sortie. 

Si les métriques traefik sont exposées dans prometheus, vous pouvez maintenant les visualiser dans grafana.

# Visualisation

Pour accéder à grafana, vous devez auparavant ouvrir les accès :

-  Récupérer le mot de passe admin : `kubectl get secrets prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo`
-  Faire un port-forward sur le pod grafana. Attention, il faut corriger cet appel. `kubectl port-forward prometheus-grafana-<xxxx> 3000:3000`
-  Y accéder localement via firefox ou sur une autre machine avec un tunnel ssh : `ssh -L 3000:localhost:3000 <monPoteIP>`. Le nom d'utilisateur est `admin`, et vous avez récupéré le mot de passe précédemment.

Grafana, Kibana, sont les mêmes outils de visualisation de métriques et de surveillance d'alertes. Pour cette installation nous avons supprimé tous les `dashboards` de surveillance. Quand vous allez vous connecter dans Grafana vous ne verrez pas grand chose. 
- Vous pouvez `explorer` les métriques collectées : menu->explore, sélectionner une métrique et faites `run query`. Normalement la magie opère. Vous pouvez choisir des métriques de mesure de cpu par exemple.

Si vous commencez à voir quelque chose, vous pouvez installer un dashboard, ou en créer un, si vous êtes aventurier ou explorateur. 
Nous avons déposé dans le dossier TD8-Supervision un dashboard json `dashboard-grafana-17346_rev9.json` permettant de visualiser les  métriques traefik. N'hésitez pas à ouvrir le fichier pour voir le côté déclaratif de ces infrastructures...

Normalement vous pouvez consulter le dashboard traefik qui est... toujours vide, à part la zone indiquant les instances traefik qui devrait être à `1`.

# Et si on testait la charge ?

Après avoir installé le chart de l'application, 
```
cd /opt/minecraft-app-chart/
helm install minecraft .
```
vérifiez que l'application fonctionne. 

Sur votre machine ou sur une autre, vous pouvez tester : 
`curl -H "Host: minecraft.localhost" "http://<monPoteIp>/`

Puis générer de la charge : `ab -n 10000 -c 10 -s 50000 -H "Host: minecraft.localhost" "http://<monPoteIp>/display_skin?username=toto"`

Laissez tourner le site quelques temps. N'oubliez pas de recharger la page grafana, pour voir les métriques se mettre à jour plus rapidement. 

:question: Combien de requêtes notre site peut traiter par seconde ?  Note : le chart `minecraft` démarre avec deux pods `web` par défaut.

- Mettre à jour le nombre de pods de votre release helm : `helm upgrade minecraft . --set replicaCount=4`. Attendez quelques minutes que le nouveau déploiement soit effectif, et que les métriques Prometheus soit mises à jour.

:question: Quel est l'effet de l'augmentation du nombre de pod ?

:question: Quel est le nombre de pods adaptés à la charge générée par `ab` ? Testez plusieurs valeurs de `replicaCount` et concluez

La mise en place d'une infrastructure de supervision est terminée... Ou ce n'est que le début.

# Pour la suite
Comme nous vous l'avions indiqué la configuration d'un cluster de run 24/7 se fait par des l'intermédiaire de centaines de fichiers de configuration. C'est parfaitement similaire aux configuration d'infrastructure réseau. Il s'agit d'une convergence majeure des services de télécom et d'informatique. 
La maîtrise des configurations est un réel challenge pour l'avenir, il sera certainement simplifié via des IAg, des outils de check et des surlangages. En tant qu'experts vous pouvez maitriser les commandes de base nécessaires aux premiers débug. 

Ce TD est l'exemple typique de l'exercice qui prend 5 min à installer intégralement et aveuglément, mais peut prendre des semaines à installer selon une configuration précise. Dans le premier cas, vous allez aller très vite et prendre beaucoup de place, et beaucoup de charge, dans le second cas, vous risquer de ne pas atteindre vos objectifs de déployement. A vous de voir l'énergie à passer dans ce type de projet.

En résumé ce td se résumé à démarrer quatre commandes : 
```
 - k3s start server   
 - helm install prometheus kube-prometheus-stack   
 - helm install traefik traefik/traefik   
 - helm install minecraft .   
```

Ces quelques commandes déclenchent quelques des milliers de lignes de code et autant de lignes de paramètres de configuration. 

Si vous lancez uniquement ces lignes, vous verrez de nombreuses erreur de configuration. Pour vous entrainer, n'hésitez pas à essayer de les repérer et les corriger... La correction est donnée dans les fichiers <start..> que vos enseignants ont passé des nuits à valider pour vous. 

# Avant de commencer, nettoyer la configuration existante :

```bash
helm list -q | xargs helm uninstall # Désinstaller toutes les releases en cours
```

# Liste des commandes utilisées
Voici les quelques commandes bien utiles pour corriger les configurations. 

- La commande `kubectl get servicemonitors.monitoring.coreos.com`. Trouve bien un servicemonitor pour traefik.
      ```
      NAME      AGE
      traefik   48s
      ```
- La commande `kubectl describe servicemonitors.monitoring.coreos.com`. Affiche bien un label `release=prometheus`.
      ```
      Name:         traefik
      Namespace:    default
      Labels:       app.kubernetes.io/component=metrics
              app.kubernetes.io/instance=traefik-default
              app.kubernetes.io/managed-by=Helm
              app.kubernetes.io/name=traefik
              helm.sh/chart=traefik-39.0.5
              release=prometheus   <--- ICI
      Annotations:  meta.helm.sh/release-name: traefik
      ...
      ```

- La commande `helm show value <repository/chartname> > Value.yaml` est utile pour extraire les valeurs possibles du charts. Vous pouvez ne conserver que les valeurs qui vous intéressent, puis lancer l'installation de votre chart en passant ce fichier de valeurs avec la commande :  `helm install <tag> <repository/chartname> -f ./mesValeurs.yaml`. Cette technique est utilisée pour l'installation de prometheus dans le script startPrometheus. 

- La commande `helm search repo <repository>` affiche les charts d'un repository. Bien utile pour les repository communautaires comme prometheus-community.
  
- `ab` : apache benchmark permet de générer de la charge sur un serveur
- `jq` : parse une sortie json

# Références
https://github.com/prometheus-community/helm-chart -> Prometheus
https://oneuptime.com/blog/post/2026-02-02-k3s-monitoring/view -> Prometheus/k3s
https://oneuptime.com/blog/post/2026-02-06-opentelemetry-k3s-lightweight-kubernetes/view -> Opentelemetry
https://opentelemetry.io/docs/platforms/kubernetes/helm/demo/ -> Opentelemetry
https://locust.io/ -> Pour la montée en charge
https://gist.github.com/rxaviers/7360908

:ok: si vous voyez des bugs dans le sujet, n'hésitez-pas à nous prévenir !!!

