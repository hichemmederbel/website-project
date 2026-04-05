from flask import Flask, render_template, request, redirect, url_for, session, flash
import database as db

app = Flask(__name__)
app.secret_key = "chess_volunteers_secret_key_2024"

# Initialiser la base de données au démarrage
db.init_db()


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def get_current_user():
    """Retourne le dict de l'utilisateur connecté ou None."""
    user_id = session.get("user_id")
    if user_id:
        return db.get_user_by_id(user_id)
    return None


def require_login():
    """Redirige vers /login si l'utilisateur n'est pas connecté."""
    if "user_id" not in session:
        flash("Vous devez être connecté pour accéder à cette page.", "warning")
        return redirect(url_for("login"))
    return None


def require_admin():
    """Redirige vers / si l'utilisateur n'est pas admin."""
    user = get_current_user()
    if not user or user["role"] != "admin":
        flash("Accès réservé à l'administrateur.", "danger")
        return redirect(url_for("index"))
    return None


# ──────────────────────────────────────────────
# Routes générales
# ──────────────────────────────────────────────

@app.route("/")
def index():
    tasks = db.get_all_tasks()
    user = get_current_user()
    user_task_ids = set()
    if user:
        user_task_ids = {t['id'] for t in db.get_user_tasks(user['id'])}
    return render_template("index.html", tasks=tasks, user=user, user_task_ids=user_task_ids)


# ──────────────────────────────────────────────
# Routes d'authentification
# ──────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")

        if not name or not password:
            flash("Veuillez remplir tous les champs.", "danger")
            return render_template("login.html", user=None)

        user_id = db.login(name, password)
        if user_id == -1:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
            return render_template("login.html", user=None)

        session["user_id"] = user_id
        flash(f"Bienvenue, {name} !", "success")
        return redirect(url_for("index"))

    return render_template("login.html", user=None)


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not name or not password or not confirm:
            flash("Veuillez remplir tous les champs.", "danger")
            return render_template("register.html", user=None)

        if password != confirm:
            flash("Les mots de passe ne correspondent pas.", "danger")
            return render_template("register.html", user=None)

        user_id = db.new_user(name, password)
        if user_id == -1:
            flash("Ce nom d'utilisateur est déjà pris.", "danger")
            return render_template("register.html", user=None)

        session["user_id"] = user_id
        flash("Compte créé avec succès ! Bienvenue !", "success")
        return redirect(url_for("index"))

    return render_template("register.html", user=None)


@app.route("/logout")
def logout():
    session.clear()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("index"))


# ──────────────────────────────────────────────
# Routes bénévoles
# ──────────────────────────────────────────────

@app.route("/profile")
def profile():
    redir = require_login()
    if redir:
        return redir

    user = get_current_user()
    tasks = db.get_user_tasks(session["user_id"])
    return render_template("profile.html", tasks=tasks, user=user)


@app.route("/assign", methods=["POST"])
def assign():
    redir = require_login()
    if redir:
        return redir

    task_id = request.form.get("task_id")
    if task_id:
        result = db.assign_task(int(task_id), session["user_id"])
        if result == 'ok':
            flash("Vous êtes inscrit à cette tâche.", "success")
        elif result == 'already':
            flash("Vous êtes déjà inscrit à cette tâche.", "warning")
        elif result == 'full':
            flash("Cette tâche est complète, plus de places disponibles.", "danger")
    return redirect(url_for("index"))


@app.route("/unassign", methods=["POST"])
def unassign():
    redir = require_login()
    if redir:
        return redir

    task_id = request.form.get("task_id")
    if task_id:
        db.remove_assignment(int(task_id), session["user_id"])
        flash("Vous vous êtes désinscrit de cette tâche.", "info")
    return redirect(url_for("profile"))


# Routes administrateur

@app.route("/admin")
def admin():
    redir = require_admin()
    if redir:
        return redir

    tasks = db.get_all_tasks()
    user = get_current_user()
    stats = {
        "total":     len(tasks),
        "full":      sum(1 for t in tasks if t["is_full"]),
        "available": sum(1 for t in tasks if not t["is_full"]),
    }
    return render_template("admin.html", tasks=tasks, user=user, stats=stats)


@app.route("/add_task", methods=["POST"])
def add_task():
    redir = require_admin()
    if redir:
        return redir

    title      = request.form.get("title", "").strip()
    date       = request.form.get("date", "").strip()
    start_time = request.form.get("start_time", "").strip()
    end_time   = request.form.get("end_time", "").strip()
    try:
        max_volunteers = max(1, int(request.form.get("max_volunteers", 1)))
    except (ValueError, TypeError):
        max_volunteers = 1

    if not title or not date or not start_time or not end_time:
        flash("Veuillez remplir tous les champs de la tâche.", "danger")
        return redirect(url_for("admin"))

    db.add_task(title, date, start_time, end_time, max_volunteers)
    flash(f"Tâche « {title} » ajoutée avec succès.", "success")
    return redirect(url_for("admin"))


@app.route("/delete_task", methods=["POST"])
def delete_task():
    redir = require_admin()
    if redir:
        return redir

    task_id = request.form.get("task_id")
    if task_id:
        db.delete_task(int(task_id))
        flash("Tâche supprimée.", "info")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
