import os
import re
import sqlite3
from functools import wraps
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from markupsafe import Markup, escape

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "blog.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

app = Flask(__name__)
app.config["SECRET_KEY"] = "nostalgic-blog-secret"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
REACTION_EMOJIS = ("❤️", "😂", "😮", "😢", "👏")
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "ogg"}
HASHTAG_PATTERN = re.compile(r"(?<![\w&])#([\w]{1,50})", re.UNICODE)

os.makedirs(os.path.join(UPLOAD_FOLDER, "profile_photos"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "posts"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "comments"), exist_ok=True)


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
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
    user_columns = {column["name"] for column in db.execute("PRAGMA table_info(users)")}
    if "is_private" not in user_columns:
        db.execute("ALTER TABLE users ADD COLUMN is_private INTEGER NOT NULL DEFAULT 0")
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
    post_columns = {column["name"] for column in db.execute("PRAGMA table_info(posts)")}
    if "media_type" not in post_columns:
        db.execute("ALTER TABLE posts ADD COLUMN media_type TEXT NOT NULL DEFAULT 'image'")
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS likes (
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, post_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
        """
    )
    comment_columns = {
        column["name"] for column in db.execute("PRAGMA table_info(comments)")
    }
    if "image_path" not in comment_columns:
        db.execute("ALTER TABLE comments ADD COLUMN image_path TEXT")
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS reactions (
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            emoji TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, post_id, emoji),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS follows (
            follower_id INTEGER NOT NULL,
            followed_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (follower_id, followed_id),
            CHECK (follower_id != followed_id),
            FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (followed_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS blocks (
            blocker_id INTEGER NOT NULL,
            blocked_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (blocker_id, blocked_id),
            CHECK (blocker_id != blocked_id),
            FOREIGN KEY (blocker_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (blocked_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS friend_requests (
            requester_id INTEGER NOT NULL,
            recipient_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (requester_id, recipient_id),
            CHECK (requester_id != recipient_id),
            FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            recipient_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    message_columns = {
        column["name"] for column in db.execute("PRAGMA table_info(messages)")
    }
    if "is_read" not in message_columns:
        db.execute(
            "ALTER TABLE messages ADD COLUMN is_read INTEGER NOT NULL DEFAULT 1"
        )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_messages_participants "
        "ON messages(sender_id, recipient_id, created_at)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_messages_unread "
        "ON messages(recipient_id, is_read)"
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS group_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            creator_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE SET NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS group_chat_members (
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            last_read_message_id INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (group_id, user_id),
            FOREIGN KEY (group_id) REFERENCES group_chats(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS group_chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES group_chats(id) ON DELETE CASCADE,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_group_chat_messages "
        "ON group_chat_messages(group_id, id)"
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_id INTEGER NOT NULL,
            actor_id INTEGER,
            kind TEXT NOT NULL,
            reference_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_at TIMESTAMP,
            FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_notifications_recipient_read "
        "ON notifications(recipient_id, read_at, created_at)"
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS post_hashtags (
            post_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            PRIMARY KEY (post_id, tag),
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
        """
    )
    db.execute("CREATE INDEX IF NOT EXISTS idx_post_hashtags_tag ON post_hashtags(tag)")
    for post in db.execute("SELECT id, content FROM posts").fetchall():
        db.executemany(
            "INSERT OR IGNORE INTO post_hashtags (post_id, tag) VALUES (?, ?)",
            [(post["id"], tag.casefold()) for tag in extract_hashtags(post["content"])],
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


def extract_hashtags(content):
    return {match.group(1).casefold() for match in HASHTAG_PATTERN.finditer(content or "")}


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


def validate_post_upload(file):
    if file is None or not file.filename:
        return None, None
    extension = secure_filename(file.filename).rsplit(".", 1)
    if len(extension) != 2:
        return None, None
    extension = extension[1].lower()
    if extension in IMAGE_EXTENSIONS:
        media_type = "image"
    elif extension in VIDEO_EXTENSIONS:
        media_type = "video"
    else:
        return None, None
    return file, media_type


def linkify_hashtags(content):
    escaped_content = str(escape(content or ""))

    def replace(match):
        tag = match.group(1)
        href = url_for("hashtag_feed", tag=tag.casefold())
        return f'<a class="hashtag" href="{escape(href)}">#{tag}</a>'

    return Markup(HASHTAG_PATTERN.sub(replace, escaped_content))


def load_posts(query, params, user_id):
    db = get_db()
    post_rows = db.execute(query, params).fetchall()
    posts = [dict(post) for post in post_rows]
    if not posts:
        return []

    post_ids = [post["id"] for post in posts]
    placeholders = ",".join("?" for _ in post_ids)
    comments = db.execute(
        f"""
        SELECT comments.*, users.username, users.nickname, users.profile_photo
        FROM comments
        JOIN users ON users.id = comments.user_id
        WHERE comments.post_id IN ({placeholders})
          AND NOT EXISTS (
              SELECT 1 FROM blocks
              WHERE (blocks.blocker_id = ? AND blocks.blocked_id = comments.user_id)
                 OR (blocks.blocker_id = comments.user_id AND blocks.blocked_id = ?)
          )
        ORDER BY comments.created_at ASC, comments.id ASC
        """,
        [*post_ids, user_id, user_id],
    ).fetchall()
    reactions = db.execute(
        f"""
        SELECT post_id, emoji, COUNT(*) AS reaction_count,
               MAX(CASE WHEN user_id = ? THEN 1 ELSE 0 END) AS reacted_by_user
        FROM reactions
        WHERE post_id IN ({placeholders})
        GROUP BY post_id, emoji
        """,
        [user_id, *post_ids],
    ).fetchall()
    hashtags = db.execute(
        f"""
        SELECT post_id, tag
        FROM post_hashtags
        WHERE post_id IN ({placeholders})
        ORDER BY tag
        """,
        post_ids,
    ).fetchall()

    comments_by_post = {post_id: [] for post_id in post_ids}
    for comment in comments:
        comments_by_post[comment["post_id"]].append(comment)

    reactions_by_post = {post_id: {} for post_id in post_ids}
    for reaction in reactions:
        reactions_by_post[reaction["post_id"]][reaction["emoji"]] = {
            "count": reaction["reaction_count"],
            "selected": bool(reaction["reacted_by_user"]),
        }
    hashtags_by_post = {post_id: [] for post_id in post_ids}
    for hashtag in hashtags:
        hashtags_by_post[hashtag["post_id"]].append(hashtag["tag"])

    for post in posts:
        post["comments"] = comments_by_post[post["id"]]
        post["reactions"] = reactions_by_post[post["id"]]
        post["hashtags"] = hashtags_by_post[post["id"]]

    return posts


def safe_referrer(default):
    referrer = request.referrer
    if not referrer:
        return default
    parsed = urlparse(referrer)
    if parsed.netloc and parsed.netloc != request.host:
        return default
    if not parsed.path.startswith("/") or parsed.path.startswith("//"):
        return default
    return parsed.path + (f"?{parsed.query}" if parsed.query else "")


def is_blocked_between(db, first_user_id, second_user_id):
    return db.execute(
        """
        SELECT 1 FROM blocks
        WHERE (blocker_id = ? AND blocked_id = ?)
           OR (blocker_id = ? AND blocked_id = ?)
        """,
        (first_user_id, second_user_id, second_user_id, first_user_id),
    ).fetchone() is not None


def can_interact_with_post(db, post_id, user_id):
    post = db.execute(
        """
        SELECT posts.user_id, users.is_private
        FROM posts JOIN users ON users.id = posts.user_id
        WHERE posts.id = ?
        """,
        (post_id,),
    ).fetchone()
    if post is None or is_blocked_between(db, user_id, post["user_id"]):
        return False
    return not post["is_private"] or post["user_id"] == user_id or are_friends(
        db, user_id, post["user_id"]
    )


def are_friends(db, first_user_id, second_user_id):
    return db.execute(
        """
        SELECT 1
        FROM follows AS first_follow
        JOIN follows AS second_follow
          ON second_follow.follower_id = first_follow.followed_id
         AND second_follow.followed_id = first_follow.follower_id
        WHERE first_follow.follower_id = ? AND first_follow.followed_id = ?
        """,
        (first_user_id, second_user_id),
    ).fetchone() is not None


def can_view_user_posts(db, owner_id, viewer_id, is_private):
    if owner_id == viewer_id:
        return True
    if is_blocked_between(db, owner_id, viewer_id):
        return False
    return not is_private or are_friends(db, owner_id, viewer_id)


def can_message_user(db, sender_id, recipient_id, recipient_is_private):
    if sender_id == recipient_id or is_blocked_between(db, sender_id, recipient_id):
        return False
    return not recipient_is_private or are_friends(db, sender_id, recipient_id)


def add_notification(db, recipient_id, actor_id, kind, reference_id=None):
    db.execute(
        """
        INSERT INTO notifications (recipient_id, actor_id, kind, reference_id)
        VALUES (?, ?, ?, ?)
        """,
        (recipient_id, actor_id, kind, reference_id),
    )


def post_ranking_sql():
    return """
        (
            1.0
            + (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) * 2.0
            + (SELECT COUNT(*) FROM comments WHERE comments.post_id = posts.id) * 3.0
            + (SELECT COUNT(*) FROM reactions WHERE reactions.post_id = posts.id) * 2.0
            + CASE WHEN EXISTS (
                SELECT 1 FROM follows
                WHERE follows.follower_id = ? AND follows.followed_id = posts.user_id
            ) THEN 6.0 ELSE 0.0 END
        ) / (
            1.0 + MAX(0.0, (julianday('now') - julianday(posts.created_at)) * 24.0) / 18.0
        )
    """


def post_select_sql():
    return f"""
        SELECT posts.*, users.username, users.nickname, users.profile_photo,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count,
               EXISTS(
                   SELECT 1 FROM likes
                   WHERE likes.post_id = posts.id AND likes.user_id = ?
               ) AS liked_by_user,
               {post_ranking_sql()} AS ranking_score
        FROM posts
        JOIN users ON users.id = posts.user_id
    """


def blocked_post_filter_sql():
    return """
        NOT EXISTS (
            SELECT 1 FROM blocks
            WHERE (blocks.blocker_id = ? AND blocks.blocked_id = users.id)
               OR (blocks.blocker_id = users.id AND blocks.blocked_id = ?)
        )
    """


def private_post_filter_sql():
    return """
        (
            users.id = ?
            OR users.is_private = 0
            OR EXISTS (
                SELECT 1 FROM follows AS owner_follow
                JOIN follows AS viewer_follow
                  ON viewer_follow.follower_id = owner_follow.followed_id
                 AND viewer_follow.followed_id = owner_follow.follower_id
                WHERE owner_follow.follower_id = users.id
                  AND owner_follow.followed_id = ?
            )
        )
    """


def suggested_people(user_id, limit=5):
    db = get_db()
    return db.execute(
        """
        SELECT users.id, users.username, users.nickname, users.profile_photo,
               (SELECT COUNT(*) FROM follows WHERE followed_id = users.id) AS follower_count,
               (
                   (SELECT COUNT(*)
                    FROM follows AS my_follows
                    JOIN follows AS their_follows
                      ON their_follows.followed_id = my_follows.followed_id
                    WHERE my_follows.follower_id = ?
                      AND their_follows.follower_id = users.id) * 4.0
                   + (SELECT COUNT(*)
                      FROM follows AS my_followers
                      JOIN follows AS their_followers
                        ON their_followers.follower_id = my_followers.follower_id
                      WHERE my_followers.followed_id = ?
                        AND their_followers.followed_id = users.id) * 3.0
                   + (SELECT COUNT(*)
                      FROM (
                          SELECT DISTINCT tag FROM post_hashtags
                          JOIN posts AS my_posts ON my_posts.id = post_hashtags.post_id
                          WHERE my_posts.user_id = ?
                      ) AS my_tags
                      JOIN (
                          SELECT DISTINCT tag FROM post_hashtags
                          JOIN posts AS their_posts ON their_posts.id = post_hashtags.post_id
                          WHERE their_posts.user_id = users.id
                      ) AS their_tags USING (tag)) * 2.0
                   + MIN((SELECT COUNT(*) FROM follows WHERE followed_id = users.id), 100) * 0.05
               ) AS suggestion_score
        FROM users
        WHERE users.id != ?
          AND NOT EXISTS (
              SELECT 1 FROM follows
              WHERE follower_id = ? AND followed_id = users.id
          )
          AND NOT EXISTS (
              SELECT 1 FROM blocks
              WHERE (blocker_id = ? AND blocked_id = users.id)
                 OR (blocker_id = users.id AND blocked_id = ?)
          )
        ORDER BY suggestion_score DESC, users.created_at DESC, users.username COLLATE NOCASE
        LIMIT ?
        """,
        (user_id, user_id, user_id, user_id, user_id, user_id, user_id, limit),
    ).fetchall()


app.add_template_filter(linkify_hashtags, "linkify_hashtags")


@app.route("/")
@login_required
def home():
    user = get_current_user()
    posts = load_posts(
        f"""
        {post_select_sql()}
        WHERE {blocked_post_filter_sql()}
          AND {private_post_filter_sql()}
        ORDER BY ranking_score DESC, posts.created_at DESC
        """,
        (user["id"], user["id"], user["id"], user["id"], user["id"], user["id"]),
        user["id"],
    )
    return render_template(
        "home.html",
        posts=posts,
        current_user=user,
    )


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
    media_file, media_type = validate_post_upload(request.files.get("media"))

    if request.files.get("media") and request.files["media"].filename and media_file is None:
        flash("Choose an image or a supported video file (MP4, WebM, MOV, or OGG).", "warning")
        return redirect(url_for("home"))
    if not content and media_file is None:
        flash("Write something or attach an image or video before posting.", "warning")
        return redirect(url_for("home"))

    image_path = None
    if media_file:
        image_path = save_upload(media_file, "posts")

    db = get_db()
    cursor = db.execute(
        "INSERT INTO posts (user_id, content, image_path, media_type) VALUES (?, ?, ?, ?)",
        (user["id"], content, image_path, media_type or "image"),
    )
    post_id = cursor.lastrowid
    db.executemany(
        "INSERT INTO post_hashtags (post_id, tag) VALUES (?, ?)",
        [(post_id, tag) for tag in extract_hashtags(content)],
    )
    db.commit()

    flash("Your post is live!", "success")
    return redirect(url_for("home"))


@app.route("/posts/<int:post_id>/like", methods=["POST"])
@login_required
def toggle_like(post_id):
    user = get_current_user()
    db = get_db()
    post = db.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        flash("That post could not be found.", "danger")
        return redirect(url_for("home"))
    if not can_interact_with_post(db, post_id, user["id"]):
        flash("You cannot interact with this post.", "warning")
        return redirect(safe_referrer(url_for("home")))

    existing = db.execute(
        "SELECT 1 FROM likes WHERE user_id = ? AND post_id = ?",
        (user["id"], post_id),
    ).fetchone()
    if existing:
        db.execute(
            "DELETE FROM likes WHERE user_id = ? AND post_id = ?",
            (user["id"], post_id),
        )
    else:
        db.execute(
            "INSERT INTO likes (user_id, post_id) VALUES (?, ?)",
            (user["id"], post_id),
        )
    db.commit()
    return redirect(safe_referrer(url_for("home")))


@app.route("/posts/<int:post_id>/comments", methods=["POST"])
@login_required
def add_comment(post_id):
    user = get_current_user()
    content = request.form.get("content", "").strip()
    image_file = request.files.get("image")
    has_image = image_file is not None and bool(image_file.filename)
    if not content and not has_image:
        flash("Write a comment or attach an image before submitting.", "warning")
        return redirect(f"{safe_referrer(url_for('home'))}#comments-{post_id}")
    if len(content) > 1000:
        flash("Comments must be 1,000 characters or fewer.", "warning")
        return redirect(f"{safe_referrer(url_for('home'))}#comments-{post_id}")

    db = get_db()
    post = db.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        flash("That post could not be found.", "danger")
        return redirect(url_for("home"))
    if not can_interact_with_post(db, post_id, user["id"]):
        flash("You cannot interact with this post.", "warning")
        return redirect(f"{safe_referrer(url_for('home'))}#comments-{post_id}")

    image_path = save_upload(image_file, "comments") if has_image else None
    db.execute(
        "INSERT INTO comments (user_id, post_id, content, image_path) VALUES (?, ?, ?, ?)",
        (user["id"], post_id, content, image_path),
    )
    db.commit()
    return redirect(f"{safe_referrer(url_for('home'))}#post-{post_id}")


@app.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    user = get_current_user()
    db = get_db()
    comment = db.execute(
        "SELECT id, user_id, post_id, image_path FROM comments WHERE id = ?",
        (comment_id,),
    ).fetchone()
    if comment is None:
        flash("That comment could not be found.", "danger")
        return redirect(safe_referrer(url_for("home")))
    if comment["user_id"] != user["id"]:
        flash("You can only delete your own comments.", "danger")
        return redirect(f"{safe_referrer(url_for('home'))}#post-{comment['post_id']}")

    db.execute("DELETE FROM comments WHERE id = ? AND user_id = ?", (comment_id, user["id"]))
    db.commit()

    if comment["image_path"] and comment["image_path"].startswith("uploads/comments/"):
        filename = os.path.basename(comment["image_path"])
        image_path = os.path.join(UPLOAD_FOLDER, "comments", filename)
        if os.path.isfile(image_path):
            os.remove(image_path)

    return redirect(f"{safe_referrer(url_for('home'))}#post-{comment['post_id']}")


@app.route("/posts/<int:post_id>/reactions", methods=["POST"])
@login_required
def toggle_reaction(post_id):
    user = get_current_user()
    emoji = request.form.get("emoji", "")
    if emoji not in REACTION_EMOJIS:
        flash("That reaction is not supported.", "warning")
        return redirect(safe_referrer(url_for("home")))

    db = get_db()
    post = db.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        flash("That post could not be found.", "danger")
        return redirect(url_for("home"))
    if not can_interact_with_post(db, post_id, user["id"]):
        flash("You cannot interact with this post.", "warning")
        return redirect(f"{safe_referrer(url_for('home'))}#post-{post_id}")

    existing = db.execute(
        "SELECT 1 FROM reactions WHERE user_id = ? AND post_id = ? AND emoji = ?",
        (user["id"], post_id, emoji),
    ).fetchone()
    if existing:
        db.execute(
            "DELETE FROM reactions WHERE user_id = ? AND post_id = ? AND emoji = ?",
            (user["id"], post_id, emoji),
        )
    else:
        db.execute(
            "INSERT INTO reactions (user_id, post_id, emoji) VALUES (?, ?, ?)",
            (user["id"], post_id, emoji),
        )
    db.commit()
    return redirect(f"{safe_referrer(url_for('home'))}#post-{post_id}")


@app.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    user = get_current_user()
    db = get_db()
    post = db.execute(
        "SELECT id, user_id, image_path FROM posts WHERE id = ?",
        (post_id,),
    ).fetchone()
    if post is None:
        flash("That post could not be found.", "danger")
        return redirect(url_for("my_posts"))
    if post["user_id"] != user["id"]:
        flash("You can only delete your own posts.", "danger")
        return redirect(safe_referrer(url_for("home")))

    comment_images = db.execute(
        "SELECT image_path FROM comments WHERE post_id = ? AND image_path IS NOT NULL",
        (post_id,),
    ).fetchall()
    db.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
    db.execute("DELETE FROM likes WHERE post_id = ?", (post_id,))
    db.execute("DELETE FROM reactions WHERE post_id = ?", (post_id,))
    db.execute("DELETE FROM posts WHERE id = ? AND user_id = ?", (post_id, user["id"]))
    db.commit()

    if post["image_path"] and post["image_path"].startswith("uploads/posts/"):
        filename = os.path.basename(post["image_path"])
        image_path = os.path.join(UPLOAD_FOLDER, "posts", filename)
        if os.path.isfile(image_path):
            os.remove(image_path)

    for comment_image in comment_images:
        image_path = comment_image["image_path"]
        if image_path.startswith("uploads/comments/"):
            filename = os.path.basename(image_path)
            image_path = os.path.join(UPLOAD_FOLDER, "comments", filename)
            if os.path.isfile(image_path):
                os.remove(image_path)

    flash("Post deleted.", "success")
    return redirect(safe_referrer(url_for("my_posts")))


@app.route("/my_posts")
@login_required
def my_posts():
    user = get_current_user()
    posts = load_posts(
        """
        SELECT posts.*, users.username, users.nickname, users.profile_photo,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count,
               EXISTS(
                   SELECT 1 FROM likes
                   WHERE likes.post_id = posts.id AND likes.user_id = ?
               ) AS liked_by_user
        FROM posts
        JOIN users ON users.id = posts.user_id
        WHERE posts.user_id = ?
        ORDER BY posts.created_at DESC
        """,
        (user["id"], user["id"]),
        user["id"],
    )
    return render_template("my_posts.html", posts=posts, current_user=user)


@app.route("/tags/<tag>")
@login_required
def hashtag_feed(tag):
    normalized_tag = tag.casefold().lstrip("#")
    if not re.fullmatch(r"[\w]{1,50}", normalized_tag, re.UNICODE):
        flash("That hashtag is not valid.", "warning")
        return redirect(url_for("home"))

    user = get_current_user()
    posts = load_posts(
        f"""
        {post_select_sql()}
        JOIN post_hashtags ON post_hashtags.post_id = posts.id
        WHERE post_hashtags.tag = ?
          AND {blocked_post_filter_sql()}
          AND {private_post_filter_sql()}
        ORDER BY ranking_score DESC, posts.created_at DESC
        """,
        (
            user["id"],
            user["id"],
            normalized_tag,
            user["id"],
            user["id"],
            user["id"],
            user["id"],
        ),
        user["id"],
    )
    return render_template(
        "hashtag_feed.html",
        posts=posts,
        tag=normalized_tag,
        current_user=user,
    )


@app.route("/people")
@login_required
def people():
    user = get_current_user()
    db = get_db()
    people_rows = db.execute(
        """
        SELECT users.id, users.username, users.nickname, users.profile_photo,
               (SELECT COUNT(*) FROM follows WHERE followed_id = users.id) AS follower_count,
               EXISTS(
                   SELECT 1 FROM follows
                   WHERE follower_id = ? AND followed_id = users.id
               ) AS is_following,
               EXISTS(
                   SELECT 1 FROM blocks
                   WHERE blocker_id = ? AND blocked_id = users.id
               ) AS is_blocked,
               EXISTS(
                   SELECT 1 FROM blocks
                   WHERE blocker_id = users.id AND blocked_id = ?
               ) AS blocked_viewer,
               EXISTS(
                   SELECT 1 FROM follows AS owner_follow
                   JOIN follows AS viewer_follow
                     ON viewer_follow.follower_id = owner_follow.followed_id
                    AND viewer_follow.followed_id = owner_follow.follower_id
                   WHERE owner_follow.follower_id = users.id
                     AND owner_follow.followed_id = ?
               ) AS is_friend,
               EXISTS(
                   SELECT 1 FROM friend_requests
                   WHERE requester_id = ? AND recipient_id = users.id
               ) AS request_sent,
               EXISTS(
                   SELECT 1 FROM friend_requests
                   WHERE requester_id = users.id AND recipient_id = ?
               ) AS request_received,
               (
                   (SELECT COUNT(*)
                    FROM follows AS my_follows
                    JOIN follows AS their_follows
                      ON their_follows.followed_id = my_follows.followed_id
                    WHERE my_follows.follower_id = ?
                      AND their_follows.follower_id = users.id) * 4.0
                   + (SELECT COUNT(*)
                      FROM follows AS my_followers
                      JOIN follows AS their_followers
                        ON their_followers.follower_id = my_followers.follower_id
                      WHERE my_followers.followed_id = ?
                        AND their_followers.followed_id = users.id) * 3.0
                   + (SELECT COUNT(*)
                      FROM (
                          SELECT DISTINCT tag FROM post_hashtags
                          JOIN posts AS my_posts ON my_posts.id = post_hashtags.post_id
                          WHERE my_posts.user_id = ?
                      ) AS my_tags
                      JOIN (
                          SELECT DISTINCT tag FROM post_hashtags
                          JOIN posts AS their_posts ON their_posts.id = post_hashtags.post_id
                          WHERE their_posts.user_id = users.id
                      ) AS their_tags USING (tag)) * 2.0
                   + MIN((SELECT COUNT(*) FROM follows WHERE followed_id = users.id), 100) * 0.05
               ) AS suggestion_score
        FROM users
        WHERE users.id != ?
        ORDER BY suggestion_score DESC, users.created_at DESC, users.username COLLATE NOCASE
        """,
        (
            user["id"],
            user["id"],
            user["id"],
            user["id"],
            user["id"],
            user["id"],
            user["id"],
            user["id"],
            user["id"],
            user["id"],
        ),
    ).fetchall()
    return render_template("people.html", people=people_rows, current_user=user)


@app.route("/friends")
@login_required
def friends():
    user = get_current_user()
    db = get_db()
    friend_rows = db.execute(
        """
        SELECT users.id, users.username, users.nickname, users.profile_photo
        FROM follows AS my_follow
        JOIN follows AS friend_follow
          ON friend_follow.follower_id = my_follow.followed_id
         AND friend_follow.followed_id = my_follow.follower_id
        JOIN users ON users.id = my_follow.followed_id
        WHERE my_follow.follower_id = ?
          AND NOT EXISTS (
              SELECT 1 FROM blocks
              WHERE (blocks.blocker_id = ? AND blocks.blocked_id = users.id)
                 OR (blocks.blocker_id = users.id AND blocks.blocked_id = ?)
          )
        ORDER BY users.username COLLATE NOCASE
        """,
        (user["id"], user["id"], user["id"]),
    ).fetchall()
    friends_with_posts = []
    for friend in friend_rows:
        person = dict(friend)
        person["posts"] = load_posts(
            f"""
            {post_select_sql()}
            WHERE posts.user_id = ?
              AND {blocked_post_filter_sql()}
            ORDER BY posts.created_at DESC
            """,
            (user["id"], user["id"], friend["id"], user["id"], user["id"]),
            user["id"],
        )
        friends_with_posts.append(person)
    return render_template(
        "friends.html",
        friends=friends_with_posts,
        current_user=user,
    )


@app.route("/users/<username>")
@login_required
def user_profile(username):
    user = get_current_user()
    db = get_db()
    viewed_user = db.execute(
        """
        SELECT users.*,
               (SELECT COUNT(*) FROM follows WHERE followed_id = users.id) AS follower_count,
               (SELECT COUNT(*) FROM follows WHERE follower_id = users.id) AS following_count,
               EXISTS(
                   SELECT 1 FROM follows
                   WHERE follower_id = ? AND followed_id = users.id
               ) AS is_following,
               EXISTS(
                   SELECT 1 FROM blocks
                   WHERE blocker_id = ? AND blocked_id = users.id
               ) AS is_blocked,
               EXISTS(
                   SELECT 1 FROM follows AS owner_follow
                   JOIN follows AS viewer_follow
                     ON viewer_follow.follower_id = owner_follow.followed_id
                    AND viewer_follow.followed_id = owner_follow.follower_id
                   WHERE owner_follow.follower_id = users.id
                     AND owner_follow.followed_id = ?
               ) AS is_friend,
               EXISTS(
                   SELECT 1 FROM friend_requests
                   WHERE requester_id = ? AND recipient_id = users.id
               ) AS request_sent,
               EXISTS(
                   SELECT 1 FROM friend_requests
                   WHERE requester_id = users.id AND recipient_id = ?
               ) AS request_received
        FROM users
        WHERE users.username = ?
        """,
        (user["id"], user["id"], user["id"], user["id"], user["id"], username),
    ).fetchone()
    if viewed_user is None or viewed_user["id"] == user["id"]:
        return redirect(url_for("profile"))

    blocked_by_viewer = bool(viewed_user["is_blocked"])
    blocked_viewer = db.execute(
        "SELECT 1 FROM blocks WHERE blocker_id = ? AND blocked_id = ?",
        (viewed_user["id"], user["id"]),
    ).fetchone() is not None
    blocked_viewer = blocked_viewer and not blocked_by_viewer
    posts = []
    can_view_posts = (
        not blocked_by_viewer
        and not blocked_viewer
        and can_view_user_posts(db, viewed_user["id"], user["id"], viewed_user["is_private"])
    )
    if can_view_posts:
        posts = load_posts(
            f"""
            {post_select_sql()}
            WHERE posts.user_id = ?
            ORDER BY posts.created_at DESC
            """,
            (user["id"], user["id"], viewed_user["id"]),
            user["id"],
        )
    return render_template(
        "user_profile.html",
        viewed_user=viewed_user,
        posts=posts,
        blocked_by_viewer=blocked_by_viewer,
        blocked_viewer=blocked_viewer,
        can_view_posts=can_view_posts,
        can_message=can_message_user(
            db, user["id"], viewed_user["id"], viewed_user["is_private"]
        ),
        current_user=user,
    )


@app.route("/users/<int:target_id>/follow", methods=["POST"])
@login_required
def toggle_follow(target_id):
    user = get_current_user()
    db = get_db()
    target = db.execute("SELECT id FROM users WHERE id = ?", (target_id,)).fetchone()
    if target is None or target_id == user["id"]:
        flash("That account is not available to follow.", "warning")
        return redirect(safe_referrer(url_for("people")))
    if is_blocked_between(db, user["id"], target_id):
        flash("Following is unavailable while either account has blocked the other.", "warning")
        return redirect(safe_referrer(url_for("people")))

    existing = db.execute(
        "SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?",
        (user["id"], target_id),
    ).fetchone()
    if existing:
        db.execute(
            "DELETE FROM follows WHERE follower_id = ? AND followed_id = ?",
            (user["id"], target_id),
        )
    else:
        db.execute(
            "INSERT INTO follows (follower_id, followed_id) VALUES (?, ?)",
            (user["id"], target_id),
        )
    db.commit()
    return redirect(safe_referrer(url_for("people")))


@app.route("/friend-requests")
@login_required
def friend_requests():
    user = get_current_user()
    db = get_db()
    incoming = db.execute(
        """
        SELECT users.id, users.username, users.nickname, users.profile_photo,
               friend_requests.created_at
        FROM friend_requests
        JOIN users ON users.id = friend_requests.requester_id
        WHERE friend_requests.recipient_id = ?
        ORDER BY friend_requests.created_at DESC
        """,
        (user["id"],),
    ).fetchall()
    outgoing = db.execute(
        """
        SELECT users.id, users.username, users.nickname, users.profile_photo,
               friend_requests.created_at
        FROM friend_requests
        JOIN users ON users.id = friend_requests.recipient_id
        WHERE friend_requests.requester_id = ?
        ORDER BY friend_requests.created_at DESC
        """,
        (user["id"],),
    ).fetchall()
    return render_template(
        "friend_requests.html",
        incoming=incoming,
        outgoing=outgoing,
        current_user=user,
    )


@app.route("/users/<int:target_id>/friend-request", methods=["POST"])
@login_required
def send_friend_request(target_id):
    user = get_current_user()
    db = get_db()
    target = db.execute("SELECT id FROM users WHERE id = ?", (target_id,)).fetchone()
    if target is None or target_id == user["id"]:
        flash("That account is not available for a friend request.", "warning")
        return redirect(safe_referrer(url_for("people")))
    if is_blocked_between(db, user["id"], target_id):
        flash("You cannot send a friend request to this account.", "warning")
        return redirect(safe_referrer(url_for("people")))
    if are_friends(db, user["id"], target_id):
        flash("You are already friends with this account.", "info")
        return redirect(safe_referrer(url_for("people")))

    pending = db.execute(
        "SELECT 1 FROM friend_requests WHERE requester_id = ? AND recipient_id = ?",
        (user["id"], target_id),
    ).fetchone()
    if pending:
        db.execute(
            "DELETE FROM friend_requests WHERE requester_id = ? AND recipient_id = ?",
            (user["id"], target_id),
        )
        db.execute(
            """
            DELETE FROM notifications
            WHERE recipient_id = ? AND actor_id = ? AND kind = 'friend_request'
            """,
            (target_id, user["id"]),
        )
        flash("Friend request canceled.", "success")
    else:
        reverse_pending = db.execute(
            "SELECT 1 FROM friend_requests WHERE requester_id = ? AND recipient_id = ?",
            (target_id, user["id"]),
        ).fetchone()
        if reverse_pending:
            flash("They already sent you a request. Review it on Friend Requests.", "info")
        else:
            db.execute(
                "INSERT INTO friend_requests (requester_id, recipient_id) VALUES (?, ?)",
                (user["id"], target_id),
            )
            add_notification(db, target_id, user["id"], "friend_request")
            flash("Friend request sent.", "success")
    db.commit()
    return redirect(safe_referrer(url_for("friend_requests")))


@app.route("/friend-requests/<int:requester_id>/respond", methods=["POST"])
@login_required
def respond_friend_request(requester_id):
    user = get_current_user()
    db = get_db()
    decision = request.form.get("decision")
    if decision not in {"accept", "decline"}:
        flash("Choose whether to accept or decline the friend request.", "warning")
        return redirect(url_for("friend_requests"))
    friend_request = db.execute(
        """
        SELECT 1 FROM friend_requests
        WHERE requester_id = ? AND recipient_id = ?
        """,
        (requester_id, user["id"]),
    ).fetchone()
    if not friend_request:
        flash("That friend request is no longer available.", "warning")
        return redirect(url_for("friend_requests"))

    if decision == "accept":
        if is_blocked_between(db, user["id"], requester_id):
            db.execute(
                "DELETE FROM friend_requests WHERE requester_id = ? AND recipient_id = ?",
                (requester_id, user["id"]),
            )
            db.commit()
            flash("You cannot accept a request while either account has blocked the other.", "warning")
            return redirect(url_for("friend_requests"))
        db.execute(
            "INSERT OR IGNORE INTO follows (follower_id, followed_id) VALUES (?, ?)",
            (user["id"], requester_id),
        )
        db.execute(
            "INSERT OR IGNORE INTO follows (follower_id, followed_id) VALUES (?, ?)",
            (requester_id, user["id"]),
        )
        add_notification(db, requester_id, user["id"], "friend_accepted")
        flash("Friend request accepted.", "success")
    else:
        flash("Friend request declined.", "success")
    db.execute(
        """
        DELETE FROM friend_requests
        WHERE (requester_id = ? AND recipient_id = ?)
           OR (requester_id = ? AND recipient_id = ?)
        """,
        (requester_id, user["id"], user["id"], requester_id),
    )
    db.execute(
        """
        DELETE FROM notifications
        WHERE (recipient_id = ? AND actor_id = ? AND kind = 'friend_request')
           OR (recipient_id = ? AND actor_id = ? AND kind = 'friend_request')
        """,
        (user["id"], requester_id, requester_id, user["id"]),
    )
    db.commit()
    return redirect(url_for("friend_requests"))


def load_group_chats(db, user_id):
    return db.execute(
        """
        SELECT group_chats.id, group_chats.name,
               (SELECT group_chat_messages.content
                FROM group_chat_messages
                WHERE group_chat_messages.group_id = group_chats.id
                ORDER BY group_chat_messages.id DESC
                LIMIT 1) AS latest_message,
               (SELECT group_chat_messages.created_at
                FROM group_chat_messages
                WHERE group_chat_messages.group_id = group_chats.id
                ORDER BY group_chat_messages.id DESC
                LIMIT 1) AS latest_at,
               (SELECT COUNT(*)
                FROM group_chat_messages
                WHERE group_chat_messages.group_id = group_chats.id
                  AND group_chat_messages.sender_id != ?
                  AND group_chat_messages.id > group_chat_members.last_read_message_id
               ) AS unread_count
        FROM group_chat_members
        JOIN group_chats ON group_chats.id = group_chat_members.group_id
        WHERE group_chat_members.user_id = ?
        ORDER BY latest_at DESC, group_chats.id DESC
        """,
        (user_id, user_id),
    ).fetchall()


@app.route("/messages/groups/new", methods=["GET", "POST"])
@login_required
def create_group_chat():
    user = get_current_user()
    db = get_db()
    eligible_friends = db.execute(
        """
        SELECT users.id, users.username, users.nickname, users.profile_photo
        FROM follows AS my_follow
        JOIN follows AS friend_follow
          ON friend_follow.follower_id = my_follow.followed_id
         AND friend_follow.followed_id = my_follow.follower_id
        JOIN users ON users.id = my_follow.followed_id
        WHERE my_follow.follower_id = ?
          AND NOT EXISTS (
              SELECT 1 FROM blocks
              WHERE (blocks.blocker_id = ? AND blocks.blocked_id = users.id)
                 OR (blocks.blocker_id = users.id AND blocks.blocked_id = ?)
          )
        ORDER BY users.username COLLATE NOCASE
        """,
        (user["id"], user["id"], user["id"]),
    ).fetchall()
    friend_ids = {friend["id"] for friend in eligible_friends}

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        selected_ids = {
            int(value)
            for value in request.form.getlist("members")
            if value.isdigit()
        }
        selected_ids.intersection_update(friend_ids)
        if not name or len(name) > 80:
            flash("Enter a group name of 1 to 80 characters.", "warning")
        elif len(selected_ids) < 2:
            flash("Choose at least two friends to start a group chat.", "warning")
        elif len(selected_ids) > 49:
            flash("A group chat can have at most 50 members.", "warning")
        else:
            cursor = db.execute(
                "INSERT INTO group_chats (name, creator_id) VALUES (?, ?)",
                (name, user["id"]),
            )
            group_id = cursor.lastrowid
            db.executemany(
                "INSERT INTO group_chat_members (group_id, user_id) VALUES (?, ?)",
                [(group_id, user["id"])]
                + [(group_id, friend_id) for friend_id in sorted(selected_ids)],
            )
            for friend_id in sorted(selected_ids):
                add_notification(
                    db,
                    friend_id,
                    user["id"],
                    "group_invite",
                    group_id,
                )
            db.commit()
            return redirect(url_for("group_conversation", group_id=group_id))

    return render_template(
        "group_chat_create.html",
        friends=eligible_friends,
        current_user=user,
    )


@app.route("/notifications")
@login_required
def notifications():
    user = get_current_user()
    db = get_db()
    rows = db.execute(
        """
        SELECT notifications.id, notifications.kind, notifications.reference_id,
               notifications.created_at, notifications.read_at,
               users.id AS actor_id, users.username AS actor_username,
               users.nickname AS actor_nickname, users.profile_photo AS actor_photo
        FROM notifications
        LEFT JOIN users ON users.id = notifications.actor_id
        WHERE notifications.recipient_id = ?
        ORDER BY notifications.created_at DESC, notifications.id DESC
        LIMIT 100
        """,
        (user["id"],),
    ).fetchall()
    return render_template(
        "notifications.html",
        notifications=rows,
        current_user=user,
    )


@app.route("/notifications/read", methods=["POST"])
@login_required
def mark_notifications_read():
    user = get_current_user()
    db = get_db()
    db.execute(
        "UPDATE notifications SET read_at = CURRENT_TIMESTAMP "
        "WHERE recipient_id = ? AND read_at IS NULL",
        (user["id"],),
    )
    db.commit()
    return redirect(url_for("notifications"))


@app.route("/messages/new")
@login_required
def new_message():
    user = get_current_user()
    query = request.args.get("q", "").strip()
    results = []
    if query:
        escaped_query = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        db = get_db()
        rows = db.execute(
            """
            SELECT users.id, users.username, users.nickname, users.profile_photo,
                   users.is_private
            FROM users
            WHERE users.id != ?
              AND (users.username LIKE ? ESCAPE '\\'
                   OR users.nickname LIKE ? ESCAPE '\\')
            ORDER BY users.username COLLATE NOCASE
            LIMIT 30
            """,
            (user["id"], f"%{escaped_query}%", f"%{escaped_query}%"),
        ).fetchall()
        for row in rows:
            person = dict(row)
            person["blocked"] = is_blocked_between(db, user["id"], row["id"])
            person["can_message"] = can_message_user(
                db, user["id"], row["id"], row["is_private"]
            )
            results.append(person)
    return render_template(
        "new_message.html",
        query=query,
        results=results,
        current_user=user,
    )


@app.route("/messages")
@login_required
def message_inbox():
    user = get_current_user()
    db = get_db()
    conversations = db.execute(
        """
        SELECT users.id, users.username, users.nickname, users.profile_photo,
               (SELECT messages.content
                FROM messages
                WHERE (messages.sender_id = ? AND messages.recipient_id = users.id)
                   OR (messages.sender_id = users.id AND messages.recipient_id = ?)
                ORDER BY messages.created_at DESC, messages.id DESC
                LIMIT 1) AS latest_message,
               (SELECT messages.created_at
                FROM messages
                WHERE (messages.sender_id = ? AND messages.recipient_id = users.id)
                   OR (messages.sender_id = users.id AND messages.recipient_id = ?)
                ORDER BY messages.created_at DESC, messages.id DESC
                LIMIT 1) AS latest_at
        FROM users
        WHERE users.id != ?
          AND (
              users.is_private = 0
              OR EXISTS (
                  SELECT 1 FROM follows AS owner_follow
                  JOIN follows AS viewer_follow
                    ON viewer_follow.follower_id = owner_follow.followed_id
                   AND viewer_follow.followed_id = owner_follow.follower_id
                  WHERE owner_follow.follower_id = users.id
                    AND owner_follow.followed_id = ?
              )
          )
          AND EXISTS (
              SELECT 1 FROM messages
              WHERE (messages.sender_id = ? AND messages.recipient_id = users.id)
                 OR (messages.sender_id = users.id AND messages.recipient_id = ?)
          )
          AND NOT EXISTS (
              SELECT 1 FROM blocks
              WHERE (blocks.blocker_id = ? AND blocks.blocked_id = users.id)
                 OR (blocks.blocker_id = users.id AND blocks.blocked_id = ?)
          )
        ORDER BY latest_at DESC
        """,
        (user["id"], user["id"], user["id"], user["id"], user["id"],
         user["id"], user["id"], user["id"], user["id"], user["id"]),
    ).fetchall()
    group_conversations = load_group_chats(db, user["id"])
    return render_template(
        "messages.html",
        conversations=conversations,
        group_conversations=group_conversations,
        current_user=user,
    )


@app.route("/messages/groups/<int:group_id>", methods=["GET", "POST"])
@login_required
def group_conversation(group_id):
    user = get_current_user()
    db = get_db()
    group = db.execute(
        """
        SELECT group_chats.id, group_chats.name
        FROM group_chats
        JOIN group_chat_members ON group_chat_members.group_id = group_chats.id
        WHERE group_chat_members.user_id = ? AND group_chats.id = ?
        """,
        (user["id"], group_id),
    ).fetchone()
    if group is None:
        flash("That group conversation is not available.", "warning")
        return redirect(url_for("message_inbox"))

    db.execute(
        """
        UPDATE group_chat_members
        SET last_read_message_id = COALESCE(
            (SELECT MAX(id) FROM group_chat_messages WHERE group_id = ?), 0
        )
        WHERE group_id = ? AND user_id = ?
        """,
        (group_id, group_id, user["id"]),
    )
    db.commit()

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if not content:
            flash("Messages cannot be empty.", "warning")
        elif len(content) > 5000:
            flash("Messages must be 5,000 characters or fewer.", "warning")
        else:
            db.execute(
                """
                INSERT INTO group_chat_messages (group_id, sender_id, content)
                VALUES (?, ?, ?)
                """,
                (group_id, user["id"], content),
            )
            member_ids = db.execute(
                """
                SELECT user_id FROM group_chat_members
                WHERE group_id = ? AND user_id != ?
                """,
                (group_id, user["id"]),
            ).fetchall()
            for member in member_ids:
                add_notification(
                    db,
                    member["user_id"],
                    user["id"],
                    "group_message",
                    group_id,
                )
            db.commit()
            return redirect(url_for("group_conversation", group_id=group_id))

    thread = db.execute(
        """
        SELECT group_chat_messages.id, group_chat_messages.sender_id,
               group_chat_messages.content, group_chat_messages.created_at,
               users.username, users.nickname
        FROM group_chat_messages
        JOIN users ON users.id = group_chat_messages.sender_id
        WHERE group_chat_messages.group_id = ?
        ORDER BY group_chat_messages.id
        """,
        (group_id,),
    ).fetchall()
    members = db.execute(
        """
        SELECT users.id, users.username, users.nickname
        FROM group_chat_members
        JOIN users ON users.id = group_chat_members.user_id
        WHERE group_chat_members.group_id = ?
        ORDER BY users.username COLLATE NOCASE
        """,
        (group_id,),
    ).fetchall()
    return render_template(
        "messages.html",
        conversations=[],
        group_conversations=load_group_chats(db, user["id"]),
        group_target=group,
        group_members=members,
        thread=thread,
        current_user=user,
    )


@app.route("/messages/<int:target_id>", methods=["GET", "POST"])
@login_required
def conversation(target_id):
    user = get_current_user()
    db = get_db()
    target = db.execute(
        "SELECT id, username, nickname, profile_photo, is_private FROM users WHERE id = ?",
        (target_id,),
    ).fetchone()
    if target is None or target_id == user["id"]:
        flash("That conversation is not available.", "warning")
        return redirect(url_for("message_inbox"))
    if not can_message_user(db, user["id"], target_id, target["is_private"]):
        flash("You can message public accounts, or private accounts only if you are friends.", "warning")
        return redirect(url_for("message_inbox"))

    db.execute(
        """
        UPDATE messages SET is_read = 1
        WHERE sender_id = ? AND recipient_id = ? AND is_read = 0
        """,
        (target_id, user["id"]),
    )
    db.commit()

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if not content:
            flash("Messages cannot be empty.", "warning")
        elif len(content) > 5000:
            flash("Messages must be 5,000 characters or fewer.", "warning")
        else:
            db.execute(
                """
                INSERT INTO messages (sender_id, recipient_id, content, is_read)
                VALUES (?, ?, ?, 0)
                """,
                (user["id"], target_id, content),
            )
            add_notification(db, target_id, user["id"], "message", user["id"])
            db.commit()
            return redirect(url_for("conversation", target_id=target_id))

    messages = db.execute(
        """
        SELECT messages.id, messages.sender_id, messages.content, messages.created_at,
               users.username, users.nickname
        FROM messages
        JOIN users ON users.id = messages.sender_id
        WHERE (messages.sender_id = ? AND messages.recipient_id = ?)
           OR (messages.sender_id = ? AND messages.recipient_id = ?)
        ORDER BY messages.created_at, messages.id
        """,
        (user["id"], target_id, target_id, user["id"]),
    ).fetchall()
    conversations = db.execute(
        """
        SELECT users.id, users.username, users.nickname, users.profile_photo,
               (SELECT messages.content
                FROM messages
                WHERE (messages.sender_id = ? AND messages.recipient_id = users.id)
                   OR (messages.sender_id = users.id AND messages.recipient_id = ?)
                ORDER BY messages.created_at DESC, messages.id DESC
                LIMIT 1) AS latest_message,
               (SELECT messages.created_at
                FROM messages
                WHERE (messages.sender_id = ? AND messages.recipient_id = users.id)
                   OR (messages.sender_id = users.id AND messages.recipient_id = ?)
                ORDER BY messages.created_at DESC, messages.id DESC
                LIMIT 1) AS latest_at
        FROM users
        WHERE users.id != ?
          AND (
              users.is_private = 0
              OR EXISTS (
                  SELECT 1 FROM follows AS owner_follow
                  JOIN follows AS viewer_follow
                    ON viewer_follow.follower_id = owner_follow.followed_id
                   AND viewer_follow.followed_id = owner_follow.follower_id
                  WHERE owner_follow.follower_id = users.id
                    AND owner_follow.followed_id = ?
              )
          )
          AND EXISTS (
              SELECT 1 FROM messages
              WHERE (messages.sender_id = ? AND messages.recipient_id = users.id)
                 OR (messages.sender_id = users.id AND messages.recipient_id = ?)
          )
          AND NOT EXISTS (
              SELECT 1 FROM blocks
              WHERE (blocks.blocker_id = ? AND blocks.blocked_id = users.id)
                 OR (blocks.blocker_id = users.id AND blocks.blocked_id = ?)
          )
        ORDER BY latest_at DESC
        """,
        (user["id"], user["id"], user["id"], user["id"], user["id"],
         user["id"], user["id"], user["id"], user["id"], user["id"]),
    ).fetchall()
    return render_template(
        "messages.html",
        conversations=conversations,
        group_conversations=load_group_chats(db, user["id"]),
        target=target,
        thread=messages,
        current_user=user,
    )


@app.route("/users/<int:target_id>/block", methods=["POST"])
@login_required
def toggle_block(target_id):
    user = get_current_user()
    db = get_db()
    target = db.execute("SELECT id FROM users WHERE id = ?", (target_id,)).fetchone()
    if target is None or target_id == user["id"]:
        flash("That account cannot be blocked.", "warning")
        return redirect(safe_referrer(url_for("people")))

    existing = db.execute(
        "SELECT 1 FROM blocks WHERE blocker_id = ? AND blocked_id = ?",
        (user["id"], target_id),
    ).fetchone()
    if existing:
        db.execute(
            "DELETE FROM blocks WHERE blocker_id = ? AND blocked_id = ?",
            (user["id"], target_id),
        )
    else:
        db.execute(
            "INSERT INTO blocks (blocker_id, blocked_id) VALUES (?, ?)",
            (user["id"], target_id),
        )
        db.execute(
            """
            DELETE FROM follows
            WHERE (follower_id = ? AND followed_id = ?)
               OR (follower_id = ? AND followed_id = ?)
            """,
            (user["id"], target_id, target_id, user["id"]),
        )
        db.execute(
            """
            DELETE FROM notifications
            WHERE kind = 'friend_request'
              AND ((recipient_id = ? AND actor_id = ?)
                   OR (recipient_id = ? AND actor_id = ?))
            """,
            (user["id"], target_id, target_id, user["id"]),
        )
        db.execute(
            """
            DELETE FROM friend_requests
            WHERE (requester_id = ? AND recipient_id = ?)
               OR (requester_id = ? AND recipient_id = ?)
            """,
            (user["id"], target_id, target_id, user["id"]),
        )
    db.commit()
    return redirect(safe_referrer(url_for("people")))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = get_current_user()
    counts = get_db().execute(
        """
        SELECT
            (SELECT COUNT(*) FROM follows WHERE followed_id = ?) AS follower_count,
            (SELECT COUNT(*) FROM follows WHERE follower_id = ?) AS following_count
        """,
        (user["id"], user["id"]),
    ).fetchone()
    if request.method == "POST":
        new_username = request.form.get("username", "").strip()
        new_nickname = request.form.get("nickname", "").strip()
        profile_photo = request.files.get("profile_photo")

        if not new_username or not new_nickname:
            flash("Username and nickname are required.", "danger")
            return render_template(
                "profile.html",
                current_user=user,
                follower_count=counts["follower_count"],
                following_count=counts["following_count"],
            )

        db = get_db()
        other_user = db.execute(
            "SELECT id FROM users WHERE username = ? AND id != ?",
            (new_username, user["id"]),
        ).fetchone()

        if other_user:
            flash("That username is already used by someone else.", "danger")
            return render_template(
                "profile.html",
                current_user=user,
                follower_count=counts["follower_count"],
                following_count=counts["following_count"],
            )

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

    return render_template(
        "profile.html",
        current_user=get_current_user(),
        follower_count=counts["follower_count"],
        following_count=counts["following_count"],
    )


@app.route("/profile/followers")
@login_required
def profile_followers():
    user = get_current_user()
    followers = get_db().execute(
        """
        SELECT users.id, users.username, users.nickname, users.profile_photo
        FROM follows JOIN users ON users.id = follows.follower_id
        WHERE follows.followed_id = ?
        ORDER BY users.username COLLATE NOCASE
        """,
        (user["id"],),
    ).fetchall()
    return render_template(
        "relationships.html",
        heading="Followers",
        people=followers,
        current_user=user,
    )


@app.route("/profile/following")
@login_required
def profile_following():
    user = get_current_user()
    following = get_db().execute(
        """
        SELECT users.id, users.username, users.nickname, users.profile_photo
        FROM follows JOIN users ON users.id = follows.followed_id
        WHERE follows.follower_id = ?
        ORDER BY users.username COLLATE NOCASE
        """,
        (user["id"],),
    ).fetchall()
    return render_template(
        "relationships.html",
        heading="Following",
        people=following,
        current_user=user,
    )


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = get_current_user()
    if request.method == "POST":
        if request.form.get("action") == "privacy":
            is_private = request.form.get("is_private") == "1"
            db = get_db()
            db.execute(
                "UPDATE users SET is_private = ? WHERE id = ?",
                (int(is_private), user["id"]),
            )
            db.commit()
            flash(
                "Your account is now private." if is_private else "Your account is now public.",
                "success",
            )
            return redirect(url_for("settings"))

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


@app.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    user = get_current_user()
    password = request.form.get("password", "")
    confirmation = request.form.get("confirmation", "").strip()
    if not check_password_hash(user["password"], password):
        flash("Your password is incorrect. The account was not deleted.", "danger")
        return redirect(url_for("settings"))
    if confirmation != "DELETE":
        flash('Type "DELETE" exactly to confirm account deletion.', "danger")
        return redirect(url_for("settings"))

    db = get_db()
    post_rows = db.execute(
        "SELECT id, image_path FROM posts WHERE user_id = ?",
        (user["id"],),
    ).fetchall()
    post_ids = [post["id"] for post in post_rows]
    comment_rows = db.execute(
        """
        SELECT id, image_path FROM comments
        WHERE user_id = ?
           OR post_id IN (SELECT id FROM posts WHERE user_id = ?)
        """,
        (user["id"], user["id"]),
    ).fetchall()

    upload_paths = []
    if user["profile_photo"] and user["profile_photo"].startswith("uploads/profile_photos/"):
        upload_paths.append(user["profile_photo"])
    upload_paths.extend(
        post["image_path"]
        for post in post_rows
        if post["image_path"] and post["image_path"].startswith("uploads/posts/")
    )
    upload_paths.extend(
        comment["image_path"]
        for comment in comment_rows
        if comment["image_path"] and comment["image_path"].startswith("uploads/comments/")
    )

    db.execute(
        """
        DELETE FROM comments
        WHERE user_id = ?
           OR post_id IN (SELECT id FROM posts WHERE user_id = ?)
        """,
        (user["id"], user["id"]),
    )
    db.execute(
        "DELETE FROM likes WHERE user_id = ? OR post_id IN (SELECT id FROM posts WHERE user_id = ?)",
        (user["id"], user["id"]),
    )
    db.execute(
        "DELETE FROM reactions WHERE user_id = ? OR post_id IN (SELECT id FROM posts WHERE user_id = ?)",
        (user["id"], user["id"]),
    )
    db.execute("DELETE FROM post_hashtags WHERE post_id IN (SELECT id FROM posts WHERE user_id = ?)", (user["id"],))
    db.execute("DELETE FROM posts WHERE user_id = ?", (user["id"],))
    db.execute("DELETE FROM follows WHERE follower_id = ? OR followed_id = ?", (user["id"], user["id"]))
    db.execute("DELETE FROM blocks WHERE blocker_id = ? OR blocked_id = ?", (user["id"], user["id"]))
    db.execute(
        "DELETE FROM friend_requests WHERE requester_id = ? OR recipient_id = ?",
        (user["id"], user["id"]),
    )
    db.execute(
        "DELETE FROM messages WHERE sender_id = ? OR recipient_id = ?",
        (user["id"], user["id"]),
    )
    db.execute("DELETE FROM users WHERE id = ?", (user["id"],))
    db.commit()

    for relative_path in upload_paths:
        filename = os.path.basename(relative_path)
        folder = relative_path.split("/", 2)[1]
        upload_path = os.path.join(UPLOAD_FOLDER, folder, filename)
        if os.path.isfile(upload_path):
            os.remove(upload_path)

    session.clear()
    flash("Your account and its content have been deleted.", "success")
    return redirect(url_for("login"))


@app.context_processor
def inject_user():
    current_user = get_current_user()
    friend_request_count = 0
    unread_message_count = 0
    notification_count = 0
    if current_user:
        db = get_db()
        friend_request_count = db.execute(
            "SELECT COUNT(*) FROM friend_requests WHERE recipient_id = ?",
            (current_user["id"],),
        ).fetchone()[0]
        unread_message_count = db.execute(
            """
            SELECT COUNT(*)
            FROM messages
            WHERE recipient_id = ? AND is_read = 0
              AND NOT EXISTS (
                  SELECT 1 FROM blocks
                  WHERE (blocks.blocker_id = messages.sender_id
                         AND blocks.blocked_id = messages.recipient_id)
                     OR (blocks.blocker_id = messages.recipient_id
                         AND blocks.blocked_id = messages.sender_id)
              )
            """,
            (current_user["id"],),
        ).fetchone()[0]
        unread_message_count += db.execute(
            """
            SELECT COUNT(*)
            FROM group_chat_messages
            JOIN group_chat_members
              ON group_chat_members.group_id = group_chat_messages.group_id
            WHERE group_chat_members.user_id = ?
              AND group_chat_messages.sender_id != ?
              AND group_chat_messages.id > group_chat_members.last_read_message_id
            """,
            (current_user["id"], current_user["id"]),
        ).fetchone()[0]
        notification_count = db.execute(
            "SELECT COUNT(*) FROM notifications "
            "WHERE recipient_id = ? AND read_at IS NULL",
            (current_user["id"],),
        ).fetchone()[0]
    return {
        "current_user": current_user,
        "reaction_emojis": REACTION_EMOJIS,
        "friend_request_count": friend_request_count,
        "unread_message_count": unread_message_count,
        "notification_count": notification_count,
    }


with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
