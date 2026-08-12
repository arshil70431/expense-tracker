"""
Personal Expense Tracker Application (Multi-User)
-------------------------------------
Backend: Flask (Python web framework)
Database: SQLite (SQL database, accessed via raw SQL through sqlite3)
Features: user accounts/login, manual expense entry, notification-based daily
reminders, category-wise summaries, monthly filtering, edit/delete records,
shop/store tracking with weekly totals.
"""

import os
import sqlite3
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-this")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

DB_PATH = "expenses.db"

CATEGORIES = [
    "Food", "Transport", "Rent", "Utilities", "Shopping",
    "Entertainment", "Health", "Education", "Other"
]

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS shops (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            entry_date  TEXT    NOT NULL,
            created_at  TEXT    NOT NULL,
            shop_id     INTEGER REFERENCES shops(id) ON DELETE SET NULL,
            user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Migrations for older databases
    cursor = conn.execute("PRAGMA table_info(expenses)")
    columns = [col[1] for col in cursor.fetchall()]
    if "shop_id" not in columns:
        conn.execute("ALTER TABLE expenses ADD COLUMN shop_id INTEGER REFERENCES shops(id) ON DELETE SET NULL")
    if "user_id" not in columns:
        conn.execute("ALTER TABLE expenses ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE")

    cursor = conn.execute("PRAGMA table_info(shops)")
    columns = [col[1] for col in cursor.fetchall()]
    if "user_id" not in columns:
        conn.execute("ALTER TABLE shops ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE")

    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Flask-Login user object
# ---------------------------------------------------------------------------

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if row:
        return User(row["id"], row["username"])
    return None

# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("signup.html")

        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            conn.close()
            flash("That username is already taken.", "error")
            return render_template("signup.html")

        password_hash = generate_password_hash(password)
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, datetime.now().isoformat())
        )
        new_user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # ✅ Auto‑login after signup
        user = User(new_user_id, username)
        login_user(user)
        flash("Account created! Welcome!", "success")
        return redirect(url_for("index"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if row and check_password_hash(row["password_hash"], password):
            user = User(row["id"], row["username"])
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
@login_required
def index():
    conn = get_db()
    month_filter = request.args.get("month", date.today().strftime("%Y-%m"))
    category_filter = request.args.get("category", "All")

    # Join with shops to get shop_name
    query = """
        SELECT expenses.*, shops.name as shop_name
        FROM expenses
        LEFT JOIN shops ON shops.id = expenses.shop_id
        WHERE expenses.entry_date LIKE ? AND expenses.user_id = ?
    """
    params = [f"{month_filter}%", current_user.id]
    if category_filter != "All":
        query += " AND expenses.category = ?"
        params.append(category_filter)
    query += " ORDER BY expenses.entry_date DESC, expenses.id DESC"
    rows = conn.execute(query, params).fetchall()

    # ✅ Convert sqlite3.Row objects to dictionaries for JSON serialization
    expenses = [dict(row) for row in rows]

    total = sum(e["amount"] for e in expenses)

    category_rows = conn.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE entry_date LIKE ? AND user_id = ?
        GROUP BY category
        ORDER BY total DESC
    """, [f"{month_filter}%", current_user.id]).fetchall()
    category_totals = [dict(row) for row in category_rows]

    last_entry = conn.execute(
        "SELECT entry_date FROM expenses WHERE user_id = ? ORDER BY entry_date DESC LIMIT 1",
        (current_user.id,)
    ).fetchone()

    shops_summary = conn.execute("""
        SELECT s.id, s.name, COUNT(e.id) as count, COALESCE(SUM(e.amount), 0) as total
        FROM shops s
        LEFT JOIN expenses e ON e.shop_id = s.id AND e.entry_date LIKE ? AND e.user_id = ?
        WHERE s.user_id = ?
        GROUP BY s.id, s.name
        ORDER BY total DESC, s.name
    """, [f"{month_filter}%", current_user.id, current_user.id]).fetchall()

    conn.close()

    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        category_totals=category_totals,
        categories=CATEGORIES,
        month_filter=month_filter,
        category_filter=category_filter,
        today=date.today().isoformat(),
        last_entry_date=last_entry["entry_date"] if last_entry else None,
        shops_summary=shops_summary
    )

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_expense():
    conn = get_db()
    shops = conn.execute("SELECT id, name FROM shops WHERE user_id = ? ORDER BY name", (current_user.id,)).fetchall()
    conn.close()

    if request.method == "POST":
        description = request.form.get("description", "").strip()
        category = request.form.get("category")
        amount = request.form.get("amount")
        entry_date = request.form.get("entry_date") or date.today().isoformat()
        shop_id = request.form.get("shop_id")
        new_shop_name = request.form.get("new_shop_name", "").strip()

        if new_shop_name:
            conn = get_db()
            existing = conn.execute(
                "SELECT id FROM shops WHERE name = ? AND user_id = ?",
                (new_shop_name, current_user.id)
            ).fetchone()
            if existing:
                shop_id = existing["id"]
            else:
                cursor = conn.execute(
                    "INSERT INTO shops (name, created_at, user_id) VALUES (?, ?, ?)",
                    (new_shop_name, datetime.now().isoformat(), current_user.id)
                )
                shop_id = cursor.lastrowid
            conn.commit()
            conn.close()
        else:
            shop_id = None if shop_id == "" else int(shop_id)

        error = None
        try:
            amount = float(amount)
            if amount <= 0:
                error = "Amount must be greater than zero."
        except (TypeError, ValueError):
            error = "Please enter a valid numeric amount."

        if not description:
            error = "Description is required."
        if category not in CATEGORIES:
            error = "Please select a valid category."

        if error:
            flash(error, "error")
            conn = get_db()
            shops = conn.execute("SELECT id, name FROM shops WHERE user_id = ? ORDER BY name", (current_user.id,)).fetchall()
            conn.close()
            return render_template("add.html", categories=CATEGORIES,
                                    today=date.today().isoformat(), form=request.form, shops=shops)

        conn = get_db()
        conn.execute(
            "INSERT INTO expenses (description, category, amount, entry_date, created_at, shop_id, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (description, category, amount, entry_date, datetime.now().isoformat(), shop_id, current_user.id)
        )
        conn.commit()
        conn.close()

        flash("Expense added successfully.", "success")
        return redirect(url_for("index"))

    return render_template("add.html", categories=CATEGORIES, today=date.today().isoformat(), form={}, shops=shops)

@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    conn = get_db()
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?", (expense_id, current_user.id)
    ).fetchone()
    if expense is None:
        conn.close()
        flash("Expense not found.", "error")
        return redirect(url_for("index"))

    shops = conn.execute("SELECT id, name FROM shops WHERE user_id = ? ORDER BY name", (current_user.id,)).fetchall()
    conn.close()

    if request.method == "POST":
        description = request.form.get("description", "").strip()
        category = request.form.get("category")
        amount = request.form.get("amount")
        entry_date = request.form.get("entry_date")
        shop_id = request.form.get("shop_id")
        new_shop_name = request.form.get("new_shop_name", "").strip()

        conn = get_db()
        if new_shop_name:
            existing = conn.execute(
                "SELECT id FROM shops WHERE name = ? AND user_id = ?",
                (new_shop_name, current_user.id)
            ).fetchone()
            if existing:
                shop_id = existing["id"]
            else:
                cursor = conn.execute(
                    "INSERT INTO shops (name, created_at, user_id) VALUES (?, ?, ?)",
                    (new_shop_name, datetime.now().isoformat(), current_user.id)
                )
                shop_id = cursor.lastrowid
        else:
            shop_id = None if shop_id == "" else int(shop_id)

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            amount = expense["amount"]

        conn.execute(
            "UPDATE expenses SET description=?, category=?, amount=?, entry_date=?, shop_id=? WHERE id=? AND user_id=?",
            (description, category, amount, entry_date, shop_id, expense_id, current_user.id)
        )
        conn.commit()
        conn.close()
        flash("Expense updated.", "success")
        return redirect(url_for("index"))

    return render_template("edit.html", expense=expense, categories=CATEGORIES, shops=shops)

@app.route("/delete/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, current_user.id))
    conn.commit()
    conn.close()
    flash("Expense deleted.", "success")
    return redirect(url_for("index"))

# -----------------------------------------------------------
# API endpoints
# -----------------------------------------------------------

@app.route("/api/reminder-status")
@login_required
def reminder_status():
    conn = get_db()
    today = date.today().isoformat()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM expenses WHERE entry_date = ? AND user_id = ?",
        (today, current_user.id)
    ).fetchone()
    conn.close()
    return jsonify({"logged_today": row["cnt"] > 0, "date": today})

@app.route("/api/summary")
@login_required
def api_summary():
    conn = get_db()
    month_filter = request.args.get("month", date.today().strftime("%Y-%m"))
    rows = conn.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE entry_date LIKE ? AND user_id = ?
        GROUP BY category
        ORDER BY total DESC
    """, [f"{month_filter}%", current_user.id]).fetchall()
    conn.close()
    return jsonify([{"category": r["category"], "total": r["total"]} for r in rows])

@app.route("/api/quick-add", methods=["POST"])
@login_required
def api_quick_add():
    data = request.get_json()
    category = data.get("category")
    amount = data.get("amount")
    description = data.get("description", f"Quick {category}")

    if category not in CATEGORIES:
        return jsonify({"success": False, "error": "Invalid category"}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({"success": False, "error": "Amount must be > 0"}), 400
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid amount"}), 400

    today = date.today().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (description, category, amount, entry_date, created_at, user_id) VALUES (?, ?, ?, ?, ?, ?)",
        (description, category, amount, today, datetime.now().isoformat(), current_user.id)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Added {category} for ₹{amount:.2f}"})

@app.route("/export")
@login_required
def export_csv():
    import csv
    from io import StringIO

    month_filter = request.args.get("month", date.today().strftime("%Y-%m"))
    category_filter = request.args.get("category", "All")

    conn = get_db()
    query = "SELECT * FROM expenses WHERE entry_date LIKE ? AND user_id = ?"
    params = [f"{month_filter}%", current_user.id]
    if category_filter != "All":
        query += " AND category = ?"
        params.append(category_filter)
    query += " ORDER BY entry_date DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "Description", "Category", "Amount", "Entry Date", "Created At", "Shop ID"])
    for r in rows:
        writer.writerow([r["id"], r["description"], r["category"], r["amount"], r["entry_date"], r["created_at"], r["shop_id"]])
    output = si.getvalue()
    return output, 200, {
        "Content-Type": "text/csv",
        "Content-Disposition": f'attachment; filename="expenses_{month_filter}.csv"'
    }

@app.route("/shop/<int:shop_id>")
@login_required
def shop_detail(shop_id):
    conn = get_db()
    shop = conn.execute("SELECT * FROM shops WHERE id = ? AND user_id = ?", (shop_id, current_user.id)).fetchone()
    if not shop:
        conn.close()
        flash("Shop not found.", "error")
        return redirect(url_for("index"))

    expenses = conn.execute("""
        SELECT * FROM expenses
        WHERE shop_id = ? AND user_id = ?
        ORDER BY entry_date DESC, id DESC
    """, (shop_id, current_user.id)).fetchall()

    weekly_totals = conn.execute("""
        SELECT
            strftime('%Y-%W', entry_date) as week,
            MIN(entry_date) as week_start,
            SUM(amount) as total
        FROM expenses
        WHERE shop_id = ? AND user_id = ?
        GROUP BY week
        ORDER BY week DESC
    """, (shop_id, current_user.id)).fetchall()

    conn.close()
    return render_template("shop_detail.html", shop=shop, expenses=expenses, weekly_totals=weekly_totals)

init_db()

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=False)