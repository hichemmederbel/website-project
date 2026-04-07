import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "chess_volunteers.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialise la base et applique les migrations nécessaires."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS user (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            role     TEXT    NOT NULL DEFAULT 'benevole'
        );

        CREATE TABLE IF NOT EXISTS task (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            title          TEXT    NOT NULL,
            date           TEXT    NOT NULL DEFAULT '',
            start_time     TEXT    NOT NULL,
            end_time       TEXT    NOT NULL,
            max_volunteers INTEGER NOT NULL DEFAULT 1,
            volunteer_id   INTEGER REFERENCES user(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS task_assignment (
            task_id INTEGER NOT NULL REFERENCES task(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
            PRIMARY KEY (task_id, user_id)
        );
    """)

    # Migrations colonnes
    existing_cols = [r[1] for r in cur.execute("PRAGMA table_info(task)").fetchall()]
    if 'date' not in existing_cols:
        cur.execute("ALTER TABLE task ADD COLUMN date TEXT NOT NULL DEFAULT ''")
    if 'max_volunteers' not in existing_cols:
        cur.execute("ALTER TABLE task ADD COLUMN max_volunteers INTEGER NOT NULL DEFAULT 1")

    # Migration volunteer_id → task_assignment
    if 'volunteer_id' in existing_cols:
        legacy = cur.execute(
            "SELECT id, volunteer_id FROM task WHERE volunteer_id IS NOT NULL"
        ).fetchall()
        for row in legacy:
            cur.execute(
                "INSERT OR IGNORE INTO task_assignment (task_id, user_id) VALUES (?, ?)",
                (row[0], row[1]),
            )
        cur.execute("UPDATE task SET volunteer_id = NULL")

    # Admin par défaut
    cur.execute("SELECT COUNT(*) FROM user WHERE role = 'admin'")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO user (name, password, role) VALUES (?, ?, 'admin')",
            ("admin", "admin123"),
        )

    #  Tâches de démonstration
    cur.execute("SELECT COUNT(*) FROM task")
    if cur.fetchone()[0] == 0:
        demo_tasks = [
            ("Installation des pendules – Salle A", "2026-05-10", "08:00", "09:00", 3),
            ("Installation des pendules – Salle B", "2026-05-10", "08:00", "09:00", 3),
            ("Arbitrage Secteur 1 (rondes 1-3)",    "2026-05-10", "09:00", "13:00", 2),
            ("Arbitrage Secteur 2 (rondes 1-3)",    "2026-05-10", "09:00", "13:00", 2),
            ("Arbitrage Secteur 1 (rondes 4-6)",    "2026-05-10", "14:00", "18:00", 2),
            ("Arbitrage Secteur 2 (rondes 4-6)",    "2026-05-10", "14:00", "18:00", 2),
            ("Gestion buvette – matin",             "2026-05-10", "08:30", "13:00", 2),
            ("Gestion buvette – après-midi",        "2026-05-10", "13:00", "18:30", 2),
            ("Saisie des résultats – ronde 1-3",    "2026-05-11", "09:00", "13:00", 1),
            ("Saisie des résultats – ronde 4-6",    "2026-05-11", "14:00", "18:00", 1),
            ("Accueil et remise des cartons de jeu","2026-05-11", "08:00", "09:30", 4),
            ("Rangement général en fin de tournoi", "2026-05-11", "18:00", "19:30", 6),
        ]
        cur.executemany(
            "INSERT INTO task (title, date, start_time, end_time, max_volunteers) VALUES (?,?,?,?,?)",
            demo_tasks,
        )

    conn.commit()
    conn.close()


# DAO

def login(name: str, password: str) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM user WHERE name = ? AND password = ?", (name, password)
    ).fetchone()
    conn.close()
    return row["id"] if row else -1


def new_user(name: str, password: str) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO user (name, password, role) VALUES (?, ?, 'benevole')",
            (name, password),
        )
        conn.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        user_id = -1
    finally:
        conn.close()
    return user_id


def get_all_tasks() -> list:
    """Retourne toutes les tâches avec le nombre et les noms des bénévoles inscrits."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT t.id, t.title, t.date, t.start_time, t.end_time, t.max_volunteers,
               COUNT(ta.user_id)          AS volunteer_count,
               GROUP_CONCAT(u.name, ', ') AS volunteer_names
        FROM task t
        LEFT JOIN task_assignment ta ON t.id = ta.task_id
        LEFT JOIN user u              ON ta.user_id = u.id
        GROUP BY t.id
        ORDER BY t.date, t.start_time, t.id
    """).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d['is_full'] = d['volunteer_count'] >= d['max_volunteers']
        result.append(d)
    return result


def get_user_tasks(user_id: int) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT t.id, t.title, t.date, t.start_time, t.end_time, t.max_volunteers
        FROM task t
        JOIN task_assignment ta ON t.id = ta.task_id
        WHERE ta.user_id = ?
        ORDER BY t.date, t.start_time
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_task(title: str, date: str, start_time: str, end_time: str,
             max_volunteers: int = 1) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO task (title, date, start_time, end_time, max_volunteers) VALUES (?,?,?,?,?)",
        (title, date, start_time, end_time, max_volunteers),
    )
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return task_id


def assign_task(task_id: int, user_id: int) -> str:
    """Inscrit l'utilisateur à la tâche.
    Retourne 'ok', 'already' (déjà inscrit) ou 'full' (complet).
    """
    conn = get_connection()
    already = conn.execute(
        "SELECT 1 FROM task_assignment WHERE task_id = ? AND user_id = ?",
        (task_id, user_id),
    ).fetchone()
    if already:
        conn.close()
        return 'already'

    count = conn.execute(
        "SELECT COUNT(*) FROM task_assignment WHERE task_id = ?", (task_id,)
    ).fetchone()[0]
    max_v = conn.execute(
        "SELECT max_volunteers FROM task WHERE id = ?", (task_id,)
    ).fetchone()
    if not max_v or count >= max_v[0]:
        conn.close()
        return 'full'

    conn.execute(
        "INSERT INTO task_assignment (task_id, user_id) VALUES (?, ?)", (task_id, user_id)
    )
    conn.commit()
    conn.close()
    return 'ok'


def remove_assignment(task_id: int, user_id: int) -> None:
    """Retire l'inscription d'un utilisateur à une tâche."""
    conn = get_connection()
    conn.execute(
        "DELETE FROM task_assignment WHERE task_id = ? AND user_id = ?",
        (task_id, user_id),
    )
    conn.commit()
    conn.close()


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT id, name, role FROM user WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_task(task_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM task WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
