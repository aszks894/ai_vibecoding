import os
import sqlite3
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "blog.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

app = Flask(__name__)
app.config["SECRET_KEY"] = "nostalgic-blog-secret"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

os.makedirs(os.path.join(UPLOAD_FOLDER, "profile_photos"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "posts"), exist_ok=True)


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            nickname TEXT NOT NULL,
            password TEXT NOT NULL,
            profile_photo TEXT DEFAULT 'default_avatar.svg',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    db.commit()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def save_upload(file, folder):
    if file is None or not file.filename:
        return None

    filename = secure_filename(file.filename)
    if not filename:
        return None

    unique_name = f"{os.urandom(8).hex()}_{filename}"
    target_dir = os.path.join(BASE_DIR, "static", "uploads", folder)
    os.makedirs(target_dir, exist_ok=True)
    file.save(os.path.join(target_dir, unique_name))
    return os.path.join("uploads", folder, unique_name).replace("\\", "/")


@app.route("/")
@login_required
def home():
    db = get_db()
    posts = db.execute(
        """
        SELECT posts.*, users.username, users.nickname, users.profile_photo
        FROM posts
        JOIN users ON users.id = posts.user_id
        ORDER BY posts.created_at DESC
        """
    ).fetchall()
    return render_template("home.html", posts=posts, current_user=get_current_user())


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        nickname = request.form.get("nickname", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not nickname or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        db = get_db()
        existing = db.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if existing:
            flash("That username is already taken.", "danger")
            return render_template("register.html")

        db.execute(
            "INSERT INTO users (username, nickname, password) VALUES (?, ?, ?)",
            (username, nickname, generate_password_hash(password)),
        )
        db.commit()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            flash("Welcome back!", "success")
            return redirect(url_for("home"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/post", methods=["POST"])
@login_required
def create_post():
    user = get_current_user()
    content = request.form.get("content", "").strip()
    image_file = request.files.get("image")

    if not content and (image_file is None or not image_file.filename):
        flash("Write something or add an image before posting.", "warning")
        return redirect(url_for("home"))

    image_path = None
    if image_file and image_file.filename:
        image_path = save_upload(image_file, "posts")

    db = get_db()
    db.execute(
        "INSERT INTO posts (user_id, content, image_path) VALUES (?, ?, ?)",
        (user["id"], content, image_path),
    )
    db.commit()

    flash("Your post is live!", "success")
    return redirect(url_for("home"))


@app.route("/my_posts")
@login_required
def my_posts():
    user = get_current_user()
    db = get_db()
    posts = db.execute(
        """
        SELECT posts.*, users.username, users.nickname, users.profile_photo
        FROM posts
        JOIN users ON users.id = posts.user_id
        WHERE posts.user_id = ?
        ORDER BY posts.created_at DESC
        """,
        (user["id"],),
    ).fetchall()
    return render_template("my_posts.html", posts=posts, current_user=user)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = get_current_user()
    if request.method == "POST":
        new_username = request.form.get("username", "").strip()
        new_nickname = request.form.get("nickname", "").strip()
        profile_photo = request.files.get("profile_photo")

        if not new_username or not new_nickname:
            flash("Username and nickname are required.", "danger")
            return render_template("profile.html", current_user=user)

        db = get_db()
        other_user = db.execute(
            "SELECT id FROM users WHERE username = ? AND id != ?",
            (new_username, user["id"]),
        ).fetchone()

        if other_user:
            flash("That username is already used by someone else.", "danger")
            return render_template("profile.html", current_user=user)

        db.execute(
            "UPDATE users SET username = ?, nickname = ? WHERE id = ?",
            (new_username, new_nickname, user["id"]),
        )

        if profile_photo and profile_photo.filename:
            photo_path = save_upload(profile_photo, "profile_photos")
            if photo_path:
                db.execute(
                    "UPDATE users SET profile_photo = ? WHERE id = ?",
                    (photo_path, user["id"]),
                )

        db.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", current_user=get_current_user())


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = get_current_user()
    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if new_password:
            if not check_password_hash(user["password"], old_password):
                flash("Current password is incorrect.", "danger")
                return render_template("settings.html", current_user=user)

            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return render_template("settings.html", current_user=user)

            db = get_db()
            db.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (generate_password_hash(new_password), user["id"]),
            )
            db.commit()
            flash("Password updated successfully.", "success")

    return render_template("settings.html", current_user=user)


@app.context_processor
def inject_user():
    return {"current_user": get_current_user()}


with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
