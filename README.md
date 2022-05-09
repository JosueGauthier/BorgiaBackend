# BorgiaBackend : Installation prod avec NGINX et Gunicorn

# Documentation - Installation


# Introduction

Ce guide permet d'installer, configurer et faire fonctionner Borgia sur un serveur web en production.

L'ensemble de l'installation se fait sur un serveur sous Linux. La distribution n'est pas importante, mais le guide est écrit pour une distribution Debian, si tel n'est pas le cas certaines commandes (notamment les commandes d'installation de paquets) seront peut-être à adapter.

# Première configuration du serveur

-   L'ensemble des commandes suivantes sont à effectuer en `sudo`, sauf cas exceptionnels contraires et indiqués explicitement par la suite.

-   Il est préférable que l'ensemble du serveur soit configuré sur une machine virtuelle (VM) et non sur le serveur physique directement. Elle pourra ainsi facilement être copiée, sauvegardée ou réinitialisée.

-   Afin que le guide soit plus clair, il est décidé de travailler dans un dossier spécifique nommé `borgia-app` situé à la racine du serveur (`/borgia-app`). Il est bien évidemment possible de changer ce répertoire, les commandes devront donc être modifiées.

## Préliminaires

#### Mettre à jour le serveur :

-   `apt-get update`
-   `apt-get upgrade`

#### Supprimer Apache s'il est installé :

`apt-get purge apache2`

#### Installer des paquets nécessaires pour la suite de l'installation :

`apt-get install curl apt-transport-https`

#### Installer les packages python de base :

`apt-get install build-essential libpq-dev python-dev libjpeg-dev libssl-dev libffi-dev`

#### Installation de nginx, postgres & git :

-   `apt-get install postgresql postgresql-contrib nginx git`

#### Installation de pip pour python3 :

-   S'assurer que la commande `python3 --version` retourne une version supérieure ou égale à `3.5` (Version par défaut sur Debian 9). Si ce n'est pas le cas, réinstaller `python3`.
-   `apt-get install python3-pip`

#### Installation de Yarn (cas explicite de Debian, sinon voir [ici](https://yarnpkg.com/lang/en/docs/install/)):

-   `curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -`
-   `echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list`
-   `apt-get update && sudo apt-get install yarn`

#### Création du dossier racine de Borgia :

`mkdir /borgia-app`

## Mise en place de l'environnement virtuel Python


/!\ installation possible de venv l'utiliser dans ce cas la 

#### Installation de `virtualenv`

-   `pip3 install virtualenv virtualenvwrapper`
-   Dans `/borgia-app`, créer un environnement virtuel : `virtualenv borgiaenv`.
-   Si la commande virtualenv n'existe pas, faire: `ln -s /usr/local/bin/virtualenv* /usr/bin/`

#### Fonctionnement de l'environnement virtuel

-   Dans la suite du tutoriel, lorsque des commandes sont effectuées dans l'environnement virtuel il faut s'assurer d'y être. Afin d'être sûr, l'invite de commande indique le nom de l'environnement en parenthèses (ici `(borgiaenv)` par exemple).
-   Lorsque c'est demandé, la commande `source /borgia-app/borgiaenv/bin/activate` permet d'entrer dans l'environnement. Et `deactivate` pour en sortir.

## Installation et configuration de la base de données

Cette partie ne doit pas être effectuée dans l'environnement virtuel.



#### Sélectionner l'utilisateur postgres

`su - postgres`


https://phoenixnap.com/kb/how-to-install-postgresql-on-ubuntu

La suite des commandes est a effectuer dans l'invite de commande postgres. `psql` permet d'activer l'invite et `\q` permet d'en sortir. Attention, toutes les commandes se terminent par un `;`.

#### Création de la base de données

**MOT_DE_PASSE_DB** est le mot de passe choisi pour se connecter à la base de données. Faites attention à le modifier dans toutes les commandes.

Dans l'invite postgres :

-   `CREATE DATABASE borgia;`
-   `CREATE USER borgiauser WITH PASSWORD 'MOT_DE_PASSE_DB';`
-   `GRANT ALL PRIVILEGES ON DATABASE borgia TO borgiauser;`

## Copie de Borgia

Dans `/borgia-app` :

-   `git clone https://github.com/borgia-app/Borgia.git`

Ensuite dans `/borgia-app/Borgia` :

-   `git checkout tags/RELEASE_A_UTILISER`
-   `git checkout -b production_RELEASE_A_UTILISER`

## Installation des paquets nécessaires à l'application

Dans `/borgia-app/Borgia` et dans l'environnement virtuel :

-   `pip3 install -r requirements/prod.txt`

Et finalement, hors de l'environnement virtuel :

-   `yarn global add less`

# Configuration du logiciel

#### Paramètres vitaux

Copier le fichier `/borgia-app/Borgia/contrib/production/settings.py` dans `/borgia-app/Borgia/borgia/borgia/settings.py` et :

-   Modifier la ligne `SECRET_KEY =` en indiquant une clé privée aléatoire. Par exemple, [ce site](https://randomkeygen.com/) permet de générer des clés, choisissez au minimum "CodeIgniter Encryption Keys", par exemple : `SECRET_KEY = 'AAHHBxi0qHiVWWk6J1bVWCMdF45p6X9t'`.

-   S'assurer que `DEBUG = False`.

-   Modifier la ligne `ALLOWED_HOSTS =` en indiquant les domaines ou sous domaines acceptés par l'application. Par exemple : `ALLOWED_HOSTS = ['sibers.borgia-app.com', 'borgia-me.ueam.net']`.

#### Base de données

Dans le fichier `/borgia-app/Borgia/borgia/borgia/settings.py`, modifier la partie :

```python
DATABASES = {
...
}
```

en indiquant le nom de la base de données, le nom de l'utilisateur et le mot de passe définis lors de la configuration de cette dernière. Par exemple :

```python
DATABASES = {
   'default': {
       'ENGINE': 'django.db.backends.postgresql_psycopg2',
       'NAME': 'borgia',
       'USER': 'borgiauser',
       'PASSWORD': 'mot_de_passe',
       'HOST': 'localhost',
       'PORT': '5432',
   }
}
```

#### Serveur mail

-   Créer un compte mail Google via le site [Gmail](https://www.google.com/gmail/) et noter le nom d'utilisateur **NOM_UTILISATEUR_MAIL** et le mot de passe **MOT_DE_PASSE_MAIL**.

Dans le fichier `/borgia-app/Borgia/borgia/borgia/settings.py` :

-   Modifier les lignes `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL` et `EMAIL_HOST_USER` en indiquant l'email **NOM_UTILISATEUR_MAIL**.

-   Modifier la ligne `EMAIL_HOST_PASSWORD` en indiquant le bon mot de passe **MOT_DE_PASSE_MAIL**.

#### Administrateurs

Les administrateur reçoivent des emails en cas de problèmes lors de l'utilisation de Borgia. Par exemple, si la base de données est inacessible, Borgia enverra automatiquement un mail aux administrateurs. Ces mails sont précieux et permettent de corriger des erreurs. En effet, l'interface de debug utilisée en développement n'est pas accessible ici et les mails la remplacent. Il convient d'ajouter au moins un administrateur qui va stocker les éventuels mails d'erreurs pour débuguer ensuite ou transférer à l'équipe de mainteneurs de Borgia.

Pour ajouter des administrateurs, indiquer les adresses mails dans la ligne `ADMINS =` dans le fichier `/borgia-app/Borgia/borgia/borgia/settings.py`.

# Migration de la base de données

Dans `/borgia-app/Borgia/borgia` et dans l'environnement virtuel :

-   `python3 manage.py makemigrations configurations users shops finances events modules sales stocks`
-   `python3 manage.py migrate`
-   `python3 manage.py loaddata initial`
-   `python3 manage.py collectstatic --clear` en acceptant l'alerte

Ensuite, indiquer le mot de passe du compte administrateur (qui sera désactivé par la suite) :

-   `python3 manage.py shell`,
-   `from users.models import User`,
-   `u = User.objects.get(pk=2)`,  mettre pk=1 AE_ENSAM
-   `u.set_password(NEW_PASSWORD)`.
-   `u.save()`
-   `exit()`

#### Test intermédiaire

La commande dans l'environnement virtuel `python3 manage.py runserver 0.0.0.0:8000` doit lancer le serveur et ne doit pas indiquer d'erreur. Si tel est le cas, continuer vers la suite et fin du guide d'installation.

# Fin de la configuration du serveur

- suivre tutoriel : https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-20-04-fr



ressources a utiliser si pblm 

- https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-20-04-fr
- https://stackoverflow.com/questions/11426087/nginx-error-conflicting-server-name-ignored

- sudo tail -f /var/log/nginx/error.log

- https://www.digitalocean.com/community/tutorials/how-to-set-up-nginx-server-blocks-virtual-hosts-on-ubuntu-16-04
- https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-20-04-fr

- https://stackoverflow.com/questions/53223914/issue-using-certbot-with-nginx


#### Sauvegarde dans git

Enfin, il convient de sauvegarder l'ensemble de cette configuration sur une branche de production (sudo non nécessaire ici) :

-   `git add .`
-   `git commit -m "production"`

Il n'est pas recommandé de push cette branche car elle pourrait contenir des informations sensibles comme des clés et des mots de passe.


### Lydia

Les deux clés publique et privée `LYDIA_API_TOKEN` & `LYDIA_VENDOR_TOKEN` permettent d'identifier le compte auprès de Lydia. Ces informations sont obtenues en contactant le support de Lydia directement après avoir ouvert un compte professionnel chez eux.

De même, il faut changer les deux urls `LYDIA_CALLBACK_URL` et `LYDIA_CONFIRM_URL` en modifiant la première partie qui concerne uniquement le domaine (`borgia.iresam.org` par exemple). Attention, `LYDIA_CONFIRM_URL` doit être en `http` et Borgia fera automatiquement la redirection si SSL est activé, mais `LYDIA_CALLBACK_URL` **DOIT** être en `https` si SSL est activé !
