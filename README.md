# Projet Rousseau

![Vue.js](https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

## Sommaire
- [Contexte](#contexte)
- [Prérequis](#prérequis)
- [Stack Technique](#stack-technique)
- [Développement](#développement)
  - [Configuration (.env)](#configuration-variables-denvironnement)
  - [Méthode 1 : Lancement Complet (Docker)](#méthode-1--lancement-complet-avec-docker)
  - [Méthode 2 : Développement Local (Hot-Reload)](#méthode-2--développement-local-hot-reload)
- [Accès aux services](#accès-aux-services-docker)
- [Scripts Utilitaires](#scripts-utilitaires-backend)
- [Structure du Projet](#structure-du-projet)
- [Tests](#tests)
- [Diagramme de classe](#diagramme-de-classe)

## Contexte

Le Projet ROUSSEAU, mené à l'IUT d'Annecy auprès des étudiants de première année de BUT, naît du constat que la maîtrise de l'orthographe est indispensable à la réussite académique et professionnelle, mais que les dispositifs de remédiation actuels montrent leurs limites. Dans une démarche critique vis-à-vis du dressage mécanique du Projet Voltaire utilisé précédemment, l'étude introduit pour l'année 2024-2025 la plateforme universitaire gratuite Ecri+, privilégiant une approche par compétences centrée sur l'apprenant. Ce pivot stratégique répond également à une contrainte budgétaire forte : il vise à déterminer si une solution ouverte et gratuite peut remplacer efficacement une solution privée représentant un coût annuel d'environ 10 000 € pour l'établissement.

Les enjeux de cette expérimentation dépassent la simple comparaison d'outils pour interroger profondément la stratégie pédagogique de l'établissement. Il s'agit d'abord de vérifier si les progrès constatés dans les exercices se transfèrent réellement à l'écrit spontané, un fossé souvent observé chez les étudiants. Sur le plan économique, l'étude doit déterminer si la solution gratuite offre une efficacité comparable à la licence payante, ce qui permettrait une rationalisation budgétaire. Enfin, en analysant le poids des déterminismes socioculturels (habitudes de lecture, milieu familial) face à la remédiation tardive, le projet pourrait conduire l'institution à repenser sa mission : si les inégalités structurelles s'avèrent trop lourdes, l'université pourrait devoir renoncer à « réparer » l'orthographe pour se tourner vers des outils palliatifs comme l'IA.

## Prérequis

Assurez-vous d'avoir installé les outils suivants sur votre machine :
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) pour la virtualisation.
- [Python 3.13+](https://www.python.org/downloads/) pour le développement backend.
- [Node.js 22+](https://nodejs.org/) & npm pour le développement frontend.
- [Git](https://git-scm.com/install/).

## Stack Technique

- **Backend :** Python, FastAPI, SQLModel (PostgreSQL).
- **Frontend :** Vue.js 3, TypeScript, Vite, Chart.js
- **Services tiers :** LanguageTool (Correction orthographique), pgAdmin (Gestion BDD).
- **Infrastructure :** Docker & Docker Compose.

## Développement

### Configuration (Variables d'environnement)

Avant de lancer le projet, vous devez créer un fichier `.env` à la racine du projet. 
Vous pouvez vous baser sur un hypothétique fichier `.env.example` :

```env
# Base de données PostgreSQL.
POSTGRES_USER=admin
POSTGRES_PASSWORD=secretpassword
POSTGRES_DB=rousseau_db

# pgAdmin.
PGADMIN_EMAIL=admin@rousseau.com
PGADMIN_PASSWORD=admin
DATABASE_URL=postgresql://admin:secretpassword@localhost:5434/rousseau_db

# Session.
SECRET_KEY=CodeSecret
ADMIN_PASSWORD=TaCleJWT

# Sécurité Backend (AES).
# Générer avec python : "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=VotreCleFernetIci
```

### Méthode 1 : Lancement Complet avec Docker

Idéal pour tester l'application ou la déployer rapidement.

Cette commande lance absolument tout (Base de données, pgAdmin, LanguageTool, Backend et Frontend) dans des conteneurs isolés :
- ```docker compose up -d --build```

### Méthode 2 : Développement Local (Hot-Reload)

Idéal pour travailler sur le code. Le backend et le frontend se rechargeront automatiquement à chaque modification de fichier.

1. Lancer l'infrastructure Docker
Nous n'avons besoin que de la base de données, de pgAdmin et de LanguageTool. Lancez uniquement ces services :
```docker compose up -d db pgadmin languagetool```

2. Démarrer le Backend FastAPI
    1. Se placer dans le bon dossier
    `cd backend`

    2. Créer l'environnement virtuel
    `python -m venv venv`

    3. Activer l'environnement
        - Sur Windows (PowerShell)
        `.\venv\Scripts\Activate`
        - Sur Mac / Linux
        `source venv/bin/activate`

    4. Installer les dépendances
    `pip install -r requirements.txt`

    5. Lancer le serveur avec rechargement automatique
    `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

3. Démarrer le Frontend Vue.js
    1. Se placer dans le dossier frontend :
    `cd frontend`

    2. Installer les dépendances Node :
    `npm install`

    3. Lancer le serveur de développement Vite :
    `npm run dev`

## Accès aux services (Docker)

Une fois les conteneurs lancés via `docker-compose up -d`, les services sont accessibles aux adresses suivantes :

| Service | URL | Description |
|---|---|---|
| **Frontend** | `http://localhost:8080` | L'interface web de l'application |
| **Backend API** | `http://localhost:8000` | L'API racine |
| **API Docs (Swagger)** | `http://localhost:8000/docs` | Documentation interactive de l'API (FastAPI) |
| **pgAdmin** | `http://localhost:5050` | Interface d'administration de la base de données |
| **LanguageTool** | `http://localhost:8010/v2/info` | API de correction orthographique |
| **Base de données** | `localhost:5434` | Port exposé pour connexion locale (DBeaver, DataGrip...) |

## Scripts Utilitaires (Backend)

#### Script de Seed

- Pour un import standard (si la base est vide).
`docker-compose exec backend python -m app.scripts.seed`

- Pour écraser et tout remettre à propre (reset).
`docker-compose exec backend python -m app.scripts.seed --reset-db`

- Pour tester (simulation).
`docker-compose exec backend python -m app.scripts.seed --dry-run`

#### Script Check Names

- Permet de vérifier la différence entre le nom de la dictée et le nom de l'étudiant.
`docker-compose exec backend python -m app.scripts.check_names`

#### Script Fix Files

- Permet de corréler les noms de fichiers similaires (dictée et étudiant).
`docker-compose exec backend python -m app.scripts.fix_files`

#### Script Check Mapping

- Permet de voir si les étudiants matchent entre les différents CSV.
`docker-compose exec backend python -m app.scripts.check_mapping`

#### Script Check Status

- Permet de voir l'avancée de chaque étudiant niveau des dictées et résultats outils.
`docker-compose exec backend python -m app.scripts.check_status`

#### Script Reset Database

- Permet de réinitialiser la base de données.
`docker-compose exec backend python -m app.scripts.reset_db`

#### Script Sync Enum

- Permet de générer un fichier `generated_enums.ts` dans `/frontend/src/types`, afin d'avoir des Enums synchronisés entre le Backend et le Frontend.
`docker-compose exec backend python -m app.scripts.sync_enum`

## Structure du Projet

```text
projet-rousseau/
├── backend/            # Code source de l'API (FastAPI).
│   ├── app/            # Logique métier, endpoints, modèles, services.
│   └── data/           # Fichiers bruts (CSV, copies) pour l'import.
├── frontend/           # Code source de l'interface (Vue 3 / TypeScript).
│   ├── src/views/      # Vues (Tableaux de bord, corrections, etc.).
│   └── src/components/ # Composants UI réutilisables.
├── docker-compose.yml  # Orchestration des services.
└── .env                # Fichier de configuration.
```

## Tests

### Backend

Le projet inclut des tests d'intégrations pour le backend.

1. Se placer dans le dossier backend : `cd backend`
2. Activer l'environnement virtuel : `.\venv\Scripts\Activate`
3. Lancer les tests d'intégrations (Pytest) : `pytest -vv -s`
4. Générer le rapport de code coverage (HTML) : `pytest --cov=app --cov-report=html`

### Frontend

Le projet inclut des tests unitaires et de bout en bout (E2E) pour le frontend.

1. Se placer dans le dossier frontend : `cd frontend`
2. Lancer les tests unitaires (Vitest) : `npm run test:unit`
3. Lancer les tests E2E (Playwright) : `npm run test:e2e`

## Diagramme de classe

Voici ton diagramme de classe complet.

Pour éviter les bugs d'affichage ("spaghetti" de flèches ou erreurs de syntaxe dans VS Code/GitHub), j'ai appliqué les règles suivantes :

Tous les champs sont explicitement listés dans les classes (y compris les dates du TimestampMixin et les clés étrangères comme group_id). Cela m'a permis de retirer les flèches d'héritage qui rendent le diagramme illisible.

J'ai converti les types complexes Python (Dict, uuid.UUID) en types standards lisibles (JSON, UUID).

Les liaisons sont simples (-->) et déclarées dans un ordre logique (de la configuration vers les résultats) pour aider le moteur de rendu à organiser les blocs proprement de gauche à droite (direction LR).

Copie-colle exactement le bloc ci-dessous dans ton README.md (sans espace avant les backticks) :

Markdown
## Diagramme de classe

```mermaid
classDiagram
    direction LR

    %% ==========================================
    %% BLOC 1 : STRUCTURE ET CONFIGURATION
    %% ==========================================
    class Promotion {
        +int id
        +string name
    }

    class Group {
        +int id
        +string name
        +string description
    }

    class Tool {
        +int id
        +string name
        +string full_name
    }

    class Dictation {
        +int id
        +string title
        +string content_reference
        +datetime created_at
        +datetime updated_at
    }

    class Category {
        +int id
        +string lt_category_id
        +string name
        +MistakeType type_rousseau
        +float penalty
        +datetime created_at
        +datetime updated_at
    }

    %% ==========================================
    %% BLOC 2 : NOYAU (ÉLÈVE)
    %% ==========================================
    class Student {
        +int id
        +UUID anonymous_id
        +string first_name_encrypted
        +string last_name_encrypted
        +int promotion_id
        +int group_id
        +int tool_id
        +string appetence_level
        +Library has_library
        +ReadingSupport reading_support
        +string reading_works
        +string motive
        +Degree parent_1_degree
        +CSP parent_1_csp
        +Degree parent_2_degree
        +CSP parent_2_csp
        +string declared_level
        +datetime created_at
        +datetime updated_at
    }

    %% ==========================================
    %% BLOC 3 : ÉVALUATIONS ET RÉSULTATS
    %% ==========================================
    class AssessmentResult {
        +int id
        +int student_id
        +int tool_id
        +AssessmentType assessment_type
        +float score
        +JSON details
        +datetime created_at
        +datetime updated_at
    }

    class Submission {
        +int id
        +int student_id
        +int dictation_id
        +AssessmentType assessment_type
        +string content_student
        +float final_score
        +JSON scores
        +datetime created_at
        +datetime updated_at
    }

    %% ==========================================
    %% BLOC 4 : CORRECTION ET LOGIQUE
    %% ==========================================
    class Rule {
        +int id
        +string lt_rule_id
        +string description
        +bool is_active
        +int category_id
        +datetime created_at
        +datetime updated_at
    }

    class Mistake {
        +int id
        +int submission_id
        +int category_id
        +string student_word
        +string correct_word
        +int position_index
        +int length
        +MistakeType type_rousseau
        +float malus_applied
        +string rule_id_lt
        +string message
        +string context
        +datetime created_at
        +datetime updated_at
    }

    %% ==========================================
    %% RELATIONS
    %% ==========================================
    
    %% Arrivées sur l'étudiant
    Promotion "1" --> "*" Student
    Group "1" --> "*" Student
    Tool "1" --> "*" Student

    %% Départs de l'étudiant (Résultats & Copies)
    Student "1" --> "*" AssessmentResult
    Tool "1" --> "*" AssessmentResult
    Student "1" --> "*" Submission
    Dictation "1" --> "*" Submission

    %% Logique de correction
    Category "1" --> "*" Rule
    Submission "1" --> "*" Mistake
    Category "1" --> "*" Mistake
```