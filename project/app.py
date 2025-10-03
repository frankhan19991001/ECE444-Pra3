import sqlite3
from pathlib import Path

from flask import (
    Flask,
    g,
    render_template,
    request,
    session,
    flash,
    redirect,
    url_for,
    abort,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy

import os


basedir = Path(__file__).resolve().parent

# configuration
DATABASE = "flaskr.db"
USERNAME = "admin"
PASSWORD = "admin"
SECRET_KEY = "change_me"
url = os.getenv("DATABASE_URL", f"sqlite:///{Path(basedir).joinpath(DATABASE)}")

if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)

SQLALCHEMY_DATABASE_URI = url
SQLALCHEMY_TRACK_MODIFICATIONS = False


# create and initialize a new Flask app
app = Flask(__name__)
# load the config
app.config.from_object(__name__)
# init sqlalchemy
db = SQLAlchemy(app)

from project import models


@app.route("/")
def index():
    """Searches the database for entries, then displays them."""
    entries = db.session.query(models.Post)
    return render_template("index.html", entries=entries)


@app.route("/search/", methods=["GET"])
def search():
    query = request.args.get("query")
    entries = db.session.query(models.Post)
    if query:
        return render_template("search.html", entries=entries, query=query)
    return render_template("search.html")


@app.route("/add", methods=["POST"])
def add_entry():
    """Adds new post to the database."""
    if not session.get("logged_in"):
        abort(401)
    new_entry = models.Post(request.form["title"], request.form["text"])
    db.session.add(new_entry)
    db.session.commit()
    flash("New entry was successfully posted")
    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login/authentication/session management."""
    error = None
    if request.method == "POST":
        if request.form["username"] != app.config["USERNAME"]:
            error = "Invalid username"
        elif request.form["password"] != app.config["PASSWORD"]:
            error = "Invalid password"
        else:
            session["logged_in"] = True
            flash("You were logged in")
            return redirect(url_for("index"))
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """User logout/authentication/session management."""
    session.pop("logged_in", None)
    flash("You were logged out")
    return redirect(url_for("index"))


@app.route("/delete/<int:post_id>", methods=["GET", "POST"])
def delete_entry(post_id):
    if not session.get("logged_in"):
        abort(401)
    if request.method == "GET":
        # Optional: require a query param to reduce accidental deletions
        # if request.args.get("confirm") != "1": abort(400)
        pass
    try:
        deleted = db.session.query(models.Post).filter_by(id=post_id).delete()
        if deleted == 0:
            return jsonify({"status": 0, "message": "Post not found"}), 404
        db.session.commit()
        flash("The entry was deleted.")
        return jsonify({"status": 1, "message": "Post Deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": 0, "message": repr(e)}), 500


if __name__ == "__main__":
    app.run()
