# Projet Rousseau

## Contexte

## Développement

### Environnement Virtuel

1. Se placer dans le bon dossier
`cd backend`

2. Créer l'environnement virtuel
`python -m venv venv`

3. Activer l'environnement
- Sur Windows (PowerShell)
`.\venv\Scripts\Activate`
- Sur Mac / Linux
`source venv/bin/activate`

### Installer les dépendances

`pip install -r requirements.txt`

### Virtualisation

`docker-compose up -d --build`

#### Script de Seed

- Pour un import standard (si la base est vide).
`docker-compose exec backend python -m app.seed`

- Pour écraser et tout remettre à propre (reset).
`docker-compose exec backend python -m app.seed --reset-db`

- Pour tester (simulation).
`docker-compose exec backend python -m app.seed --dry-run`

#### Script Check Names

- Permet de vérifier la différence entre le nom de la dictée et le nom de l'étudiant.
`docker-compose exec backend python -m app.check_names`

#### Script Fix Files

- Permet de corréler les noms de fichiers similaires (dictée et étudiant).
`docker-compose exec backend python -m app.fix_files`

#### Script Check Mapping

- Permet de voir si les étudiants matchent entre les différents CSV.
`docker-compose exec backend python -m app.check_mapping`

#### Script Check Status

- Permet de voir l'avancée de chaque étudiant niveau des dictées et résultats outils.
`docker-compose exec backend python -m app.check_status`