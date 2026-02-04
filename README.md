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

### Script de Seed

- Pour un import standard (si la base est vide).
`docker-compose exec backend python -m app.seed`

- Pour écraser et tout remettre à propre (reset).
`docker-compose exec backend python -m app.seed --reset-db`

### Script Check Names

- Permet de vérifier la différence entre le nom de la dictée et le nom dans le CSV.
`docker-compose exec backend python -m app.check_names`

### Script Fix Files

- Si besoin de corréler les noms de fichiers similaires.
`docker-compose exec backend python -m app.fix_files`