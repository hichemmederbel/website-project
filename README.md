# ChessVolunteer

Application web de gestion des bénévoles pour tournois d'échecs.  
Permet à un administrateur de créer des créneaux avec une capacité définie, et aux bénévoles de s'y inscrire librement.

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3 · Flask |
| Base de données | SQLite |
| Frontend | HTML · CSS · JavaScript (vanilla) |

---

## Lancer le projet

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Démarrer le serveur
python3 app.py
```

L'application est accessible sur **http://127.0.0.1:5000**

> La base de données `chess_volunteers.db` est créée automatiquement au premier démarrage avec des données de démonstration.

---

## Compte administrateur

### Compte par défaut

Un compte admin est créé automatiquement au premier démarrage :

| Champ | Valeur |
|-------|--------|
| Nom d'utilisateur | `admin` |
| Mot de passe | `admin123` |

> ⚠️ **Changez ce mot de passe** avant tout déploiement en production.

### Créer un nouveau compte admin

Il n'existe pas de formulaire d'inscription admin dans l'interface — le rôle doit être défini directement en base de données.

**Méthode 1 — SQLite en ligne de commande**

```bash
sqlite3 chess_volunteers.db
```

Puis dans le shell SQLite :

```sql
INSERT INTO user (name, password, role) VALUES ('votre_nom', 'votre_mot_de_passe', 'admin');
.quit
```

**Méthode 2 — Script Python one-liner**

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('chess_volunteers.db')
conn.execute(\"INSERT INTO user (name, password, role) VALUES ('votre_nom', 'votre_mot_de_passe', 'admin')\")
conn.commit()
conn.close()
print('Compte admin créé.')
"
```

**Vérifier les comptes existants**

```bash
sqlite3 chess_volunteers.db "SELECT id, name, role FROM user;"
```

**Promouvoir un compte bénévole existant en admin**

```bash
sqlite3 chess_volunteers.db "UPDATE user SET role = 'admin' WHERE name = 'nom_du_compte';"
```

---

## Structure du projet

```
website-project/
├── app.py               # Routes Flask (auth, bénévoles, admin)
├── database.py          # Couche DAO + initialisation SQLite
├── requirements.txt     # Dépendances Python
├── chess_volunteers.db  # Base SQLite (générée automatiquement)
├── templates/
│   ├── layout.html      # Template de base (navbar + footer)
│   ├── index.html       # Liste des tâches avec capacité
│   ├── login.html       # Connexion
│   ├── register.html    # Création de compte
│   ├── profile.html     # Mes inscriptions
│   └── admin.html       # Tableau de bord administrateur
└── static/
    ├── css/style.css    # Design sobre (thème universitaire)
    └── js/main.js       # Validation formulaires + filtres
```

---

## Modèle de données

### Table `user`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER PK | Identifiant |
| name | TEXT UNIQUE | Nom d'utilisateur |
| password | TEXT | Mot de passe |
| role | TEXT | `admin` ou `benevole` |

### Table `task`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER PK | Identifiant |
| title | TEXT | Intitulé de la tâche |
| date | TEXT | Date de l'événement |
| start_time | TEXT | Heure de début |
| end_time | TEXT | Heure de fin |
| max_volunteers | INTEGER | Nombre de places max |

### Table `task_assignment`
| Colonne | Type | Description |
|---------|------|-------------|
| task_id | INTEGER FK | Référence tâche |
| user_id | INTEGER FK | Référence bénévole |

> La combinaison `(task_id, user_id)` est la clé primaire — un bénévole ne peut s'inscrire qu'une seule fois à une tâche.

---

## Fonctionnalités

### Bénévoles
- Créer un compte et se connecter
- Voir toutes les tâches du tournoi avec leur date, horaire et capacité restante
- S'inscrire à une tâche (si des places sont disponibles)
- Se désinscrire depuis la page profil
- Filtrer les tâches par disponibilité

### Administrateur
- Créer des tâches avec date, horaires et nombre de places
- Voir en temps réel les inscrits et le taux de remplissage
- Supprimer une tâche
- Tableau de bord avec statistiques (total, complètes, disponibles)

---

## Routes Flask

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/` | Liste des tâches |
| GET/POST | `/login` | Connexion |
| GET/POST | `/register` | Création de compte |
| GET | `/logout` | Déconnexion |
| GET | `/profile` | Mes inscriptions |
| POST | `/assign` | S'inscrire à une tâche |
| POST | `/unassign` | Se désinscrire |
| GET | `/admin` | Tableau de bord admin |
| POST | `/add_task` | Créer une tâche |
| POST | `/delete_task` | Supprimer une tâche |

---

## Auteur

Mederbel Hichem
